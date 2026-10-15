"""Registry and factory for AI tool adapters."""
from typing import Dict, List, Optional, Type
from skill_hub.adapters.base import BaseAdapter
from skill_hub.adapters.agy import AgyAdapter
from skill_hub.adapters.claude import ClaudeAdapter
from skill_hub.adapters.codex import CodexAdapter
from skill_hub.adapters.kiro import KiroAdapter
from skill_hub.adapters.universal import UniversalAdapter

ALL_ADAPTER_CLASSES: List[Type[BaseAdapter]] = [
    AgyAdapter,
    ClaudeAdapter,
    CodexAdapter,
    KiroAdapter,
    UniversalAdapter,
]


class AdapterRegistry:
    def __init__(self, custom_paths: Optional[Dict[str, str]] = None):
        self.custom_paths = custom_paths or {}
        self._adapters: Dict[str, BaseAdapter] = {}
        self._alias_map: Dict[str, str] = {}
        self._init_adapters()

    def _init_adapters(self) -> None:
        for cls in ALL_ADAPTER_CLASSES:
            custom = self.custom_paths.get(cls.name)
            instance = cls(custom_path=custom)
            self._adapters[instance.name] = instance
            self._alias_map[instance.name] = instance.name
            for alias in instance.aliases:
                self._alias_map[alias.lower()] = instance.name

    def get_adapter(self, name_or_alias: str) -> Optional[BaseAdapter]:
        key = name_or_alias.strip().lower()
        canonical_name = self._alias_map.get(key)
        if canonical_name:
            return self._adapters.get(canonical_name)
        return None

    def list_adapters(self) -> List[BaseAdapter]:
        return list(self._adapters.values())

    def get_installed_adapters(self) -> List[BaseAdapter]:
        return [a for a in self._adapters.values() if a.is_installed()]

    def resolve_targets(self, target_names: List[str]) -> List[BaseAdapter]:
        """Resolve a list of target names or aliases to BaseAdapter instances."""
        resolved: List[BaseAdapter] = []
        seen = set()
        for t in target_names:
            adapter = self.get_adapter(t)
            if adapter and adapter.name not in seen:
                seen.add(adapter.name)
                resolved.append(adapter)
        return resolved
