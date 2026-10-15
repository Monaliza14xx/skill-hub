import unittest
import tempfile
import shutil
from pathlib import Path

from skill_hub.adapters.registry import AdapterRegistry
from skill_hub.adapters.base import BaseAdapter

class MockAdapter(BaseAdapter):
    name = "mock"
    display_name = "Mock Adapter"
    aliases = ["m"]

    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir

    def is_installed(self) -> bool:
        return True

    def get_skills_dir(self, global_scope: bool = True, workspace_path: Path = None) -> Path:
        return self.base_dir / "skills"

    def get_plugins_dir(self, global_scope: bool = True, workspace_path: Path = None) -> Path:
        return self.base_dir / "plugins"

class TestAdapters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.adapter = MockAdapter(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sync_skill_symlink(self):
        src_skill = self.temp_dir / "source_skill"
        src_skill.mkdir()
        (src_skill / "SKILL.md").write_text("---\nname: s1\n---\n", encoding="utf-8")

        ok, msg = self.adapter.sync_skill("s1", src_skill, mode="symlink")
        self.assertTrue(ok)

        dest = self.adapter.get_skills_dir() / "s1"
        self.assertTrue(dest.is_symlink())
        self.assertTrue((dest / "SKILL.md").exists())

    def test_sync_skill_copy(self):
        src_skill = self.temp_dir / "source_skill2"
        src_skill.mkdir()
        (src_skill / "SKILL.md").write_text("---\nname: s2\n---\n", encoding="utf-8")

        ok, msg = self.adapter.sync_skill("s2", src_skill, mode="copy")
        self.assertTrue(ok)

        dest = self.adapter.get_skills_dir() / "s2"
        self.assertTrue(dest.is_dir())
        self.assertFalse(dest.is_symlink())

    def test_unlink_skill(self):
        src_skill = self.temp_dir / "source_skill3"
        src_skill.mkdir()
        self.adapter.sync_skill("s3", src_skill, mode="symlink")
        dest = self.adapter.get_skills_dir() / "s3"
        self.assertTrue(dest.exists())

        unlinked = self.adapter.unlink_skill("s3")
        self.assertTrue(unlinked)
        self.assertFalse(dest.exists())

    def test_clean_broken_links(self):
        skills_dir = self.adapter.get_skills_dir()
        skills_dir.mkdir(parents=True)
        ghost = skills_dir / "broken"
        ghost.symlink_to(self.temp_dir / "non_existent_file")
        self.assertTrue(ghost.is_symlink())

        cleaned = self.adapter.clean_broken_links()
        self.assertEqual(cleaned, 1)
        self.assertFalse(ghost.exists(follow_symlinks=False))

    def test_registry_lookup(self):
        registry = AdapterRegistry()
        agy = registry.get_adapter("agy")
        self.assertIsNotNone(agy)
        self.assertEqual(agy.name, "agy")

        gemini_alias = registry.get_adapter("gemini")
        self.assertEqual(gemini_alias.name, "agy")

        claude = registry.get_adapter("claude")
        self.assertIsNotNone(claude)

        kiri = registry.get_adapter("kiri")
        self.assertIsNotNone(kiri)
        self.assertEqual(kiri.name, "kiro")

        codex = registry.get_adapter("codex")
        self.assertIsNotNone(codex)
        self.assertEqual(codex.name, "chatgpt")

if __name__ == "__main__":
    unittest.main()
