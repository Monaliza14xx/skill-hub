"""Configuration management for skill-hub."""
import os
import json
from pathlib import Path
from typing import Dict, Any, List

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "sync_mode": "symlink",  # "symlink" or "copy"
    "auto_sync": True,
    "backup_on_overwrite": True,
    "enabled_targets": ["agy", "claude", "chatgpt", "kiro", "agents"],
    "custom_paths": {},
}

def get_hub_home() -> Path:
    """Return the base directory for skill-hub, defaulting to ~/.skill-hub."""
    override = os.environ.get("SKILL_HUB_HOME")
    if override:
        return Path(override).expanduser().resolve()
    
    preferred = Path.home() / ".skill-hub"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except (PermissionError, OSError):
        # Fallback in sandboxed environments
        for fallback in [Path.cwd() / ".skill-hub", Path("/tmp/skill-hub")]:
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                return fallback
            except (PermissionError, OSError):
                continue
        return preferred

class Config:
    def __init__(self, config_dir: Path = None):
        self.hub_home = config_dir or get_hub_home()
        self.config_file = self.hub_home / "config.json"
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk, creating default if not found."""
        if not self.config_file.exists():
            self._data = dict(DEFAULT_CONFIG)
            self.save()
            return

        try:
            content = self.config_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            self._data = dict(DEFAULT_CONFIG)
            self._data.update(loaded)
        except Exception:
            self._data = dict(DEFAULT_CONFIG)

    def save(self) -> None:
        """Save configuration to disk."""
        self.hub_home.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    @property
    def sync_mode(self) -> str:
        return self._data.get("sync_mode", "symlink")

    @sync_mode.setter
    def sync_mode(self, mode: str) -> None:
        if mode not in ("symlink", "copy"):
            raise ValueError(f"Invalid sync mode: {mode}. Must be 'symlink' or 'copy'.")
        self._data["sync_mode"] = mode
        self.save()

    @property
    def auto_sync(self) -> bool:
        return bool(self._data.get("auto_sync", True))

    @auto_sync.setter
    def auto_sync(self, val: bool) -> None:
        self._data["auto_sync"] = bool(val)
        self.save()

    @property
    def enabled_targets(self) -> List[str]:
        return list(self._data.get("enabled_targets", DEFAULT_CONFIG["enabled_targets"]))

    @enabled_targets.setter
    def enabled_targets(self, targets: List[str]) -> None:
        self._data["enabled_targets"] = targets
        self.save()

    def get_custom_path(self, target: str) -> str:
        return self._data.get("custom_paths", {}).get(target, "")

    def set_custom_path(self, target: str, path: str) -> None:
        if "custom_paths" not in self._data:
            self._data["custom_paths"] = {}
        self._data["custom_paths"][target] = path
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)
