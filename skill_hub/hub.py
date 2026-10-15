"""Core orchestration engine for skill-hub."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from skill_hub.config import Config
from skill_hub.store import Store
from skill_hub.adapters.registry import AdapterRegistry
from skill_hub.adapters.base import BaseAdapter
from skill_hub.parser import (
    inspect_skill_dir,
    inspect_plugin_dir,
    parse_frontmatter,
    format_skill_md,
)
from skill_hub.curated import get_curated_item


class Hub:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.store = Store(self.config)
        self.adapter_registry = AdapterRegistry(custom_paths=self.config.to_dict().get("custom_paths"))

    def get_active_adapters(self, target_names: Optional[List[str]] = None) -> List[BaseAdapter]:
        """Return list of active BaseAdapter instances."""
        if target_names:
            return self.adapter_registry.resolve_targets(target_names)
        return self.adapter_registry.resolve_targets(self.config.enabled_targets)

    def install(
        self,
        source: str,
        name: Optional[str] = None,
        sync_after: Optional[bool] = None,
        targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Install a skill or plugin from a Git URL, GitHub repo slug, curated name, or local path.
        """
        source_clean = source.strip()
        temp_dir_to_clean: Optional[Path] = None

        # 1. Check if source is a curated name
        curated = get_curated_item(source_clean)
        if curated:
            source_uri = curated["source"]
        else:
            source_uri = source_clean

        # 2. Check if source is a Git URL or GitHub shorthand (e.g. user/repo)
        is_git = (
            source_uri.startswith("http://")
            or source_uri.startswith("https://")
            or source_uri.startswith("git@")
            or source_uri.endswith(".git")
            or (len(source_uri.split("/")) == 2 and not Path(source_uri).exists())
        )

        local_path: Path
        if is_git:
            # Expand GitHub shorthand
            if not (source_uri.startswith("http://") or source_uri.startswith("https://") or source_uri.startswith("git@")):
                git_clone_url = f"https://github.com/{source_uri}.git"
            else:
                git_clone_url = source_uri

            temp_dir = Path(tempfile.mkdtemp(prefix="skillhub_git_"))
            temp_dir_to_clean = temp_dir
            try:
                cmd = ["git", "clone", "--depth", "1", git_clone_url, str(temp_dir)]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {proc.stderr.strip()}")
                local_path = temp_dir
            except Exception as e:
                if temp_dir_to_clean and temp_dir_to_clean.exists():
                    shutil.rmtree(temp_dir_to_clean, ignore_errors=True)
                raise RuntimeError(f"Failed to fetch git repository '{source_uri}': {e}")
        else:
            local_path = Path(source_uri).expanduser().resolve()
            if not local_path.exists():
                raise FileNotFoundError(f"Source not found: {source_uri}")

        # 3. Detect content type (Single File, Skill Directory, or Plugin)
        installed_type = "unknown"
        installed_name = name
        installed_path: Optional[Path] = None

        try:
            if local_path.is_file():
                # Single markdown file
                content = local_path.read_text(encoding="utf-8", errors="replace")
                meta, body = parse_frontmatter(content)
                skill_name = name or meta.get("name") or local_path.stem
                if not meta.get("name"):
                    meta["name"] = skill_name
                if not meta.get("description"):
                    meta["description"] = f"Skill {skill_name}"

                temp_skill_dir = Path(tempfile.mkdtemp(prefix="skillhub_single_"))
                (temp_skill_dir / "SKILL.md").write_text(format_skill_md(meta, body), encoding="utf-8")
                installed_path = self.store.add_skill(skill_name, temp_skill_dir, source_uri=source, metadata=meta)
                shutil.rmtree(temp_skill_dir, ignore_errors=True)
                installed_type = "skill"
                installed_name = skill_name

            elif local_path.is_dir():
                # Check if it's a plugin bundle first
                plugin_info = inspect_plugin_dir(local_path)
                skill_info = inspect_skill_dir(local_path)

                if plugin_info and (plugin_info["bundled_skills"] or plugin_info["manifest_file"]):
                    plugin_name = name or plugin_info["name"]
                    installed_path = self.store.add_plugin(plugin_name, local_path, source_uri=source, metadata=plugin_info)
                    installed_type = "plugin"
                    installed_name = plugin_name
                elif skill_info:
                    skill_name = name or skill_info["name"]
                    installed_path = self.store.add_skill(skill_name, local_path, source_uri=source, metadata=skill_info)
                    installed_type = "skill"
                    installed_name = skill_name
                else:
                    # Check if there are skills in a skills/ subfolder
                    skills_sub = local_path / "skills"
                    if skills_sub.is_dir():
                        plugin_name = name or local_path.name
                        installed_path = self.store.add_plugin(plugin_name, local_path, source_uri=source)
                        installed_type = "plugin"
                        installed_name = plugin_name
                    else:
                        raise ValueError(f"Directory {local_path} does not appear to contain a valid SKILL.md or plugin structure.")
        finally:
            if temp_dir_to_clean and temp_dir_to_clean.exists():
                shutil.rmtree(temp_dir_to_clean, ignore_errors=True)

        sync_result = None
        should_sync = self.config.auto_sync if sync_after is None else sync_after
        if should_sync:
            sync_result = self.sync(targets=targets)

        return {
            "status": "success",
            "type": installed_type,
            "name": installed_name,
            "path": str(installed_path) if installed_path else None,
            "source": source,
            "synced": sync_result is not None,
            "sync_details": sync_result,
        }

    def sync(
        self,
        targets: Optional[List[str]] = None,
        mode: Optional[str] = None,
        scope: str = "global",
        workspace_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Synchronize all installed skills and plugins across all enabled AI agent targets.
        """
        sync_mode = mode or self.config.sync_mode
        is_global = (scope == "global")
        active_adapters = self.get_active_adapters(targets)

        all_skills = self.store.get_all_exportable_skills()
        all_plugins = self.store.list_plugins()

        target_stats: Dict[str, Dict[str, Any]] = {}
        total_skills_synced = 0
        total_plugins_synced = 0

        for adapter in active_adapters:
            t_name = adapter.name
            stats = {
                "display_name": adapter.display_name,
                "skills_synced": 0,
                "plugins_synced": 0,
                "cleaned": 0,
                "errors": [],
            }

            # 1. Clean broken symlinks first
            cleaned = adapter.clean_broken_links(global_scope=is_global, workspace_path=workspace_path)
            stats["cleaned"] = cleaned

            # 2. Sync all skills (standalone + bundled)
            for skill_name, skill_path in all_skills.items():
                ok, msg = adapter.sync_skill(
                    skill_name,
                    skill_path,
                    mode=sync_mode,
                    global_scope=is_global,
                    workspace_path=workspace_path,
                )
                if ok:
                    stats["skills_synced"] += 1
                else:
                    stats["errors"].append(f"Skill '{skill_name}': {msg}")

            # 3. Sync plugins
            for plugin_item in all_plugins:
                p_name = plugin_item["name"]
                p_path = Path(plugin_item["path"])
                if p_path.is_dir():
                    ok, msg = adapter.sync_plugin(
                        p_name,
                        p_path,
                        mode=sync_mode,
                        global_scope=is_global,
                        workspace_path=workspace_path,
                    )
                    if ok:
                        stats["plugins_synced"] += 1
                    elif msg != "Target plugins directory not supported":
                        stats["errors"].append(f"Plugin '{p_name}': {msg}")

            total_skills_synced += stats["skills_synced"]
            total_plugins_synced += stats["plugins_synced"]
            target_stats[t_name] = stats

        return {
            "mode": sync_mode,
            "scope": scope,
            "total_skills_available": len(all_skills),
            "total_plugins_available": len(all_plugins),
            "targets": target_stats,
        }

    def uninstall(self, name: str, targets: Optional[List[str]] = None) -> bool:
        """Remove a skill or plugin from store and all target agent folders."""
        adapters = self.get_active_adapters(targets)
        removed_skill = False
        removed_plugin = False

        if self.store.get_skill(name):
            for adapter in adapters:
                adapter.unlink_skill(name, global_scope=True)
            removed_skill = self.store.remove_skill(name)

        if self.store.get_plugin(name):
            for adapter in adapters:
                adapter.unlink_plugin(name, global_scope=True)
            removed_plugin = self.store.remove_plugin(name)

        return removed_skill or removed_plugin

    def import_existing(self, from_target: str = "all") -> Dict[str, Any]:
        """
        Import existing skills and plugins from configured AI agent directories into the central hub.
        """
        imported_skills = []
        imported_plugins = []

        target_adapters = (
            self.adapter_registry.list_adapters()
            if from_target.lower() == "all"
            else [a for a in [self.adapter_registry.get_adapter(from_target)] if a]
        )

        for adapter in target_adapters:
            # Check skills dir
            s_dir = adapter.get_skills_dir(global_scope=True)
            if s_dir and s_dir.is_dir():
                try:
                    for item in s_dir.iterdir():
                        if item.is_symlink():
                            continue  # skip symlinks already managed
                        if item.is_dir():
                            meta = inspect_skill_dir(item)
                            if meta and meta.get("name") not in self.store._registry["skills"]:
                                self.store.add_skill(meta["name"], item, source_uri=f"imported:{adapter.name}")
                                imported_skills.append(meta["name"])
                except Exception:
                    pass

            # Check plugins dir
            p_dir = adapter.get_plugins_dir(global_scope=True)
            if p_dir and p_dir.is_dir():
                try:
                    for item in p_dir.iterdir():
                        if item.is_symlink():
                            continue
                        if item.is_dir():
                            meta = inspect_plugin_dir(item)
                            if meta and meta.get("name") not in self.store._registry["plugins"]:
                                self.store.add_plugin(meta["name"], item, source_uri=f"imported:{adapter.name}")
                                imported_plugins.append(meta["name"])
                except Exception:
                    pass

        return {
            "imported_skills": imported_skills,
            "imported_plugins": imported_plugins,
        }

    def create(self, name: str, description: str = "") -> Path:
        """Create a new standard skill template ready to be edited and synced."""
        clean_name = name.lower().strip().replace(" ", "-")
        skill_dir = self.store.skills_dir / clean_name
        if skill_dir.exists():
            raise FileExistsError(f"Skill '{clean_name}' already exists in store.")

        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)
        (skill_dir / "references").mkdir(exist_ok=True)

        meta = {
            "name": clean_name,
            "description": description or f"Custom skill {clean_name} for AI agents.",
        }
        body = f"""# {clean_name}

{description or 'Describe what this skill teaches the agent to do.'}

## When to Use
- Trigger 1: When user asks ...
- Trigger 2: When ...

## Step-by-Step Instructions
1. First step ...
2. Second step ...

## Best Practices
- Keep instructions clear, actionable, and unambiguous.
"""
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(format_skill_md(meta, body), encoding="utf-8")

        self.store.add_skill(clean_name, skill_dir, source_uri="local:created", metadata=meta)

        if self.config.auto_sync:
            self.sync()

        return skill_dir

    def doctor(self) -> Dict[str, Any]:
        """Perform system diagnostics across all agent adapters."""
        adapters_diag = []
        for adapter in self.adapter_registry.list_adapters():
            adapters_diag.append(adapter.doctor())

        return {
            "hub_home": str(self.hub_home),
            "sync_mode": self.config.sync_mode,
            "auto_sync": self.config.auto_sync,
            "stored_skills_count": len(self.store.list_skills()),
            "stored_plugins_count": len(self.store.list_plugins()),
            "adapters": adapters_diag,
        }

    @property
    def hub_home(self) -> Path:
        return self.config.hub_home
