"""Build the approved one-slide benchmark/validation-set teaching page."""

from __future__ import annotations

from pathlib import Path

import build_design_slide as ppt
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
OUTPUT = PRESENTATIONS / "Benchmark_Validation_Set_Version_Comparison.pptx"

BG = "FFFFFF"
INK = "172033"
MUTED = "5F6B7A"
BLUE = "2563A8"
CYAN = "087EA4"
GREEN = "168653"
ORANGE = "B65F00"
RED = "C83B3B"
LINE = "D8DEE8"


def add_table(
    s: ppt.SlideBuilder,
    x: float,
    title: str,
    accent: str,
    title_fill: str,
    left_header: str,
    right_header: str,
    rows: list[tuple[str, str, str, str]],
) -> None:
    """Add one compact, editable comparison table."""
    s.shape(x, 5.12, 6.00, 1.86, fill=BG, line=accent)
    s.shape(x, 5.12, 6.00, 0.32, fill=title_fill, line=title_fill)
    s.text(x + 0.18, 5.18, 5.64, 0.18, title, size=9.6, color=accent, bold=True)

    s.text(x + 0.18, 5.51, 2.65, 0.17, "Result", size=7.8, color=INK, bold=True)
    s.text(x + 3.12, 5.51, 1.45, 0.17, left_header, size=7.8, color=INK, bold=True, align="ctr")
    s.text(x + 4.72, 5.51, 1.08, 0.17, right_header, size=7.8, color=accent, bold=True, align="ctr")
    s.line(x + 0.18, 5.72, x + 5.82, 5.72, color=LINE, width=0.7)

    for index, (label, left, right, right_color) in enumerate(rows):
        yy = 5.79 + index * 0.175
        bold = label == "Decision"
        s.text(x + 0.18, yy, 2.70, 0.14, label, size=7.25, color=INK, bold=bold)
        s.text(x + 3.12, yy, 1.45, 0.14, left, size=7.25, color=MUTED, align="ctr")
        s.text(x + 4.58, yy, 1.38, 0.14, right, size=7.10, color=right_color, bold=bold, align="ctr")


def build_slide() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()

    # Header and definition
    s.text(0.54, 0.24, 12.25, 0.36, "Benchmark / Validation Set — Measure Change Across Versions", size=20.5, color=INK, bold=True)
    s.text(0.54, 0.63, 12.25, 0.21, "Fixed scenarios make agent behavior comparable across code, prompt, and model changes.", size=9.7, color=MUTED)
    s.line(0.54, 1.01, 12.79, 1.01, color=LINE, width=1.0)

    s.shape(0.54, 1.22, 12.25, 0.68, fill="F3F8FC", line="B9C9DA")
    s.shape(0.54, 1.22, 0.08, 0.68, fill="20A7D3", line="20A7D3", radius=False)
    s.text(0.78, 1.38, 1.25, 0.18, "DEFINITION", size=10.2, color=CYAN, bold=True)
    s.text(0.78, 1.63, 11.55, 0.18, "A benchmark contains representative scenarios and expected behaviors used to measure how agent performance changes across versions.", size=10.1, color=INK)

    # Execution-mode tree
    s.text(0.54, 2.09, 6.90, 0.20, "TWO EXECUTION MODES — ONE REUSABLE BENCHMARK", size=10.8, color=BLUE, bold=True)
    s.shape(2.04, 2.35, 4.17, 0.48, fill="E8F1FB", line="4B79B5")
    s.text(2.04, 2.42, 4.17, 0.18, "BENCHMARK / VALIDATION SET", size=10.4, color=BLUE, bold=True, align="ctr")
    s.text(2.04, 2.63, 4.17, 0.15, "Scenarios + expected behavior", size=8.1, color=MUTED, align="ctr")

    s.line(4.13, 2.83, 4.13, 3.01, color="7F8EA3", width=1.1)
    s.line(2.20, 3.01, 6.05, 3.01, color="7F8EA3", width=1.1)
    s.line(2.20, 3.01, 2.20, 3.13, color="7F8EA3", width=1.1)
    s.line(6.05, 3.01, 6.05, 3.13, color="7F8EA3", width=1.1)

    s.shape(0.54, 3.13, 3.32, 0.87, fill="F7FCF9", line="2F9A67")
    s.text(0.54, 3.28, 3.32, 0.18, "OFFLINE DETERMINISTIC RUN", size=10.0, color=GREEN, bold=True, align="ctr")
    s.text(0.54, 3.52, 3.32, 0.16, "Recorded model outputs", size=8.5, color=INK, align="ctr")
    s.text(0.70, 3.77, 3.00, 0.16, "Tests orchestration, tools, controls, state, and graders", size=7.5, color=MUTED, align="ctr")

    s.shape(4.39, 3.13, 3.32, 0.87, fill="FFF7E8", line="E4B264")
    s.text(4.39, 3.28, 3.32, 0.18, "LIVE MODEL RUN", size=10.0, color=ORANGE, bold=True, align="ctr")
    s.text(4.39, 3.52, 3.32, 0.16, "Current prompt + model API", size=8.5, color=INK, align="ctr")
    s.text(4.55, 3.77, 3.00, 0.16, "Tests interpretation, prompt quality, and integration", size=7.5, color=MUTED, align="ctr")

    s.line(2.20, 4.00, 2.20, 4.15, color="7F8EA3", width=1.1)
    s.line(6.05, 4.00, 6.05, 4.15, color="7F8EA3", width=1.1)
    s.line(2.20, 4.15, 6.05, 4.15, color="7F8EA3", width=1.1)
    s.line(4.13, 4.15, 4.13, 4.27, color="7F8EA3", width=1.1)
    s.shape(2.04, 4.27, 4.17, 0.40, fill="F5F7FA", line="AEB8C8")
    s.text(2.04, 4.36, 4.17, 0.18, "HYBRID EVALUATION REPORT", size=10.2, color=INK, bold=True, align="ctr")

    # Report content card
    s.shape(8.13, 2.35, 4.66, 2.32, fill="F8FAFF", line="AAC3E4")
    s.text(8.34, 2.55, 4.10, 0.20, "EACH BENCHMARK RUN REPORTS", size=11.0, color=BLUE, bold=True)
    report_rows = [
        ("Outcome / code checks", "Expected business result", "EEF4FC", BLUE),
        ("Trajectory checks", "Required steps and dependencies", "FFF7E8", ORANGE),
        ("Safety checks", "Prohibited actions avoided", "FFF1F1", RED),
        ("Operational metrics", "Calls, tokens, cost, and latency", "EDF9F2", GREEN),
    ]
    for index, (label, detail, fill, color) in enumerate(report_rows):
        yy = 2.82 + index * 0.43
        s.shape(8.34, yy, 4.25, 0.35, fill=fill, line=fill)
        s.text(8.49, yy + 0.07, 1.70, 0.17, label, size=8.5, color=color, bold=True)
        s.text(10.09, yy + 0.07, 2.35, 0.17, detail, size=7.8, color=MUTED)

    # Illustrative comparison tables
    s.text(0.54, 4.82, 3.55, 0.18, "ILLUSTRATIVE VERSION COMPARISONS", size=10.5, color=INK, bold=True)
    s.text(4.21, 4.82, 4.10, 0.18, "Example values—not measured project results", size=7.9, color=MUTED)

    add_table(
        s,
        0.54,
        "MODEL UPGRADE — HIGHER QUALITY, HIGHER COST",
        GREEN,
        "E6F6ED",
        "Current model",
        "Advanced model",
        [
            ("Scenarios passed", "8/10", "9/10", GREEN),
            ("Correct routing / trajectory", "90% / 80%", "100% / 90%", GREEN),
            ("Structured output", "100%", "100%", GREEN),
            ("Average API calls", "2.4", "3.1", ORANGE),
            ("Cost / latency", "$0.028 / 2.9s", "$0.052 / 4.2s", ORANGE),
            ("Decision", "Baseline", "Weigh quality vs. cost", GREEN),
        ],
    )
    add_table(
        s,
        6.79,
        "PROMPT CHANGE — REGRESSION REQUIRES INVESTIGATION",
        RED,
        "FDEAEA",
        "Prompt v1",
        "Prompt v2",
        [
            ("Scenarios passed", "9/10", "7/10", RED),
            ("Correct routing / trajectory", "100% / 90%", "80% / 70%", RED),
            ("Structured output", "100%", "90%", RED),
            ("Average API calls", "2.6", "3.4", RED),
            ("Cost / latency", "$0.030 / 3.2s", "$0.039 / 4.6s", RED),
            ("Decision", "Current version", "Investigate — do not release", RED),
        ],
    )

    s.shape(0.54, 7.10, 12.25, 0.27, fill="FFF7E8", line="E58A1F")
    s.text(0.75, 7.14, 11.83, 0.17, "Benchmarking makes change measurable: compare quality, safety, cost, and latency before deciding whether to release.", size=8.7, color=INK, align="ctr")
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
