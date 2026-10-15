"""ChatGPT / Codex Adapter."""
from pathlib import Path
from typing import Optional, List
from skill_hub.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    name = "chatgpt"
    display_name = "ChatGPT / Codex"
    aliases = ["codex", "openai", "chatgpt-cli"]

    def is_installed(self) -> bool:
        codex_dir = Path.home() / ".codex"
        chatgpt_dir = Path.home() / ".chatgpt"
        return codex_dir.exists() or chatgpt_dir.exists()

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if self.custom_path:
            return Path(self.custom_path).expanduser()
        if global_scope:
            codex_dir = Path.home() / ".codex"
            if codex_dir.exists():
                return codex_dir / "skills"
            return Path.home() / ".codex" / "skills"
        if workspace_path:
            return workspace_path / ".codex" / "skills"
        return Path.cwd() / ".codex" / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Optional[Path] = None) -> Optional[Path]:
        if global_scope:
            return Path.home() / ".codex" / "plugins"
        if workspace_path:
            return workspace_path / ".codex" / "plugins"
        return Path.cwd() / ".codex" / "plugins"
