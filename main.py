from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path


AUTH_ADMIN = "auth_admin"
AUTH_ADMIN_KEEP = "auth_admin_keep"
INPUT_FILE_NAME = "pkaction.txt"
COMPACT_OUTPUT_FILE_PREFIX = "pkaction_compact"


# Remove all whitespace from a string.
def compact_spaces(value: str) -> str:
    return "".join(value.split())


# Split pkaction output into non-empty sections.
def parse_sections(text: str) -> list[list[str]]:
    sections = []
    current_section = []

    for line in text.splitlines():
        if line.strip():
            current_section.append(line)
        elif current_section:
            sections.append(current_section)
            current_section = []

    if current_section:
        sections.append(current_section)

    return sections


# Find the implicit active value in a section.
def get_implicit_active_value(section: list[str]) -> str | None:
    for line in section:
        compact_line = compact_spaces(line)
        if compact_line == "implicitactive:auth_admin":
            return AUTH_ADMIN
        if compact_line == "implicitactive:auth_admin_keep":
            return AUTH_ADMIN_KEEP

    return None


# Extract the action ID from a section.
def get_action_id(section: list[str]) -> str:
    return section[0].strip().removesuffix(":")


# Collect sections with matching implicit active values.
def get_matching_sections(text: str) -> tuple[list[list[str]], Counter[str]]:
    matching_sections = []
    counts: Counter[str] = Counter()

    for section in parse_sections(text):
        implicit_active_value = get_implicit_active_value(section)
        if implicit_active_value is not None:
            matching_sections.append(section)
            counts[implicit_active_value] += 1

    return matching_sections, counts


# Build the detailed Polkit rules file content.
def build_rules_file(sections: list[list[str]]) -> str:
    lines = [
        "// Generated from pkaction.txt",
        "",
        "polkit.addRule(function(action, subject) {",
        "    if ((",
    ]

    for index, section in enumerate(sections):
        action_id = get_action_id(section)
        suffix = " ||" if index < len(sections) - 1 else ""
        lines.append(f'\t\t//action.id == "{action_id}"{suffix}')

        for line in section[1:]:
            if compact_spaces(line).startswith("implicitactive:") or line.lstrip().startswith("annotation:"):
                lines.append(f"//{line.lstrip()}")

    lines.extend([
        "\t\t) ",
        "\t\t&&",
        "        subject.local && ",
        "        subject.active &&",
        '        subject.isInGroup("superuser")) {',
        "        return polkit.Result.YES;",
        "    }",
        "});",
        "",
    ])

    return "\n".join(lines)


# Group and sort action IDs by implicit active value.
def get_sorted_action_ids_by_implicit_active(sections: list[list[str]]) -> dict[str, list[str]]:
    action_ids_by_implicit_active = {
        AUTH_ADMIN: [],
        AUTH_ADMIN_KEEP: [],
    }

    for section in sections:
        implicit_active_value = get_implicit_active_value(section)
        if implicit_active_value in action_ids_by_implicit_active:
            action_ids_by_implicit_active[implicit_active_value].append(get_action_id(section))

    for action_ids in action_ids_by_implicit_active.values():
        action_ids.sort()

    return action_ids_by_implicit_active


# Build the compact Polkit rules file content.
def build_compact_rules_file(sections: list[list[str]]) -> str:
    action_ids_by_implicit_active = get_sorted_action_ids_by_implicit_active(sections)
    sorted_action_ids = [
        action_id
        for implicit_active_value in (AUTH_ADMIN, AUTH_ADMIN_KEEP)
        for action_id in action_ids_by_implicit_active[implicit_active_value]
    ]

    lines = [
        "// Generated from pkaction.txt",
        "",
        "polkit.addRule(function(action, subject) {",
        "    if ((",
    ]

    action_index = 0
    for implicit_active_value in (AUTH_ADMIN, AUTH_ADMIN_KEEP):
        lines.append(f"//{implicit_active_value}")
        for action_id in action_ids_by_implicit_active[implicit_active_value]:
            action_index += 1
            suffix = " ||" if action_index < len(sorted_action_ids) else ""
            lines.append(f'\t\t//action.id == "{action_id}"{suffix}')

    lines.extend([
        "\t\t) ",
        "\t\t&&",
        "        subject.local && ",
        "        subject.active &&",
        '        subject.isInGroup("superuser")) {',
        "        return polkit.Result.YES;",
        "    }",
        "});",
        "",
    ])

    return "\n".join(lines)


# Create dated detailed and compact rules files.
def create_rules_file(script_dir: Path, today: date | None = None) -> tuple[Path, Path, Counter[str]]:
    if today is None:
        today = date.today()

    input_path = script_dir / INPUT_FILE_NAME
    output_path = script_dir / f"pkaction.{today.isoformat()}.rules"
    compact_output_path = script_dir / f"{COMPACT_OUTPUT_FILE_PREFIX}{today.isoformat()}.rules"

    text = input_path.read_text(encoding="utf-8")
    matching_sections, counts = get_matching_sections(text)
    output_path.write_text(build_rules_file(matching_sections), encoding="utf-8")
    compact_output_path.write_text(build_compact_rules_file(matching_sections), encoding="utf-8")

    return output_path, compact_output_path, counts


# Run the rules file generator and print a summary.
def main() -> None:
    script_dir = Path(__file__).resolve().parent
    output_path, compact_output_path, counts = create_rules_file(script_dir)

    print(f"Created {output_path.name}")
    print(f"Created {compact_output_path.name}")
    print(f"implicit active: {AUTH_ADMIN}: {counts[AUTH_ADMIN]}")
    print(f"implicit active: {AUTH_ADMIN_KEEP}: {counts[AUTH_ADMIN_KEEP]}")


if __name__ == "__main__":
    main()
