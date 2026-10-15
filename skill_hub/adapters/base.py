"""Base adapter class for AI tool integration."""
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List


class BaseAdapter:
    name: str = "base"
    display_name: str = "Base Agent"
    aliases: List[str] = []

    def __init__(self, custom_path: Optional[str] = None):
        self.custom_path = custom_path

    def is_installed(self) -> bool:
        """Check if the AI tool directory or binary is detected."""
        skills_dir = self.get_skills_dir(global_scope=True)
        if skills_dir and skills_dir.parent.exists():
            return True
        return False

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        """Return the skills directory for this tool."""
        raise NotImplementedError

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        """Return the plugins directory for this tool."""
        return None

    def ensure_dir(self, path: Path) -> bool:
        """Safely ensure directory exists."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def sync_skill(
        self,
        skill_name: str,
        source_path: Path,
        mode: str = "symlink",
        global_scope: bool = True,
        workspace_path: Optional[Path] = None,
    ) -> Tuple[bool, str]:
        """Sync a single skill into this tool's skill folder."""
        dest_dir = self.get_skills_dir(global_scope=global_scope, workspace_path=workspace_path)
        if not dest_dir:
            return False, "Target skills directory not supported"

        if not self.ensure_dir(dest_dir):
            return False, f"Could not create target directory {dest_dir}"

        dest_link = dest_dir / skill_name

        try:
            # If already exists and is a symlink pointing to source
            if dest_link.is_symlink():
                target = dest_link.resolve()
                if target == source_path.resolve():
                    return True, "Already up-to-date (symlink)"
                dest_link.unlink()
            elif dest_link.exists():
                # Regular file or dir exists - back it up or replace
                backup_name = dest_dir / f"{skill_name}.bak"
                if backup_name.exists():
                    if backup_name.is_dir():
                        shutil.rmtree(backup_name)
                    else:
                        backup_name.unlink()
                dest_link.rename(backup_name)

            if mode == "symlink":
                dest_link.symlink_to(source_path.resolve(), target_is_directory=True)
                return True, "Symlinked"
            else:
                shutil.copytree(source_path, dest_link, symlinks=True)
                return True, "Copied"
        except Exception as e:
            return False, f"Error: {e}"

    def unlink_skill(
        self,
        skill_name: str,
        global_scope: bool = True,
        workspace_path: Optional[Path] = None,
    ) -> bool:
        """Unlink/remove a skill from this tool's skill folder."""
        dest_dir = self.get_skills_dir(global_scope=global_scope, workspace_path=workspace_path)
        if not dest_dir or not dest_dir.exists():
            return False

        target = dest_dir / skill_name
        if target.is_symlink() or target.is_file():
            target.unlink()
            return True
        elif target.is_dir():
            shutil.rmtree(target)
            return True
        return False

    def sync_plugin(
        self,
        plugin_name: str,
        source_path: Path,
        mode: str = "symlink",
        global_scope: bool = True,
        workspace_path: Optional[Path] = None,
    ) -> Tuple[bool, str]:
        """Sync a plugin bundle into this tool's plugins folder."""
        dest_dir = self.get_plugins_dir(global_scope=global_scope, workspace_path=workspace_path)
        if not dest_dir:
            return False, "Target plugins directory not supported"

        if not self.ensure_dir(dest_dir):
            return False, f"Could not create target directory {dest_dir}"

        dest_link = dest_dir / plugin_name

        try:
            if dest_link.is_symlink():
                target = dest_link.resolve()
                if target == source_path.resolve():
                    return True, "Already up-to-date (symlink)"
                dest_link.unlink()
            elif dest_link.exists():
                backup_name = dest_dir / f"{plugin_name}.bak"
                if backup_name.exists():
                    if backup_name.is_dir():
                        shutil.rmtree(backup_name)
                    else:
                        backup_name.unlink()
                dest_link.rename(backup_name)

            if mode == "symlink":
                dest_link.symlink_to(source_path.resolve(), target_is_directory=True)
                return True, "Symlinked"
            else:
                shutil.copytree(source_path, dest_link, symlinks=True)
                return True, "Copied"
        except Exception as e:
            return False, f"Error: {e}"

    def unlink_plugin(
        self,
        plugin_name: str,
        global_scope: bool = True,
        workspace_path: Optional[Path] = None,
    ) -> bool:
        """Unlink/remove a plugin from this tool's plugins folder."""
        dest_dir = self.get_plugins_dir(global_scope=global_scope, workspace_path=workspace_path)
        if not dest_dir or not dest_dir.exists():
            return False

        target = dest_dir / plugin_name
        if target.is_symlink() or target.is_file():
            target.unlink()
            return True
        elif target.is_dir():
            shutil.rmtree(target)
            return True
        return False

    def clean_broken_links(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> int:
        """Remove broken symlinks in skills and plugins directories."""
        cleaned = 0
        for d in [self.get_skills_dir(global_scope, workspace_path), self.get_plugins_dir(global_scope, workspace_path)]:
            if d and d.is_dir():
                try:
                    for item in d.iterdir():
                        if item.is_symlink() and not item.exists():
                            item.unlink()
                            cleaned += 1
                except Exception:
                    pass
        return cleaned

    def doctor(self) -> Dict[str, Any]:
        """Check health and diagnostic information for this adapter."""
        skills_dir = self.get_skills_dir(global_scope=True)
        plugins_dir = self.get_plugins_dir(global_scope=True)
        installed = self.is_installed()

        skills_count = 0
        if skills_dir and skills_dir.is_dir():
            try:
                skills_count = len([x for x in skills_dir.iterdir() if x.is_dir() or x.is_symlink()])
            except Exception:
                pass

        plugins_count = 0
        if plugins_dir and plugins_dir.is_dir():
            try:
                plugins_count = len([x for x in plugins_dir.iterdir() if x.is_dir() or x.is_symlink()])
            except Exception:
                pass

        return {
            "name": self.name,
            "display_name": self.display_name,
            "installed": installed,
            "skills_dir": str(skills_dir) if skills_dir else None,
            "plugins_dir": str(plugins_dir) if plugins_dir else None,
            "skills_count": skills_count,
            "plugins_count": plugins_count,
        }
