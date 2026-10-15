"""Universal OpenAgent (.agents) Adapter."""
from pathlib import Path
from typing import Optional, List
from skill_hub.adapters.base import BaseAdapter


class UniversalAdapter(BaseAdapter):
    name = "agents"
    display_name = "Universal OpenAgent (.agents)"
    aliases = ["universal", "standard", "openagent", "all-agents"]

    def is_installed(self) -> bool:
        return (Path.home() / ".agents").exists()

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if self.custom_path:
            return Path(self.custom_path).expanduser()
        if global_scope:
            return Path.home() / ".agents" / "skills"
        if workspace_path:
            return workspace_path / ".agents" / "skills"
        return Path.cwd() / ".agents" / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if global_scope:
            return Path.home() / ".agents" / "plugins"
        if workspace_path:
            return workspace_path / ".agents" / "plugins"
        return Path.cwd() / ".agents" / "plugins"
