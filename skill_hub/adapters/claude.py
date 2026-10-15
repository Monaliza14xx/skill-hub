"""Claude Code Adapter."""
from pathlib import Path
from typing import Optional, List
from skill_hub.adapters.base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    name = "claude"
    display_name = "Claude Code"
    aliases = ["claude-code", "anthropic"]

    def is_installed(self) -> bool:
        claude_dir = Path.home() / ".claude"
        claude_json = Path.home() / ".claude.json"
        return claude_dir.exists() or claude_json.exists()

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if self.custom_path:
            return Path(self.custom_path).expanduser()
        if global_scope:
            return Path.home() / ".claude" / "skills"
        if workspace_path:
            return workspace_path / ".claude" / "skills"
        return Path.cwd() / ".claude" / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if global_scope:
            return Path.home() / ".claude" / "plugins"
        if workspace_path:
            return workspace_path / ".claude" / "plugins"
        return Path.cwd() / ".claude" / "plugins"
