import unittest
import tempfile
import shutil
from pathlib import Path

from skill_hub.config import Config
from skill_hub.hub import Hub
from skill_hub.adapters.base import BaseAdapter

class MockTargetAdapter(BaseAdapter):
    def __init__(self, name: str, root_dir: Path):
        super().__init__()
        self.name = name
        self.display_name = f"Mock {name}"
        self.root_dir = root_dir

    def is_installed(self) -> bool:
        return True

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Path = None) -> Path:
        return self.root_dir / self.name / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Path = None) -> Path:
        return self.root_dir / self.name / "plugins"

class TestHub(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp())
        self.hub_dir = self.temp_root / "hub"
        self.agents_root = self.temp_root / "agents"

        self.config = Config(config_dir=self.hub_dir)
        self.config.enabled_targets = ["agent1", "agent2"]
        self.config.sync_mode = "symlink"

        self.hub = Hub(config=self.config)

        # Inject mock adapters
        adapter1 = MockTargetAdapter("agent1", self.agents_root)
        adapter2 = MockTargetAdapter("agent2", self.agents_root)
        self.hub.adapter_registry._adapters = {
            "agent1": adapter1,
            "agent2": adapter2,
        }
        self.hub.adapter_registry._alias_map = {
            "agent1": "agent1",
            "agent2": "agent2",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_install_local_skill_and_sync(self):
        # Create a local skill folder to install
        source_skill = self.temp_root / "sample_skill"
        source_skill.mkdir()
        (source_skill / "SKILL.md").write_text("""---
name: sample-calc
description: Fast math calculator
---
# Calculator Instructions
""", encoding="utf-8")

        res = self.hub.install(str(source_skill), sync_after=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["name"], "sample-calc")
        self.assertTrue(res["synced"])

        # Verify skill is in store
        self.assertIsNotNone(self.hub.store.get_skill("sample-calc"))

        # Verify skill was synced to both mock adapters
        for agent_name in ["agent1", "agent2"]:
            dest_skill = self.agents_root / agent_name / "skills" / "sample-calc"
            self.assertTrue(dest_skill.exists())
            self.assertTrue((dest_skill / "SKILL.md").exists())

    def test_create_skill(self):
        skill_dir = self.hub.create("fast-writer", description="Write essays fast")
        self.assertTrue(skill_dir.exists())
        self.assertTrue((skill_dir / "SKILL.md").exists())
        self.assertIsNotNone(self.hub.store.get_skill("fast-writer"))

        # Since auto-sync is on by default, verify it reached target agents
        for agent_name in ["agent1", "agent2"]:
            dest = self.agents_root / agent_name / "skills" / "fast-writer"
            self.assertTrue(dest.exists())

    def test_uninstall_skill(self):
        source = self.temp_root / "temp_skill"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: temp-skill\n---\n", encoding="utf-8")
        self.hub.install(str(source), sync_after=True)

        # Confirm synced
        self.assertTrue((self.agents_root / "agent1" / "skills" / "temp-skill").exists())

        # Now uninstall
        removed = self.hub.uninstall("temp-skill")
        self.assertTrue(removed)

        # Check removed from store
        self.assertIsNone(self.hub.store.get_skill("temp-skill"))

        # Check unlinked from agents
        for agent_name in ["agent1", "agent2"]:
            dest = self.agents_root / agent_name / "skills" / "temp-skill"
            self.assertFalse(dest.exists())

if __name__ == "__main__":
    unittest.main()
