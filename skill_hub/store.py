"""Central store and registry management for skill-hub."""
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from skill_hub.config import Config, get_hub_home
from skill_hub.parser import inspect_skill_dir, inspect_plugin_dir


class Store:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.hub_home = self.config.hub_home
        self.store_dir = self.hub_home / "store"
        self.skills_dir = self.store_dir / "skills"
        self.plugins_dir = self.store_dir / "plugins"
        self.registry_file = self.hub_home / "registry.json"
        self._registry: Dict[str, Any] = {"skills": {}, "plugins": {}}
        self.ensure_dirs()
        self.load_registry()

    def ensure_dirs(self) -> None:
        """Create necessary store directories."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def load_registry(self) -> None:
        """Load registry from disk and reconcile with physical files."""
        if self.registry_file.exists():
            try:
                self._registry = json.loads(self.registry_file.read_text(encoding="utf-8"))
            except Exception:
                self._registry = {"skills": {}, "plugins": {}}
        else:
            self._registry = {"skills": {}, "plugins": {}}

        # Reconcile on disk skills
        if self.skills_dir.exists():
            for item in self.skills_dir.iterdir():
                if item.is_dir() and item.name not in self._registry["skills"]:
                    meta = inspect_skill_dir(item)
                    if meta:
                        self._registry["skills"][item.name] = {
                            "name": item.name,
                            "type": "skill",
                            "description": meta.get("description", ""),
                            "source": "local",
                            "installed_at": datetime.datetime.now().isoformat(),
                            "path": str(item.resolve()),
                        }

        # Reconcile on disk plugins
        if self.plugins_dir.exists():
            for item in self.plugins_dir.iterdir():
                if item.is_dir() and item.name not in self._registry["plugins"]:
                    meta = inspect_plugin_dir(item)
                    if meta:
                        self._registry["plugins"][item.name] = {
                            "name": item.name,
                            "type": "plugin",
                            "description": meta.get("description", ""),
                            "version": meta.get("version", "1.0.0"),
                            "bundled_skills": meta.get("bundled_skills", []),
                            "source": "local",
                            "installed_at": datetime.datetime.now().isoformat(),
                            "path": str(item.resolve()),
                        }

        self.save_registry()

    def save_registry(self) -> None:
        """Persist registry to disk."""
        self.registry_file.write_text(json.dumps(self._registry, indent=2), encoding="utf-8")

    def add_skill(self, name: str, source_dir: Path, source_uri: str = "local", metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Copy or save a skill directory into the central store."""
        target = self.skills_dir / name
        if source_dir.resolve() != target.resolve():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source_dir, target, symlinks=True)

        inspected = inspect_skill_dir(target)
        desc = (metadata and metadata.get("description")) or (inspected and inspected.get("description")) or ""

        self._registry["skills"][name] = {
            "name": name,
            "type": "skill",
            "description": desc,
            "source": source_uri,
            "installed_at": datetime.datetime.now().isoformat(),
            "path": str(target.resolve()),
        }
        self.save_registry()
        return target

    def add_plugin(self, name: str, source_dir: Path, source_uri: str = "local", metadata: Optional[Dict[str, Any]] = None) -> Path:
        """Copy or save a plugin directory into the central store."""
        target = self.plugins_dir / name
        if source_dir.resolve() != target.resolve():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source_dir, target, symlinks=True)

        inspected = inspect_plugin_dir(target)
        desc = (metadata and metadata.get("description")) or (inspected and inspected.get("description")) or ""
        version = (metadata and metadata.get("version")) or (inspected and inspected.get("version")) or "1.0.0"
        bundled = inspected.get("bundled_skills", []) if inspected else []

        self._registry["plugins"][name] = {
            "name": name,
            "type": "plugin",
            "description": desc,
            "version": version,
            "bundled_skills": bundled,
            "source": source_uri,
            "installed_at": datetime.datetime.now().isoformat(),
            "path": str(target.resolve()),
        }
        self.save_registry()
        return target

    def remove_skill(self, name: str) -> bool:
        """Remove a skill from the store and registry."""
        target = self.skills_dir / name
        removed = False
        if target.exists():
            shutil.rmtree(target)
            removed = True
        if name in self._registry["skills"]:
            del self._registry["skills"][name]
            self.save_registry()
            removed = True
        return removed

    def remove_plugin(self, name: str) -> bool:
        """Remove a plugin from the store and registry."""
        target = self.plugins_dir / name
        removed = False
        if target.exists():
            shutil.rmtree(target)
            removed = True
        if name in self._registry["plugins"]:
            del self._registry["plugins"][name]
            self.save_registry()
            removed = True
        return removed

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        return self._registry["skills"].get(name)

    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        return self._registry["plugins"].get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        return list(self._registry["skills"].values())

    def list_plugins(self) -> List[Dict[str, Any]]:
        return list(self._registry["plugins"].values())

    def get_all_exportable_skills(self) -> Dict[str, Path]:
        """
        Return a mapping of skill_name -> Path for all skills,
        including standalone skills and skills inside installed plugins.
        """
        result: Dict[str, Path] = {}

        # 1. Standalone skills in store/skills/
        for s_name, item in self._registry["skills"].items():
            p = Path(item["path"])
            if p.is_dir() and (p / "SKILL.md").exists():
                result[s_name] = p

        # 2. Bundled skills in store/plugins/<plugin>/skills/
        for p_name, item in self._registry["plugins"].items():
            p = Path(item["path"])
            skills_sub = p / "skills"
            if skills_sub.is_dir():
                for sub in skills_sub.iterdir():
                    if sub.is_dir() and (sub / "SKILL.md").exists():
                        # If not already present as standalone, register
                        if sub.name not in result:
                            result[sub.name] = sub

        return result
