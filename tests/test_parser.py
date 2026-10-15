import unittest
import tempfile
import shutil
from pathlib import Path

from skill_hub.parser import (
    parse_frontmatter,
    format_skill_md,
    inspect_skill_dir,
    inspect_plugin_dir,
)

class TestParser(unittest.TestCase):
    def test_parse_frontmatter_simple(self):
        content = """---
name: test-skill
description: A test skill description
---
# Main Content
Hello world!
"""
        meta, body = parse_frontmatter(content)
        self.assertEqual(meta.get("name"), "test-skill")
        self.assertEqual(meta.get("description"), "A test skill description")
        self.assertTrue("Hello world!" in body)

    def test_parse_frontmatter_folded(self):
        content = """---
name: folded-skill
description: >-
  This is a very long description
  that spans multiple lines in YAML
  and should be joined with spaces.
---
Body text here.
"""
        meta, body = parse_frontmatter(content)
        self.assertEqual(meta.get("name"), "folded-skill")
        self.assertTrue("very long description that spans" in meta.get("description"))

    def test_format_skill_md(self):
        meta = {"name": "sample", "description": "Short description"}
        body = "## Guide\nDo this."
        formatted = format_skill_md(meta, body)
        self.assertTrue(formatted.startswith("---\nname: sample\n"))
        self.assertTrue("Short description" in formatted)
        self.assertTrue("## Guide" in formatted)

    def test_inspect_skill_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / "SKILL.md").write_text("""---
name: my-inspected-skill
description: Inspected description
---
Body
""", encoding="utf-8")
            res = inspect_skill_dir(temp_dir)
            self.assertIsNotNone(res)
            self.assertEqual(res["name"], "my-inspected-skill")
            self.assertEqual(res["description"], "Inspected description")
        finally:
            shutil.rmtree(temp_dir)

    def test_inspect_plugin_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / "plugin.json").write_text('{"name": "my-plugin", "version": "2.0.0"}', encoding="utf-8")
            skills_dir = temp_dir / "skills" / "subskill"
            skills_dir.mkdir(parents=True)
            (skills_dir / "SKILL.md").write_text("---\nname: subskill\ndescription: sub\n---\n", encoding="utf-8")
            res = inspect_plugin_dir(temp_dir)
            self.assertIsNotNone(res)
            self.assertEqual(res["name"], "my-plugin")
            self.assertEqual(res["version"], "2.0.0")
            self.assertEqual(res["bundled_skills"], ["subskill"])
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
