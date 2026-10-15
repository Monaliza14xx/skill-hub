"""Terminal styling and formatted UI outputs for skill-hub."""
import sys
import os

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

# Disable color if stdout is not a TTY or NO_COLOR is set
def is_color_enabled() -> bool:
    if "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()

def style(text: str, *styles: str) -> str:
    if not is_color_enabled() or not styles:
        return text
    prefix = "".join(styles)
    return f"{prefix}{text}{Color.RESET}"

def success(text: str) -> str:
    return f"{style('✓', Color.GREEN, Color.BOLD)} {text}"

def failure(text: str) -> str:
    return f"{style('✗', Color.RED, Color.BOLD)} {text}"

def warning(text: str) -> str:
    return f"{style('⚠', Color.YELLOW, Color.BOLD)} {text}"

def info(text: str) -> str:
    return f"{style('ℹ', Color.CYAN)} {text}"

def bullet(text: str) -> str:
    return f"  {style('•', Color.GRAY)} {text}"

def highlight(text: str) -> str:
    return style(text, Color.CYAN, Color.BOLD)

def banner(title: str, subtitle: str = "") -> str:
    lines = [
        f"{style('===', Color.CYAN, Color.BOLD)} {style(title, Color.BOLD)} {style('===', Color.CYAN, Color.BOLD)}"
    ]
    if subtitle:
        lines.append(style(subtitle, Color.GRAY))
    return "\n".join(lines)

def print_table(headers: list, rows: list, alignments: list = None) -> None:
    """Print an ASCII/ANSI table cleanly aligned."""
    if not rows:
        return

    num_cols = len(headers)
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i in range(min(num_cols, len(row))):
            val_str = str(row[i])
            # calculate length without ansi codes
            clean_len = len(remove_ansi(val_str))
            if clean_len > col_widths[i]:
                col_widths[i] = clean_len

    # Header
    header_cells = []
    for i, h in enumerate(headers):
        align = alignments[i] if alignments and i < len(alignments) else "<"
        cell = f"{h:{align}{col_widths[i]}}"
        header_cells.append(style(cell, Color.BOLD, Color.UNDERLINE))
    print("  ".join(header_cells))

    # Rows
    for row in rows:
        row_cells = []
        for i in range(num_cols):
            val = str(row[i]) if i < len(row) else ""
            clean_len = len(remove_ansi(val))
            pad = col_widths[i] - clean_len
            align = alignments[i] if alignments and i < len(alignments) else "<"
            if align == ">":
                cell = (" " * pad) + val
            else:
                cell = val + (" " * pad)
            row_cells.append(cell)
        print("  ".join(row_cells))

def remove_ansi(text: str) -> str:
    """Strip ANSI escape sequences for length calculation."""
    import re
    ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_regex.sub('', text)
