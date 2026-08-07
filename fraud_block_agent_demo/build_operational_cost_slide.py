"""Build the approved one-slide operational-cost and business-value page."""

from __future__ import annotations

from pathlib import Path

import build_design_slide as ppt
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
OUTPUT = PRESENTATIONS / "Operational_Metrics_API_Cost_and_Business_Value.pptx"

BG = "FFFFFF"
INK = "172033"
MUTED = "5F6B7A"
BLUE = "2563A8"
CYAN = "087EA4"
GREEN = "168653"
ORANGE = "B65F00"
RED = "C83B3B"
LINE = "D8DEE8"


def metric_row(
    slide: ppt.SlideBuilder,
    y: float,
    label: str,
    description: str,
    color: str,
) -> None:
    slide.text(8.33, y, 1.67, 0.18, label, size=8.0, color=color, bold=True)
    slide.text(10.00, y, 2.45, 0.18, description, size=7.6, color=MUTED)


def build_slide() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()

    # Header
    s.text(0.54, 0.24, 10.90, 0.40, "Operational Metrics — API Cost and Business Value", size=21, color=INK, bold=True)
    s.text(0.54, 0.70, 12.10, 0.23, "Estimate direct model expense, then monitor whether that spending produces safe and contained customer outcomes.", size=9.6, color=MUTED)
    s.line(0.54, 1.02, 12.79, 1.02, color=LINE, width=1.0)

    # Definition and business lens
    s.shape(0.54, 1.22, 7.50, 0.82, fill="F3F8FC", line="B9C9DA")
    s.shape(0.54, 1.22, 0.08, 0.82, fill="20A7D3", line="20A7D3", radius=False)
    s.text(0.77, 1.36, 1.40, 0.20, "DEFINITION", size=10.2, color=CYAN, bold=True)
    s.text(0.77, 1.62, 6.80, 0.19, "API cost is the direct model-inference expense attributed to serving a session.", size=10.4, color=INK)
    s.text(0.77, 1.84, 6.80, 0.17, "It is one operational metric—not the system’s total cost of ownership.", size=8.9, color=MUTED)

    s.shape(8.23, 1.22, 4.56, 0.82, fill="FFF7E8", line="E4B264")
    s.text(8.47, 1.36, 1.60, 0.20, "BUSINESS LENS", size=10.2, color=ORANGE, bold=True)
    s.text(8.47, 1.62, 3.90, 0.19, "Measure cost per successful, safe resolution.", size=10.2, color=INK)
    s.text(8.47, 1.84, 3.90, 0.17, "Low API spend has value only when the workflow contains the call.", size=8.8, color=MUTED)

    # Column headings
    s.text(0.54, 2.20, 4.60, 0.24, "ANNUAL API-COST FUNNEL", size=12.4, color=BLUE, bold=True)
    s.text(8.33, 2.20, 4.25, 0.24, "OTHER OPERATIONAL METRICS", size=12.4, color=GREEN, bold=True)

    # Annual workload
    s.shape(0.54, 2.52, 7.29, 0.52, fill="E8F1FB", line="4B79B5")
    s.text(0.76, 2.63, 4.40, 0.18, "500,000 annual connected customer calls", size=10.2, color=BLUE, bold=True)
    s.text(0.76, 2.84, 4.40, 0.16, "Annual workload entering the fraud-block agent", size=8.2, color=MUTED)

    # Split connector
    s.line(4.18, 3.04, 4.18, 3.21, color="7F8EA3", width=1.1)
    s.line(2.32, 3.21, 6.07, 3.21, color="7F8EA3", width=1.1)
    s.line(2.32, 3.21, 2.32, 3.33, color="7F8EA3", width=1.1)
    s.line(6.07, 3.21, 6.07, 3.33, color="7F8EA3", width=1.1)

    # Successful and unsuccessful branches
    s.shape(0.54, 3.33, 3.54, 0.85, fill="F7FCF9", line="2F9A67")
    s.text(0.73, 3.47, 3.10, 0.19, "60% successful block removal", size=10.2, color=GREEN, bold=True)
    s.text(0.73, 3.74, 3.10, 0.18, "300,000 sessions × 6 calls", size=9.2, color=INK, font="Courier New")
    s.text(0.73, 4.00, 3.10, 0.18, "= 1,800,000 API calls", size=9.7, color=GREEN, bold=True, font="Courier New")

    s.shape(4.29, 3.33, 3.54, 0.85, fill="FFF8F8", line="CF7A7A")
    s.text(4.48, 3.47, 3.10, 0.19, "40% unsuccessful sessions", size=10.2, color=RED, bold=True)
    s.text(4.48, 3.74, 3.10, 0.18, "200,000 sessions × 5 calls", size=9.2, color=INK, font="Courier New")
    s.text(4.48, 4.00, 3.10, 0.18, "= 1,000,000 API calls", size=9.7, color=RED, bold=True, font="Courier New")

    # Merge connector
    s.line(2.32, 4.18, 2.32, 4.33, color="7F8EA3", width=1.1)
    s.line(6.07, 4.18, 6.07, 4.33, color="7F8EA3", width=1.1)
    s.line(2.32, 4.33, 6.07, 4.33, color="7F8EA3", width=1.1)
    s.line(4.18, 4.33, 4.18, 4.46, color="7F8EA3", width=1.1)

    # Token and price calculation
    s.shape(0.54, 4.46, 7.29, 0.68, fill="F5F7FA", line="CBD3DF")
    s.text(0.73, 4.58, 3.95, 0.18, "2,800,000 annual Claude Fable 5 API calls", size=9.8, color=INK, bold=True)
    s.text(0.73, 4.82, 4.00, 0.18, "Per-call proxy: 619.5 input + 106.5 output tokens", size=8.1, color=MUTED, font="Courier New")
    s.text(5.04, 4.58, 2.55, 0.18, "1.7346B input × $10/MTok = $17,346", size=7.7, color=INK, font="Courier New")
    s.text(5.04, 4.82, 2.55, 0.18, "298.2M output × $50/MTok = $14,910", size=7.7, color=INK, font="Courier New")

    # KPI cards
    kpis = [
        (0.54, 2.29, "F3F8FC", "AAC3E4", BLUE, "ANNUAL MODEL API COST", "$32,256", "Successful + unsuccessful traffic"),
        (2.98, 2.29, "F7FCF9", "A9D8BE", GREEN, "NET MODEL-ONLY SAVINGS", "$4.17M", "$4.20M avoided human cost − API"),
        (5.41, 2.42, "FFF7E8", "E4B264", ORANGE, "DIRECT COST ADVANTAGE", "~130×", "$4.20M ÷ $32,256"),
    ]
    for x, width, fill, line, accent, heading, value, note in kpis:
        s.shape(x, 5.31, width, 0.97, fill=fill, line=line)
        s.text(x + 0.15, 5.43, width - 0.30, 0.17, heading, size=8.4, color=accent, bold=True)
        s.text(x + 0.15, 5.71, width - 0.30, 0.28, value, size=18.5, color=accent if accent != BLUE else INK, bold=True)
        s.text(x + 0.15, 6.08, width - 0.30, 0.14, note, size=7.1, color=MUTED)

    # Other operational metrics panel
    s.shape(8.13, 2.52, 4.66, 3.76, fill="F8FAFF", line="AAC3E4")
    s.text(8.33, 2.69, 2.00, 0.19, "Customer outcome", size=9.7, color=INK, bold=True)
    metric_row(s, 2.96, "Containment rate", "Resolved without human transfer", GREEN)
    metric_row(s, 3.19, "Successful removal rate", "Safe automated blocks removed", BLUE)
    metric_row(s, 3.42, "Drop rate", "Customers leaving before resolution", RED)

    s.line(8.33, 3.70, 12.58, 3.70, color=LINE, width=0.7)
    s.text(8.33, 3.86, 2.20, 0.19, "Routing and escalation", size=9.7, color=INK, bold=True)
    metric_row(s, 4.13, "Fraud transfer rate", "Suspected fraud sent to specialist", ORANGE)
    metric_row(s, 4.36, "Non-fraud transfer rate", "Wrong-department demand", BLUE)
    metric_row(s, 4.59, "Authentication failure", "Failed or suspicious verification", RED)

    s.line(8.33, 4.87, 12.58, 4.87, color=LINE, width=0.7)
    s.text(8.33, 5.03, 3.30, 0.19, "Efficiency, reliability, and safety", size=9.7, color=INK, bold=True)
    metric_row(s, 5.30, "Calls / tokens / cost", "Per session and successful outcome", CYAN)
    metric_row(s, 5.53, "p50 / p95 latency", "Typical and slow customer experience", BLUE)
    metric_row(s, 5.76, "Clarification / retries", "Loops, parsing, and tool instability", ORANGE)
    metric_row(s, 5.99, "Safety violations", "Protected actions without evidence", RED)

    # Assumptions and pricing source
    s.shape(0.54, 6.48, 12.25, 0.77, fill="FAFBFC", line=LINE)
    s.text(0.69, 6.59, 2.10, 0.17, "ASSUMPTIONS AND SOURCE", size=8.1, color=INK, bold=True)
    s.text(0.69, 6.82, 7.30, 0.16, "500,000 annual calls; 60% successful at 6 API calls; 40% unsuccessful at 5; $14 avoided human handling per successful call.", size=6.9, color=MUTED)
    s.text(0.69, 7.03, 7.40, 0.16, "Token proxy comes from one measured DeepSeek session. Excludes telephony, infrastructure, monitoring, maintenance, and human escalation costs.", size=6.9, color=MUTED)
    s.text(8.35, 6.82, 4.10, 0.16, "Claude Fable 5: $10/MTok input; $50/MTok output.", size=7.0, color=BLUE)
    s.text(8.35, 7.03, 4.10, 0.16, "Source: anthropic.com/news/claude-fable-5-mythos-5", size=7.0, color=BLUE)
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
