"""Build the approved one-slide trajectory-check teaching page."""

from __future__ import annotations

from pathlib import Path

import build_design_slide as ppt
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
OUTPUT = PRESENTATIONS / "Trajectory_Checks_Validate_the_Path.pptx"

BG = "FFFFFF"
INK = "172033"
MUTED = "5F6B7A"
BLUE = "2563A8"
CYAN = "087EA4"
GREEN = "168653"
RED = "C83B3B"
ORANGE = "B65F00"
LINE = "D8DEE8"


def build_slide() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()

    # Header
    s.text(0.54, 0.25, 11.9, 0.40, "Trajectory Checks — Validate the Path, Not Just the Outcome", size=21, color=INK, bold=True)
    s.text(0.54, 0.70, 11.9, 0.23, "Trajectory evaluation covers the agent’s intermediate actions; execution order is one important dimension.", size=9.7, color=MUTED)
    s.line(0.54, 1.02, 12.79, 1.02, color=LINE, width=1.0)

    # Definition and best practice
    s.shape(0.54, 1.22, 7.67, 0.87, fill="F3F8FC", line="B9C9DA")
    s.shape(0.54, 1.22, 0.08, 0.87, fill="20A7D3", line="20A7D3", radius=False)
    s.text(0.77, 1.36, 1.50, 0.20, "DEFINITION", size=10.5, color=CYAN, bold=True)
    s.text(0.77, 1.62, 7.05, 0.42, "Evaluates the intermediate decisions, actions, tool use, evidence, and state\ntransitions an agent followed to reach an outcome.", size=10.8, color=INK, valign="top")

    s.shape(8.40, 1.22, 4.39, 0.87, fill="FFF7E8", line="E4B264")
    s.text(8.63, 1.36, 1.80, 0.20, "BEST PRACTICE", size=10.5, color=ORANGE, bold=True)
    s.text(8.63, 1.62, 3.80, 0.20, "Enforce business-critical dependencies.", size=10.0, color=INK)
    s.text(8.63, 1.84, 3.85, 0.19, "Allow alternative paths when exact order is unnecessary.", size=9.2, color=MUTED)

    # Breadth of trajectory evaluation
    s.text(0.54, 2.26, 4.50, 0.22, "What trajectory checks can evaluate", size=11.5, color=INK, bold=True)
    cards = [
        (0.54, "F8FAFF", "AAC3E4", BLUE, "Required steps", "Did mandatory actions occur?"),
        (2.61, "FFF8F8", "E5B0B0", RED, "Prohibited steps", "Were forbidden actions avoided?"),
        (4.68, "FFF7E8", "E4B264", ORANGE, "Order & dependencies", "Did prerequisites happen first?"),
        (6.75, "F7FCF9", "A9D8BE", GREEN, "Tool selection", "Were appropriate tools used?"),
        (8.81, "F3F8FC", "B9C9DA", CYAN, "Arguments & evidence", "Were the correct inputs used?"),
        (10.88, "F7F7FA", "C7CCD5", INK, "Efficiency", "Were calls or loops unnecessary?"),
    ]
    for x, fill, line, accent, title, question in cards:
        s.shape(x, 2.55, 1.93, 0.65, fill=fill, line=line)
        s.text(x + 0.15, 2.66, 1.65, 0.18, title, size=9.1, color=accent, bold=True)
        s.text(x + 0.15, 2.94, 1.68, 0.16, question, size=7.8, color=MUTED)

    # Sequencing scenario
    s.shape(0.54, 3.41, 12.25, 0.61, fill="F5F7FA", line="CBD3DF")
    s.text(0.73, 3.52, 2.00, 0.19, "SEQUENCING EXAMPLE", size=10.0, color=INK, bold=True)
    s.text(0.73, 3.76, 6.65, 0.18, "CUST-002  •  CARD-002  •  Expected final status: active  •  Actual final status: active", size=8.8, color=INK, font="Courier New")
    s.text(7.47, 3.76, 4.92, 0.18, "Rule: recognize transaction before approval and removal", size=9.1, color=RED, bold=True)

    # Expected path
    s.shape(0.54, 4.25, 3.71, 2.29, fill="F7FCF9", line="2F9A67")
    s.shape(0.54, 4.25, 3.71, 0.44, fill="E6F6ED", line="E6F6ED")
    s.text(0.73, 4.39, 2.90, 0.21, "EXPECTED TRAJECTORY", size=12.0, color=GREEN, bold=True)
    expected_lines = [
        ("1  authentication_success", INK, False),
        ("2  ownership_verified", INK, False),
        ("3  transaction_retrieved", INK, False),
        ("4  transaction_recognized", GREEN, True),
        ("5  eligibility_approved", INK, False),
        ("6  block_removed", INK, False),
        ("7  final_state_verified", INK, False),
    ]
    for index, (label, color, bold) in enumerate(expected_lines):
        s.text(0.76, 4.80 + index * 0.24, 3.18, 0.19, label, size=8.8, color=color, bold=bold, font="Courier New")

    # Faulty path
    s.shape(4.42, 4.25, 4.34, 2.29, fill="FFF8F8", line="CF5A5A")
    s.shape(4.42, 4.25, 4.34, 0.44, fill="FDEAEA", line="FDEAEA")
    s.text(4.61, 4.39, 3.65, 0.21, "FAULTY RECORDED TRAJECTORY", size=11.4, color=RED, bold=True)
    faulty_lines = [
        ("1  authentication_success", INK, False),
        ("2  ownership_verified", INK, False),
        ("3  transaction_retrieved", INK, False),
        ("4  eligibility_approved  ← TOO EARLY", RED, True),
        ("5  block_removed         ← TOO EARLY", RED, True),
        ("6  transaction_recognized", INK, False),
        ("7  final_state_verified", INK, False),
    ]
    s.shape(4.57, 5.50, 3.95, 0.43, fill="FFE2E2", line="FFE2E2")
    for index, (label, color, bold) in enumerate(faulty_lines):
        s.text(4.64, 4.80 + index * 0.24, 3.85, 0.19, label, size=8.5, color=color, bold=bold, font="Courier New")

    # Evaluation result
    s.shape(8.92, 4.25, 3.87, 2.29, fill="F8FAFF", line="AAC3E4")
    s.text(9.12, 4.39, 2.80, 0.21, "EVALUATION RESULT", size=11.8, color=BLUE, bold=True)
    s.line(9.12, 4.68, 12.58, 4.68, color=LINE, width=0.8)

    s.text(9.12, 4.89, 1.70, 0.19, "Outcome check", size=9.5, color=INK, bold=True)
    s.text(9.12, 5.14, 1.90, 0.18, "active == active", size=8.8, color=MUTED, font="Courier New")
    s.shape(11.72, 4.83, 0.87, 0.40, fill="E1F5E9", line="2F9A67")
    s.text(11.72, 4.93, 0.87, 0.18, "PASS", size=10.5, color=GREEN, bold=True, align="ctr")

    s.text(9.12, 5.49, 1.90, 0.19, "Sequencing check", size=9.5, color=INK, bold=True)
    s.text(9.12, 5.74, 2.28, 0.18, "recognition before approval", size=8.5, color=MUTED, font="Courier New")
    s.text(9.12, 5.95, 2.45, 0.18, "position 6 < position 4 = false", size=8.1, color=RED, font="Courier New")
    s.shape(11.72, 5.62, 0.87, 0.40, fill="FDE5E5", line="CF5A5A")
    s.text(11.72, 5.72, 0.87, 0.18, "FAIL", size=10.5, color=RED, bold=True, align="ctr")
    s.text(9.12, 6.20, 3.05, 0.19, "Overall trajectory result: FAIL", size=9.6, color=RED, bold=True)

    # Takeaway
    s.shape(0.54, 6.73, 12.25, 0.52, fill="FFF7E8", line="E58A1F")
    s.text(0.75, 6.82, 1.45, 0.18, "KEY TAKEAWAY", size=9.8, color=ORANGE, bold=True)
    s.text(0.75, 7.03, 11.70, 0.18, "A correct final state is insufficient when a protected action occurred before its required evidence was established.", size=9.9, color=INK)
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
