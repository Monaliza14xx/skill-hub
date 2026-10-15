"""Parser for SKILL.md files and plugin manifests without external dependencies."""
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter enclosed in --- at the start of a markdown file.
    Returns (metadata_dict, body_markdown).
    """
    if not content.startswith("---"):
        return {}, content

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    frontmatter_lines = lines[1:end_idx]
    body_lines = lines[end_idx + 1:]
    body = "\n".join(body_lines).strip()

    metadata: Dict[str, Any] = {}
    current_key: Optional[str] = None
    multiline_val: List[str] = []
    multiline_mode: Optional[str] = None  # '>-', '|', 'list'

    for line in frontmatter_lines:
        # Check for list item under current key
        if current_key and line.strip().startswith("- ") and multiline_mode == "list":
            item = line.strip()[2:].strip()
            metadata[current_key].append(item)
            continue

        # Check for multiline continuation (indented)
        if current_key and (line.startswith("  ") or line.startswith("\t")):
            multiline_val.append(line.strip())
            continue

        # If we had a multiline value ongoing, commit it
        if current_key and multiline_val:
            if multiline_mode in (">-", ">"):
                metadata[current_key] = " ".join(multiline_val).strip()
            elif multiline_mode in ("|", "|-"):
                metadata[current_key] = "\n".join(multiline_val).strip()
            multiline_val = []
            multiline_mode = None

        # Check for key-value pair
        match = re.match(r"^([a-zA-Z0-9_-]+)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1).strip()
            val = match.group(2).strip()

            if val in (">-", ">", "|", "|-"):
                current_key = key
                multiline_mode = val
                multiline_val = []
                metadata[key] = ""
            elif val == "":
                current_key = key
                multiline_mode = "list"
                metadata[key] = []
            else:
                current_key = None
                multiline_mode = None
                # Strip quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                metadata[key] = val

    # Flush any remaining multiline
    if current_key and multiline_val:
        if multiline_mode in (">-", ">"):
            metadata[current_key] = " ".join(multiline_val).strip()
        elif multiline_mode in ("|", "|-"):
            metadata[current_key] = "\n".join(multiline_val).strip()

    return metadata, body


def format_skill_md(metadata: Dict[str, Any], body: str) -> str:
    """Serialize metadata dict and body into a SKILL.md format."""
    lines = ["---"]
    for k, v in metadata.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        elif "\n" in str(v) or len(str(v)) > 80:
            lines.append(f"{k}: >-")
            # Break into wrapped lines
            words = str(v).split()
            current_line = "  "
            for w in words:
                if len(current_line) + len(w) + 1 > 78:
                    lines.append(current_line)
                    current_line = "  " + w
                else:
                    current_line = f"{current_line} {w}".strip()
                    current_line = "  " + current_line
            if current_line.strip():
                lines.append(current_line)
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


def inspect_skill_dir(dir_path: Path) -> Optional[Dict[str, Any]]:
    """Inspect a directory to see if it is a skill (contains SKILL.md)."""
    skill_file = dir_path / "SKILL.md"
    if not skill_file.is_file():
        # Check lowercase skill.md
        skill_file = dir_path / "skill.md"
        if not skill_file.is_file():
            return None

    try:
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(content)
        name = meta.get("name") or dir_path.name
        desc = meta.get("description", "").strip()
        return {
            "type": "skill",
            "name": name,
            "description": desc,
            "path": str(dir_path.resolve()),
            "skill_file": str(skill_file.resolve()),
            "metadata": meta,
            "has_scripts": (dir_path / "scripts").is_dir(),
            "has_references": (dir_path / "references").is_dir(),
        }
    except Exception as e:
        return None


def inspect_plugin_dir(dir_path: Path) -> Optional[Dict[str, Any]]:
    """Inspect a directory to see if it is a plugin bundle."""
    import json
    
    manifest_file = None
    manifest_data = {}
    
    for candidate in ["plugin.json", "gemini-extension.json", "package.json"]:
        p = dir_path / candidate
        if p.is_file():
            try:
                manifest_data = json.loads(p.read_text(encoding="utf-8"))
                manifest_file = p
                break
            except Exception:
                pass

    # If no JSON manifest found, check if it has skills/ and rules/
    skills_dir = dir_path / "skills"
    has_skills = skills_dir.is_dir()
    
    if not manifest_file and not has_skills:
        return None

    # Find bundled skills
    bundled_skills = []
    if has_skills:
        for item in skills_dir.iterdir():
            if item.is_dir():
                s = inspect_skill_dir(item)
                if s:
                    bundled_skills.append(s["name"])

    name = manifest_data.get("name") or dir_path.name
    desc = manifest_data.get("description", "")
    version = manifest_data.get("version", "1.0.0")

    return {
        "type": "plugin",
        "name": name,
        "description": desc,
        "version": version,
        "path": str(dir_path.resolve()),
        "manifest_file": str(manifest_file.resolve()) if manifest_file else None,
        "bundled_skills": bundled_skills,
        "has_rules": any((dir_path / r).exists() for r in ["AGENTS.md", "GEMINI.md", "CLAUDE.md", "rules"]),
        "has_commands": (dir_path / "commands").is_dir(),
        "has_hooks": (dir_path / "hooks").is_dir(),
    }
