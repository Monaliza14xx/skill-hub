import unittest
import tempfile
import shutil
from pathlib import Path

from skill_hub.config import Config
from skill_hub.store import Store

class TestStore(unittest.TestCase):
    def setUp(self):
        self.temp_home = Path(tempfile.mkdtemp())
        self.config = Config(config_dir=self.temp_home)
        self.store = Store(config=self.config)

    def tearDown(self):
        shutil.rmtree(self.temp_home, ignore_errors=True)

    def test_add_and_list_skill(self):
        skill_src = self.temp_home / "src_skill"
        skill_src.mkdir()
        (skill_src / "SKILL.md").write_text("---\nname: alpha-skill\ndescription: Test alpha\n---\n# Body\n", encoding="utf-8")

        target = self.store.add_skill("alpha-skill", skill_src, source_uri="local:test")
        self.assertTrue(target.exists())
        self.assertTrue((target / "SKILL.md").exists())

        skills = self.store.list_skills()
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "alpha-skill")

    def test_add_plugin_and_exportable_skills(self):
        plugin_src = self.temp_home / "src_plugin"
        plugin_src.mkdir()
        (plugin_src / "plugin.json").write_text('{"name": "bundle-plugin", "version": "1.0.0"}', encoding="utf-8")
        sub_skill = plugin_src / "skills" / "bundled-one"
        sub_skill.mkdir(parents=True)
        (sub_skill / "SKILL.md").write_text("---\nname: bundled-one\ndescription: Bundled\n---\n", encoding="utf-8")

        self.store.add_plugin("bundle-plugin", plugin_src, source_uri="local:plugin")
        plugins = self.store.list_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["name"], "bundle-plugin")

        exportable = self.store.get_all_exportable_skills()
        self.assertIn("bundled-one", exportable)

    def test_remove_skill(self):
        skill_src = self.temp_home / "src_skill"
        skill_src.mkdir()
        (skill_src / "SKILL.md").write_text("---\nname: to-remove\ndescription: Remove me\n---\n", encoding="utf-8")
        self.store.add_skill("to-remove", skill_src)

        removed = self.store.remove_skill("to-remove")
        self.assertTrue(removed)
        self.assertEqual(len(self.store.list_skills()), 0)

if __name__ == "__main__":
    unittest.main()
