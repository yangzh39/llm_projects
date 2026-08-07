"""Build the approved one-slide unit-test versus code-check comparison."""

from __future__ import annotations

from pathlib import Path

import build_design_slide as ppt
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
OUTPUT = PRESENTATIONS / "Authentication_Evaluation_Unit_Test_vs_Code_Check.pptx"

BG = "FFFFFF"
INK = "172033"
MUTED = "5F6B7A"
CYAN = "087EA4"
BLUE = "2563A8"
GREEN = "168653"
ORANGE = "B65F00"
LINE = "D8DEE8"
SCENARIO_FILL = "F3F8FC"
SCENARIO_LINE = "B9C9DA"
UNIT_FILL = "F8FAFF"
UNIT_HEADER = "E8F1FB"
UNIT_LINE = "4B79B5"
CHECK_FILL = "F7FCF9"
CHECK_HEADER = "E6F6ED"
CHECK_LINE = "2F9A67"
CODE_BG = "0C1017"
CODE_LINE = "293348"
CODE_TEXT = "F5F7FA"
CODE_COMMENT = "8390A5"
CODE_PURPLE = "C792EA"
CODE_GREEN = "C3E88D"
CODE_BLUE = "82AAFF"
TAKEAWAY_FILL = "FFF7E8"
TAKEAWAY_LINE = "E58A1F"


def label_value(
    slide: ppt.SlideBuilder,
    x: float,
    y: float,
    label: str,
    value: str,
    *,
    value_color: str = INK,
) -> None:
    label_width = max(0.72, len(label) * 0.075)
    slide.text(x, y, label_width, 0.25, label, size=10.3, color=INK, bold=True, font="Courier New")
    slide.text(x + label_width, y, 2.40, 0.25, value, size=10.3, color=value_color, bold=True, font="Courier New")


def code_line(
    slide: ppt.SlideBuilder,
    x: float,
    y: float,
    width: float,
    value: str,
    *,
    color: str = CODE_TEXT,
    size: float = 8.6,
    bold: bool = False,
) -> None:
    slide.text(x, y, width, 0.22, value, size=size, color=color, bold=bold, font="Courier New", valign="top")


def build_slide() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()

    # Header
    s.text(0.54, 0.25, 11.7, 0.42, "Authentication Evaluation — Unit Test vs. Deterministic Code Check", size=21, color=INK, bold=True)
    s.text(0.54, 0.70, 11.8, 0.24, "The same fictional customer and expected outcome are examined at two different levels of the system.", size=9.7, color=MUTED)
    s.line(0.54, 1.02, 12.79, 1.02, color=LINE, width=1.0)

    # Shared scenario
    s.shape(0.54, 1.23, 12.25, 0.88, fill=SCENARIO_FILL, line=SCENARIO_LINE)
    s.shape(0.54, 1.23, 0.08, 0.88, fill="20A7D3", line="20A7D3", radius=False)
    s.text(0.77, 1.35, 2.2, 0.22, "SHARED SCENARIO", size=10.5, color=CYAN, bold=True)
    s.text(0.77, 1.70, 2.85, 0.25, "Card number: 4111111111111111", size=9.5, color=INK, bold=True, font="Courier New")
    s.text(3.87, 1.70, 1.75, 0.25, "DOB: 1990-01-15", size=9.5, color=INK, bold=True, font="Courier New")
    s.text(6.15, 1.70, 2.55, 0.25, "Expected customer: CUST-001", size=9.5, color=INK, bold=True, font="Courier New")
    s.text(9.33, 1.70, 3.10, 0.25, "Expected: Authentication succeeds", size=10.3, color=GREEN, bold=True, font="Courier New")

    # Unit-test panel
    s.shape(0.54, 2.34, 5.50, 4.06, fill=UNIT_FILL, line=UNIT_LINE)
    s.shape(0.54, 2.34, 5.50, 0.53, fill=UNIT_HEADER, line=UNIT_HEADER)
    s.text(0.77, 2.47, 1.30, 0.25, "UNIT TEST", size=15, color=BLUE, bold=True)
    s.text(2.22, 2.50, 1.65, 0.20, "Isolated component", size=9.2, color=MUTED)
    s.shape(0.73, 3.04, 5.12, 2.65, fill=CODE_BG, line=CODE_LINE)

    left_lines = [
        ("def test_authentication_with_valid_credentials():", CODE_PURPLE, True),
        ("", CODE_TEXT, False),
        ("    result = authenticate_customer(", CODE_TEXT, True),
        ('        card_number="4111111111111111",', CODE_GREEN, True),
        ('        date_of_birth="1990-01-15",', CODE_GREEN, True),
        ("    )", CODE_TEXT, True),
        ("", CODE_TEXT, False),
        ('    assert result["success"] is True', CODE_PURPLE, True),
        ('    assert result["customer_id"] == "CUST-001"', CODE_PURPLE, True),
        ('    assert result["card_id"] == "CARD-001"', CODE_PURPLE, True),
    ]
    for index, (line, color, bold) in enumerate(left_lines):
        code_line(s, 0.92, 3.20 + index * 0.245, 4.72, line, color=color, size=9.0, bold=bold)

    s.text(0.77, 5.83, 1.30, 0.22, "Evidence source:", size=9.7, color=INK, bold=True)
    s.text(2.05, 5.83, 2.65, 0.22, "direct function return", size=9.7, color=MUTED)
    s.text(0.77, 6.10, 0.62, 0.22, "Proves:", size=9.7, color=INK, bold=True)
    s.text(1.38, 6.10, 4.30, 0.22, "the authentication function works when called correctly", size=9.2, color=MUTED)

    # Deterministic code-check panel
    s.shape(6.25, 2.34, 6.54, 4.06, fill=CHECK_FILL, line=CHECK_LINE)
    s.shape(6.25, 2.34, 6.54, 0.53, fill=CHECK_HEADER, line=CHECK_HEADER)
    s.text(6.48, 2.47, 3.35, 0.25, "DETERMINISTIC CODE CHECK", size=14.2, color=GREEN, bold=True)
    s.text(9.73, 2.50, 2.05, 0.20, "Complete agent session", size=9.2, color=MUTED)
    s.shape(6.44, 3.04, 6.16, 2.65, fill=CODE_BG, line=CODE_LINE)

    right_lines = [
        ("# Run the complete customer scenario", CODE_COMMENT, False),
        ("trace = run_agent_scenario(successful_block_removal)", CODE_TEXT, True),
        ("", CODE_TEXT, False),
        ('expected = {"authentication_succeeded": True,', CODE_GREEN, True),
        ('            "customer_id": "CUST-001", "card_id": "CARD-001"}', CODE_GREEN, True),
        ("", CODE_TEXT, False),
        ('actual = {"authentication_succeeded": trace.authentication_succeeded,', CODE_TEXT, True),
        ('          "customer_id": trace.authenticated_customer_id,', CODE_TEXT, True),
        ('          "card_id": trace.selected_card_id}', CODE_TEXT, True),
        ("", CODE_TEXT, False),
        ("assert actual == expected", CODE_PURPLE, True),
        ("# PASS only when every extracted value matches", CODE_COMMENT, False),
    ]
    for index, (line, color, bold) in enumerate(right_lines):
        code_line(s, 6.61, 3.16 + index * 0.205, 5.77, line, color=color, size=7.9, bold=bold)

    s.text(6.48, 5.83, 1.30, 0.22, "Evidence source:", size=9.7, color=INK, bold=True)
    s.text(7.76, 5.83, 3.80, 0.22, "structured trace from the complete run", size=9.7, color=MUTED)
    s.text(6.48, 6.10, 0.62, 0.22, "Proves:", size=9.7, color=INK, bold=True)
    s.text(7.09, 6.10, 5.30, 0.22, "the workflow reached authentication and produced the expected result", size=9.2, color=MUTED)

    # Key takeaway
    s.shape(0.54, 6.63, 12.25, 0.59, fill=TAKEAWAY_FILL, line=TAKEAWAY_LINE)
    s.text(0.76, 6.75, 1.50, 0.20, "KEY DIFFERENCE", size=10.2, color=ORANGE, bold=True)
    s.text(0.76, 6.98, 11.75, 0.20, "A unit test validates the component directly; a code check validates that the complete agent reached and used that component correctly.", size=10.4, color=INK)
    return s


def main() -> None:
    ensure_artifact_dirs()
    slide = build_slide()
    slide_xml = slide.xml().replace(
        f'<a:srgbClr val="{ppt.BG}"/>',
        f'<a:srgbClr val="{BG}"/>',
        1,
    )
    ppt.PPTX_PATH = OUTPUT
    ppt.package_pptx(slide_xml)
    print(OUTPUT)


if __name__ == "__main__":
    main()
