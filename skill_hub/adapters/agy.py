"""Antigravity (AGY) Agent Adapter."""
from pathlib import Path
from typing import Optional, List
from skill_hub.adapters.base import BaseAdapter


class AgyAdapter(BaseAdapter):
    name = "agy"
    display_name = "Antigravity (AGY)"
    aliases = ["gemini", "antigravity"]

    def is_installed(self) -> bool:
        gemini_dir = Path.home() / ".gemini"
        return gemini_dir.exists()

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if self.custom_path:
            return Path(self.custom_path).expanduser()
        if global_scope:
            return Path.home() / ".gemini" / "config" / "skills"
        if workspace_path:
            return workspace_path / ".agents" / "skills"
        return Path.cwd() / ".agents" / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if global_scope:
            return Path.home() / ".gemini" / "config" / "plugins"
        if workspace_path:
            return workspace_path / ".agents" / "plugins"
        return Path.cwd() / ".agents" / "plugins"
