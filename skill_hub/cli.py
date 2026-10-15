"""Command-line interface for skill-hub."""
import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional

from skill_hub.config import Config
from skill_hub.hub import Hub
from skill_hub.curated import find_in_curated, CURATED_REGISTRY
from skill_hub.ui import (
    style,
    Color,
    success,
    failure,
    warning,
    info,
    bullet,
    highlight,
    banner,
    print_table,
    prettify_path,
)

VERSION = "1.0.0"


def cmd_install(hub: Hub, args: argparse.Namespace) -> int:
    source = args.source
    name = args.name
    sync_after = not args.no_sync
    targets = args.targets.split(",") if args.targets else None

    print(f"\n{info(f'Installing from: {highlight(source)} ...')}")

    try:
        res = hub.install(source, name=name, sync_after=sync_after, targets=targets)
        itype = res.get("type", "item").capitalize()
        iname = res.get("name")
        print(success(f"Installed {itype} '{highlight(iname)}' to store!"))

        if res.get("synced"):
            sync_details = res.get("sync_details", {})
            print(f"\n{style('Sync Results:', Color.BOLD)}")
            for t_name, stats in sync_details.get("targets", {}).items():
                err_text = f" ({len(stats['errors'])} errors)" if stats["errors"] else ""
                print(bullet(
                    f"{stats['display_name']}: "
                    f"{style(str(stats['skills_synced']), Color.GREEN)} skills, "
                    f"{style(str(stats['plugins_synced']), Color.CYAN)} plugins synced{err_text}"
                ))
                for err in stats["errors"]:
                    print(f"      {style(err, Color.RED)}")
        else:
            print(info("Auto-sync skipped. Run 'skill-hub sync' to distribute across AI tools."))

        return 0
    except Exception as e:
        print(failure(f"Installation failed: {e}"))
        return 1


def cmd_sync(hub: Hub, args: argparse.Namespace) -> int:
    targets = args.targets.split(",") if args.targets else None
    mode = args.mode
    scope = args.scope
    workspace = Path(args.workspace) if args.workspace else Path.cwd()

    print(f"\n{info(f'Syncing skills and plugins across AI tools (mode={mode or hub.config.sync_mode}, scope={scope})...')}")

    try:
        res = hub.sync(targets=targets, mode=mode, scope=scope, workspace_path=workspace)
        print(f"\n{style('=== Sync Summary ===', Color.CYAN, Color.BOLD)}")
        print(f"Total skills available:  {style(str(res['total_skills_available']), Color.GREEN, Color.BOLD)}")
        print(f"Total plugins available: {style(str(res['total_plugins_available']), Color.CYAN, Color.BOLD)}\n")

        has_errors = False
        for t_name, stats in res.get("targets", {}).items():
            cleaned_str = f" [cleaned {stats['cleaned']} dead links]" if stats["cleaned"] > 0 else ""
            status_symbol = style("✓", Color.GREEN, Color.BOLD) if not stats["errors"] else style("⚠", Color.YELLOW, Color.BOLD)
            print(f"  {status_symbol} {style(stats['display_name'], Color.BOLD)}:")
            print(f"      • Skills synced:  {style(str(stats['skills_synced']), Color.GREEN)}")
            print(f"      • Plugins synced: {style(str(stats['plugins_synced']), Color.CYAN)}{cleaned_str}")
            if stats["errors"]:
                has_errors = True
                for err in stats["errors"]:
                    print(f"      {style('✗ ' + err, Color.RED)}")

        print(f"\n{success('All AI tools updated! Agents can now use your skills immediately.')}")
        return 1 if has_errors else 0
    except Exception as e:
        print(failure(f"Sync failed: {e}"))
        return 1


def cmd_list(hub: Hub, args: argparse.Namespace) -> int:
    skills = hub.store.list_skills()
    plugins = hub.store.list_plugins()

    if args.json:
        out = {
            "skills": skills,
            "plugins": plugins,
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"\n{banner('Installed Skills & Plugins in Skill-Hub', f'Central Store: {prettify_path(hub.store.store_dir)}')}\n")

    # Skills Table
    print(style("Standalone Skills:", Color.BOLD, Color.CYAN))
    if not skills:
        print(style("  No standalone skills installed yet. Run 'skill-hub install <source>' or 'skill-hub import'.", Color.GRAY))
    else:
        headers = ["NAME", "DESCRIPTION", "SOURCE"]
        rows = []
        for s in skills:
            desc = s.get("description", "")
            if len(desc) > 60:
                desc = desc[:57] + "..."
            rows.append([
                style(s["name"], Color.GREEN, Color.BOLD),
                desc,
                style(s.get("source", "local"), Color.GRAY),
            ])
        print_table(headers, rows)

    print()

    # Plugins Table
    print(style("Installed Plugins:", Color.BOLD, Color.CYAN))
    if not plugins:
        print(style("  No plugins installed yet.", Color.GRAY))
    else:
        headers = ["NAME", "VERSION", "BUNDLED SKILLS", "SOURCE"]
        rows = []
        for p in plugins:
            bundled = ", ".join(p.get("bundled_skills", []))
            if len(bundled) > 40:
                bundled = bundled[:37] + "..."
            rows.append([
                style(p["name"], Color.CYAN, Color.BOLD),
                p.get("version", "1.0.0"),
                bundled or style("none", Color.GRAY),
                style(p.get("source", "local"), Color.GRAY),
            ])
        print_table(headers, rows)

    print(f"\n{info(f'Total: {len(skills)} skills, {len(plugins)} plugins.')}")
    return 0


def cmd_uninstall(hub: Hub, args: argparse.Namespace) -> int:
    name = args.name
    print(f"\n{info(f'Removing {highlight(name)} from skill-hub and all AI tools...')}")

    ok = hub.uninstall(name)
    if ok:
        print(success(f"Successfully uninstalled '{name}'."))
        return 0
    else:
        print(warning(f"Item '{name}' not found in store."))
        return 1


def cmd_import(hub: Hub, args: argparse.Namespace) -> int:
    from_target = args.from_target
    print(f"\n{info(f'Scanning existing AI tools for skills to import into central hub (source: {from_target})...')}")

    res = hub.import_existing(from_target=from_target)
    imported_skills = res.get("imported_skills", [])
    imported_plugins = res.get("imported_plugins", [])

    if not imported_skills and not imported_plugins:
        print(info("No new unmanaged skills or plugins discovered to import."))
    else:
        if imported_skills:
            print(success(f"Imported {len(imported_skills)} skills: {', '.join(imported_skills)}"))
        if imported_plugins:
            print(success(f"Imported {len(imported_plugins)} plugins: {', '.join(imported_plugins)}"))

        # Ask/Trigger sync
        if not args.no_sync:
            print(f"\n{info('Distributing imported skills across all AI tools...')}")
            hub.sync()
            print(success("All AI tools are now synchronized with imported skills!"))

    return 0


def cmd_doctor(hub: Hub, args: argparse.Namespace) -> int:
    diag = hub.doctor()

    print(f"\n{banner('Skill-Hub System Diagnostics')}\n")
    print(f"Hub Home:             {style(prettify_path(diag['hub_home']), Color.BOLD)}")
    print(f"Sync Mode:            {style(diag['sync_mode'], Color.CYAN)}")
    print(f"Auto-Sync:            {style(str(diag['auto_sync']), Color.GREEN)}")
    print(f"Stored Skills Count:  {style(str(diag['stored_skills_count']), Color.BOLD)}")
    print(f"Stored Plugins Count: {style(str(diag['stored_plugins_count']), Color.BOLD)}")
    print()

    print(style("Target AI Agent Tools Status:", Color.BOLD, Color.UNDERLINE))
    headers = ["AGENT TOOL", "DETECTED", "SKILLS DIR", "SKILLS COUNT", "PLUGINS DIR"]
    rows = []
    for a in diag.get("adapters", []):
        detected_str = style("YES", Color.GREEN, Color.BOLD) if a["installed"] else style("NO", Color.GRAY)
        skills_path = prettify_path(a.get("skills_dir")) if a.get("skills_dir") else "None"
        plugins_path = prettify_path(a.get("plugins_dir")) if a.get("plugins_dir") else "None"
        rows.append([
            style(a["display_name"], Color.BOLD),
            detected_str,
            skills_path,
            str(a.get("skills_count", 0)),
            plugins_path,
        ])
    print_table(headers, rows)
    print()
    return 0


def cmd_create(hub: Hub, args: argparse.Namespace) -> int:
    name = args.name
    desc = args.description or ""
    print(f"\n{info(f'Scaffolding new skill: {highlight(name)}...')}")

    try:
        skill_dir = hub.create(name, description=desc)
        print(success(f"Created skill template at: {style(prettify_path(skill_dir), Color.BOLD)}"))
        print(f"  • Edit instructions in: {style(prettify_path(skill_dir / 'SKILL.md'), Color.CYAN)}")
        if hub.config.auto_sync:
            print(success("Skill automatically synced to all enabled AI tools!"))
        return 0
    except Exception as e:
        print(failure(f"Failed to create skill: {e}"))
        return 1


def cmd_search(hub: Hub, args: argparse.Namespace) -> int:
    query = args.query or ""
    print(f"\n{banner('Curated Skills & Plugins Catalog', f'Search query: \"{query}\"')}\n")

    results = find_in_curated(query) if query else list(CURATED_REGISTRY.values())

    if not results:
        print(style(f"No skills or plugins matching '{query}' found.", Color.GRAY))
        return 0

    headers = ["NAME", "TYPE", "DESCRIPTION", "TAGS"]
    rows = []
    for item in results:
        tags = ", ".join(item.get("tags", []))
        desc = item.get("description", "")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        type_str = style(item["type"], Color.GREEN) if item["type"] == "skill" else style(item["type"], Color.CYAN)
        rows.append([
            style(item["name"], Color.BOLD),
            type_str,
            desc,
            style(tags, Color.GRAY),
        ])
    print_table(headers, rows)
    print(f"\n{info('Install any item with: skill-hub install <name>')}\n")
    return 0


def cmd_config(hub: Hub, args: argparse.Namespace) -> int:
    action = args.action
    key = args.key
    val = args.val

    if action == "show" or not action:
        print(f"\n{banner('Skill-Hub Current Configuration')}\n")
        print(json.dumps(hub.config.to_dict(), indent=2))
        return 0
    elif action == "get":
        if not key:
            print(failure("Please specify key to get."))
            return 1
        print(hub.config.get(key))
        return 0
    elif action == "set":
        if not key or val is None:
            print(failure("Usage: skill-hub config set <key> <value>"))
            return 1
        # Parse boolean or list if needed
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        elif "," in val and key == "enabled_targets":
            val = [x.strip() for x in val.split(",")]
        hub.config.set(key, val)
        print(success(f"Config updated: {key} = {val}"))
        return 0
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skill-hub",
        description="Universal Skill and Plugin Hub for Multi-Agent AI Tools (AGY, Claude Code, ChatGPT/Codex, Kiro, etc.)",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install
    p_install = subparsers.add_parser("install", help="Install a skill or plugin from Git URL, local path, or curated catalog")
    p_install.add_argument("source", help="Git repo URL, github shorthand (user/repo), local path, or curated name")
    p_install.add_argument("--name", help="Custom name for the skill or plugin")
    p_install.add_argument("--no-sync", action="store_true", help="Do not automatically sync after installing")
    p_install.add_argument("--targets", help="Comma-separated target agents to sync (e.g. agy,claude,chatgpt,kiro)")

    # sync
    p_sync = subparsers.add_parser("sync", help="Synchronize skills and plugins to all AI tools")
    p_sync.add_argument("--targets", help="Comma-separated target agents to sync (default: all enabled)")
    p_sync.add_argument("--mode", choices=["symlink", "copy"], help="Sync mode: symlink (default) or copy")
    p_sync.add_argument("--scope", choices=["global", "project"], default="global", help="Sync scope (default: global)")
    p_sync.add_argument("--workspace", help="Workspace path when scope is project")

    # list
    p_list = subparsers.add_parser("list", help="List all installed skills and plugins in the hub")
    p_list.add_argument("--json", action="store_true", help="Output in JSON format")

    # remove / uninstall
    p_uninstall = subparsers.add_parser("uninstall", aliases=["remove", "rm"], help="Uninstall a skill or plugin")
    p_uninstall.add_argument("name", help="Name of the skill or plugin to remove")

    # import
    p_import = subparsers.add_parser("import", help="Import existing skills from AI tools into skill-hub")
    p_import.add_argument("--from-target", default="all", help="Target agent to import from (agy, claude, codex, kiro, or all)")
    p_import.add_argument("--no-sync", action="store_true", help="Do not trigger sync after import")

    # doctor
    subparsers.add_parser("doctor", aliases=["status"], help="Check AI tools detection, health, and configuration")

    # create
    p_create = subparsers.add_parser("create", help="Create a new universal skill scaffold")
    p_create.add_argument("name", help="Skill name (e.g. data-analyzer)")
    p_create.add_argument("--description", "-d", help="Skill description")

    # search
    p_search = subparsers.add_parser("search", aliases=["explore"], help="Search curated catalog of community skills and plugins")
    p_search.add_argument("query", nargs="?", default="", help="Search query (optional)")

    # config
    p_config = subparsers.add_parser("config", help="Manage skill-hub configuration")
    p_config.add_argument("action", nargs="?", choices=["show", "get", "set"], default="show")
    p_config.add_argument("key", nargs="?", help="Configuration key")
    p_config.add_argument("val", nargs="?", help="Configuration value")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    hub = Hub()

    if args.command == "install":
        return cmd_install(hub, args)
    elif args.command == "sync":
        return cmd_sync(hub, args)
    elif args.command == "list":
        return cmd_list(hub, args)
    elif args.command in ("uninstall", "remove", "rm"):
        return cmd_uninstall(hub, args)
    elif args.command == "import":
        return cmd_import(hub, args)
    elif args.command in ("doctor", "status"):
        return cmd_doctor(hub, args)
    elif args.command == "create":
        return cmd_create(hub, args)
    elif args.command in ("search", "explore"):
        return cmd_search(hub, args)
    elif args.command == "config":
        return cmd_config(hub, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
