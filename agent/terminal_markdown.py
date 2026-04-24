from __future__ import annotations

import re


BOLD = "\033[1m"
CYAN = "\033[36m"
RESET = "\033[0m"


def render_markdown(text: str, *, enable_ansi: bool = True) -> str:
    lines = text.splitlines()
    rendered: list[str] = []
    in_code_block = False
    index = 0

    while index < len(lines):
        line = lines[index]

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            index += 1
            continue

        if in_code_block:
            rendered.append(f"    {line}")
            index += 1
            continue

        if _starts_table(lines, index):
            table_lines: list[str] = []
            table_lines.append(lines[index])
            table_lines.append(lines[index + 1])
            index += 2
            while index < len(lines) and _is_table_row(lines[index]):
                table_lines.append(lines[index])
                index += 1
            rendered.extend(_render_table(table_lines, enable_ansi=enable_ansi))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            rendered.append(_style(heading.group(2).strip(), BOLD, enable_ansi))
        else:
            rendered.append(_render_inline(line, enable_ansi=enable_ansi))
        index += 1

    return "\n".join(rendered)


def _starts_table(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and _is_table_row(lines[index])
        and _is_table_separator(lines[index + 1])
    )


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_table_separator(line: str) -> bool:
    if not _is_table_row(line):
        return False
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _render_table(lines: list[str], *, enable_ansi: bool) -> list[str]:
    headers = _split_table_row(lines[0])
    separator = _split_table_row(lines[1])
    rows = [_split_table_row(line) for line in lines[2:]]
    column_count = max(len(headers), *(len(row) for row in rows), 0)
    alignments = [_alignment(separator[index]) if index < len(separator) else "left" for index in range(column_count)]

    normalized_headers = _pad_row(headers, column_count)
    normalized_rows = [_pad_row(row, column_count) for row in rows]
    widths = [
        max(
            [_visible_len(normalized_headers[index])]
            + [_visible_len(row[index]) for row in normalized_rows]
            + [1]
        )
        for index in range(column_count)
    ]

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    output = [border]
    output.append(_format_table_row(normalized_headers, widths, ["left"] * column_count, enable_ansi=enable_ansi, header=True))
    output.append(border)
    for row in normalized_rows:
        output.append(_format_table_row(row, widths, alignments, enable_ansi=enable_ansi, header=False))
    output.append(border)
    return output


def _pad_row(row: list[str], column_count: int) -> list[str]:
    return [row[index] if index < len(row) else "" for index in range(column_count)]


def _alignment(separator_cell: str) -> str:
    stripped = separator_cell.strip()
    if stripped.startswith(":") and stripped.endswith(":"):
        return "center"
    if stripped.endswith(":"):
        return "right"
    return "left"


def _format_table_row(
    row: list[str],
    widths: list[int],
    alignments: list[str],
    *,
    enable_ansi: bool,
    header: bool,
) -> str:
    cells: list[str] = []
    for cell, width, alignment in zip(row, widths, alignments):
        plain_cell = _strip_inline_markdown(cell)
        padded = _align(plain_cell, width, alignment)
        rendered = _render_inline(padded, enable_ansi=enable_ansi)
        if header:
            rendered = _style(rendered, BOLD, enable_ansi)
        cells.append(f" {rendered} ")
    return "|" + "|".join(cells) + "|"


def _align(value: str, width: int, alignment: str) -> str:
    if alignment == "right":
        return value.rjust(width)
    if alignment == "center":
        return value.center(width)
    return value.ljust(width)


def _render_inline(text: str, *, enable_ansi: bool) -> str:
    if not enable_ansi:
        return _strip_inline_markdown(text)

    rendered = re.sub(r"`([^`]+)`", lambda match: _style(match.group(1), CYAN, True), text)
    rendered = re.sub(r"\*\*([^*]+)\*\*", lambda match: _style(match.group(1), BOLD, True), rendered)
    return rendered


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", text)


def _visible_len(text: str) -> int:
    return len(_strip_inline_markdown(text))


def _style(text: str, style: str, enable_ansi: bool) -> str:
    if not enable_ansi:
        return text
    return f"{style}{text}{RESET}"
