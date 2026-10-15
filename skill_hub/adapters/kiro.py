"""Kiro / Kiri / Kimi Agent Adapter."""
from pathlib import Path
from typing import Optional, List
from skill_hub.adapters.base import BaseAdapter


class KiroAdapter(BaseAdapter):
    name = "kiro"
    display_name = "Kiro / Kiri"
    aliases = ["kiri", "kimi", "kiro-cli"]

    def is_installed(self) -> bool:
        home = Path.home()
        return (home / ".kiro").exists() or (home / ".kiri").exists() or (home / ".kimi").exists()

    def _resolve_base_dir(self) -> Path:
        home = Path.home()
        if (home / ".kiro").exists():
            return home / ".kiro"
        if (home / ".kiri").exists():
            return home / ".kiri"
        if (home / ".kimi").exists():
            return home / ".kimi"
        return home / ".kiro"

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if self.custom_path:
            return Path(self.custom_path).expanduser()
        if global_scope:
            return self._resolve_base_dir() / "skills"
        if workspace_path:
            return workspace_path / ".kiro" / "skills"
        return Path.cwd() / ".kiro" / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if global_scope:
            return self._resolve_base_dir() / "plugins"
        if workspace_path:
            return workspace_path / ".kiro" / "plugins"
        return Path.cwd() / ".kiro" / "plugins"
