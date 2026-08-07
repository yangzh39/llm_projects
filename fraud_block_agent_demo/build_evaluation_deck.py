"""Build the content-focused evaluation teaching deck (six slides)."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from build_design_slide import BG, BLUE, CYAN, GREEN, LINE, MUTED, ORANGE, PANEL, PANEL_2, RED, WHITE, SlideBuilder
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
TEMPLATE = PRESENTATIONS / "Fraud_Block_Agent_Design.pptx"
OUTPUT = PRESENTATIONS / "Fraud_Block_Agent_Evaluation_Methods.pptx"
REPORT_DIR = ROOT / "evaluation" / "outputs"


def card(slide: SlideBuilder, x: float, y: float, w: float, h: float, title: str, body: str, *, accent: str = CYAN, body_size: float = 13) -> None:
    slide.shape(x, y, w, h, fill=PANEL, line=LINE)
    slide.shape(x, y, 0.08, h, fill=accent, line=accent, radius=False)
    slide.text(x + 0.25, y + 0.15, w - 0.45, 0.32, title, size=13, color=accent, bold=True)
    slide.text(x + 0.25, y + 0.56, w - 0.48, h - 0.70, body, size=body_size, color=WHITE, valign="top")


def header(slide: SlideBuilder, title: str, subtitle: str, number: str) -> None:
    slide.text(0.55, 0.30, 10.8, 0.50, title, size=24, bold=True)
    slide.text(0.55, 0.82, 11.5, 0.30, subtitle, size=10.5, color=MUTED)
    slide.shape(12.15, 0.34, 0.65, 0.44, fill=CYAN, line=CYAN)
    slide.text(12.15, 0.35, 0.65, 0.40, number, size=14, color=BG, bold=True, align="ctr")
    slide.line(0.55, 1.18, 12.80, 1.18, color=LINE, width=1)


def load_results() -> tuple[dict, dict, list[dict]]:
    live = json.loads((REPORT_DIR / "successful_block_removal_live.json").read_text())
    hidden = json.loads((REPORT_DIR / "hidden_workflow_failure.json").read_text())
    reports = []
    for path in sorted(REPORT_DIR.glob("*.json")):
        if path.name.endswith("_live.json"):
            continue
        payload = json.loads(path.read_text())
        if "scenario" in payload and "overall_result" in payload:
            reports.append(payload)
    return live, hidden, reports


def build_slides() -> list[SlideBuilder]:
    live, hidden, reports = load_results()
    valid_passes = sum(report["overall_result"] == "PASS" for report in reports)
    live_metrics = live["metrics"]
    hidden_code_pass = sum(check["status"] == "PASS" for check in hidden["code_checks"])
    hidden_trace_fail = sum(check["status"] == "FAIL" for check in hidden["trace_checks"])
    success_code_count = len(live["code_checks"])
    success_trace_count = len(live["trace_checks"])

    slides: list[SlideBuilder] = []

    # Slide 1 — title and scope.
    s = SlideBuilder()
    s.text(0.70, 0.72, 11.9, 0.70, "Evaluating an Agentic Fraud-Block System", size=29, bold=True, align="ctr")
    s.text(1.20, 1.55, 10.9, 0.40, "Educational demonstration: outcome correctness, process validity, operational cost, and reusable validation", size=13, color=MUTED, align="ctr")
    card(s, 0.75, 2.35, 2.85, 2.15, "1  DETERMINISTIC CODE CHECKS", "Did the system reach the objectively correct route, action, transfer, and final state?", accent=BLUE, body_size=14)
    card(s, 3.75, 2.35, 2.85, 2.15, "2  TRACE-BASED CHECKS", "Did required steps occur in the correct order, without prohibited behavior?", accent=ORANGE, body_size=14)
    card(s, 6.75, 2.35, 2.85, 2.15, "3  OPERATIONAL METRICS", "How many API/tool calls, tokens, dollars, clarification turns, retries, and milliseconds?", accent=GREEN, body_size=14)
    card(s, 9.75, 2.35, 2.85, 2.15, "4  VALIDATION SET", "Does the same evaluator work reproducibly across ten representative scenarios?", accent=CYAN, body_size=14)
    s.shape(1.15, 5.05, 11.05, 1.05, fill=PANEL_2, line=LINE)
    s.text(1.35, 5.20, 10.65, 0.26, "IMPLEMENTED SCOPE", size=11, color=CYAN, bold=True, align="ctr")
    s.text(1.35, 5.56, 10.65, 0.34, "10 deterministic scenarios  •  12 evaluator tests  •  1 bounded live API session  •  No LLM-as-judge  •  No human-review workflow", size=13, bold=True, align="ctr")
    s.text(1.10, 6.55, 11.10, 0.38, "Core lesson: a correct final state is necessary—but it is not sufficient evidence that an agent followed a valid process.", size=15, color=ORANGE, bold=True, align="ctr")
    slides.append(s)

    # Slide 2 — deterministic code checks.
    s = SlideBuilder()
    header(s, "Method 1 — Deterministic Code Checks", "Objective checks compare observable state and actions with scenario expectations.", "01")
    card(s, 0.55, 1.45, 3.85, 2.15, "OBJECTIVE", "Verify facts that do not require subjective judgment:\n\n• selected route and card\n• authentication and ownership\n• expected transaction\n• eligibility and removal result\n• transfer destination\n• final card status", accent=BLUE, body_size=12)
    card(s, 4.55, 1.45, 3.85, 2.15, "PROCEDURE", "1. Reset the in-memory database.\n2. Execute one agent session.\n3. Read tool outputs and final state.\n4. Compare expected versus actual.\n5. Return one structured PASS/FAIL result per assertion.", accent=BLUE, body_size=12)
    card(s, 8.55, 1.45, 4.25, 2.15, "STRUCTURED EVIDENCE", "{\n  name: final_card_status,\n  status: PASS,\n  expected: active,\n  actual: active\n}\n\nNo model is used to grade these facts.", accent=BLUE, body_size=11.5)
    card(s, 0.55, 3.90, 5.95, 1.55, "OBSERVED — LIVE SUCCESS", f"{success_code_count}/{success_code_count} required checks passed.\nRoute = BLOCK_REMOVAL; card = CARD-001; removal = true; final status = active; final state explicitly verified.", accent=GREEN, body_size=13)
    card(s, 6.70, 3.90, 6.10, 1.55, "OBSERVED — HIDDEN FAILURE", f"{hidden_code_pass}/{len(hidden['code_checks'])} code checks passed.\nThe card became active and the block-removal action completed—so outcome-only evaluation saw success.", accent=ORANGE, body_size=13)
    card(s, 0.55, 5.75, 6.05, 1.05, "HOW TO INTERPRET", "PASS means the objective outcome matches the benchmark expectation. It does not prove the workflow was valid.", accent=GREEN, body_size=12)
    card(s, 6.75, 5.75, 6.05, 1.05, "LIMITATION", "Code checks require explicit expected values and access to reliable state/tool outputs; they cannot detect an omitted step by themselves.", accent=ORANGE, body_size=12)
    slides.append(s)

    # Slide 3 — trace checks.
    s = SlideBuilder()
    header(s, "Method 2 — Trace-Based Checks", "Process evaluation is separate from final-state evaluation.", "02")
    card(s, 0.55, 1.45, 3.85, 2.25, "WHAT THE TRACE RECORDS", "Every event includes:\n\n• sequence and timestamp\n• event type and name\n• status\n• redacted input/output\n• duration\n\nCredentials and full card data are never stored.", accent=ORANGE, body_size=12)
    card(s, 4.55, 1.45, 4.10, 2.25, "REQUIRED SUCCESS ORDER", "Route selected\n→ authentication succeeds\n→ ownership verified\n→ latest transaction retrieved\n→ transaction recognized\n→ eligibility approved\n→ block removed\n→ final state verified", accent=ORANGE, body_size=12)
    card(s, 8.80, 1.45, 4.00, 2.25, "PROHIBITED BEHAVIOR", "Examples:\n\n• suspected fraud must not authenticate\n• failed auth must not disclose account data\n• unrecognized transaction must not remove block\n• removal must not precede approval", accent=ORANGE, body_size=12)
    card(s, 0.55, 4.00, 5.80, 1.40, "OBSERVED — LIVE SUCCESS", f"{success_trace_count}/{success_trace_count} trace checks passed. All required events existed and every ordering pair was valid.", accent=GREEN, body_size=13)
    card(s, 6.55, 4.00, 6.25, 1.40, "OBSERVED — HIDDEN WORKFLOW FAILURE", f"Final card = active and code checks = PASS.\nTrace failures = {hidden_trace_fail}: required newest transaction TX-002-A was not recognized; an older transaction was used instead.", accent=RED, body_size=13)
    s.shape(0.75, 5.75, 12.00, 0.78, fill="3A2025", line=RED)
    s.text(0.95, 5.88, 11.60, 0.48, "OVERALL RESULT: FAIL — the outcome looked correct, but the required workflow evidence was missing.", size=16, color=RED, bold=True, align="ctr")
    s.text(0.75, 6.76, 12.00, 0.24, "Limitation: trace checks are only as strong as the event instrumentation and the process requirements encoded by the evaluator.", size=10.5, color=MUTED, align="ctr")
    slides.append(s)

    # Slide 4 — operational metrics.
    s = SlideBuilder()
    header(s, "Method 3 — Operational Metrics and API Cost", "One authorized live session measured real DeepSeek usage; the full benchmark remained API-free.", "03")
    card(s, 0.55, 1.45, 4.00, 2.30, "METRICS CAPTURED", "• LLM calls and token usage\n• cache-hit / cache-miss input tokens\n• estimated API cost\n• tool calls\n• clarification turns and retries\n• LLM, tool, and end-to-end latency\n• specialist/non-fraud transfers", accent=GREEN, body_size=12)
    card(s, 4.75, 1.45, 4.00, 2.30, "COST METHOD", "Cost =\ncache-hit input × hit rate\n+ cache-miss input × miss rate\n+ output × output rate\n\nModel priced as: DeepSeek V4 Flash\nSource verified: 2026-08-06\nUnknown usage → cost = None", accent=GREEN, body_size=12)
    card(s, 8.95, 1.45, 3.85, 2.30, "SAFETY LIMITS", "Hard live-session cap: 10 LLM calls\nClarification threshold: 3\nTool-call threshold: 10\nLatency threshold: 15,000 ms\n\nFull benchmark + --live is rejected to prevent unexpected spending.", accent=GREEN, body_size=12)
    s.text(0.55, 4.05, 12.20, 0.28, "OBSERVED LIVE SESSION — successful_block_removal", size=13, color=CYAN, bold=True)
    metric_cards = [
        ("2", "LLM calls"),
        (f"{live_metrics['input_tokens']:,}", "input tokens"),
        (f"{live_metrics['output_tokens']:,}", "output tokens"),
        (f"{live_metrics['input_cache_hit_tokens']:,}", "cached input"),
        (f"${live_metrics['estimated_api_cost_usd']:.8f}", "estimated cost"),
        (f"{live_metrics['total_latency_ms']/1000:.2f}s", "end-to-end"),
    ]
    for index, (value, label) in enumerate(metric_cards):
        x = 0.55 + index * 2.05
        s.shape(x, 4.50, 1.85, 1.05, fill=PANEL_2, line=LINE)
        s.text(x + 0.10, 4.66, 1.65, 0.34, value, size=16, color=GREEN, bold=True, align="ctr")
        s.text(x + 0.10, 5.10, 1.65, 0.24, label, size=9.5, color=MUTED, align="ctr")
    card(s, 0.55, 5.85, 6.05, 0.95, "INTERPRETATION", "All configured thresholds passed. API cost was tiny, but latency was dominated by model calls rather than local tools.", accent=GREEN, body_size=11.5)
    card(s, 6.75, 5.85, 6.05, 0.95, "LIMITATIONS", "One live run is illustrative, not a latency distribution. Prices can change; estimates depend on returned usage metadata and current configuration.", accent=ORANGE, body_size=11.5)
    slides.append(s)

    # Slide 5 — validation set.
    s = SlideBuilder()
    header(s, "Method 4 — Benchmark / Validation-Set Execution", "The same harness resets state and evaluates ten representative sessions reproducibly.", "04")
    card(s, 0.55, 1.45, 4.00, 3.55, "TEN SCENARIOS", "1. Successful block removal\n2. Ambiguous request + clarification\n3. Suspected fraud\n4. Non-fraud transfer\n5. Incorrect-DOB auth failure\n6. Unknown-card auth failure\n7. Card/DOB mismatch\n8. Transaction not recognized\n9. Removal ineligible\n10. Hidden workflow failure", accent=CYAN, body_size=12)
    card(s, 4.75, 1.45, 3.75, 3.55, "RUNNER PIPELINE", "For every scenario:\n\n1. Load scenario and expectations\n2. Create a fresh agent/database\n3. Execute one complete session\n4. Save structured JSON trace\n5. Apply code checks\n6. Apply trace checks\n7. Calculate metrics\n8. Explain PASS or FAIL", accent=CYAN, body_size=12)
    card(s, 8.70, 1.45, 4.10, 1.55, "OBSERVED SUMMARY", f"{valid_passes}/9 expected-valid scenarios passed.\n1/1 demo-only hidden failure was correctly rejected.\nState reset was verified by automated tests.", accent=GREEN, body_size=13)
    card(s, 8.70, 3.20, 4.10, 1.80, "WHY THIS MATTERS", "A single successful conversation proves very little. A validation set tests routing, safety boundaries, negative paths, state isolation, and evaluator sensitivity using the same repeatable process.", accent=ORANGE, body_size=12)
    card(s, 0.55, 5.30, 6.05, 1.25, "COMMANDS", "All:  python3 fraud_block_agent_demo/run_evaluation.py\nOne:  ... --scenario hidden_workflow_failure\nLive: ... --scenario successful_block_removal --live", accent=CYAN, body_size=11.5)
    card(s, 6.75, 5.30, 6.05, 1.25, "LIMITATION", "Recorded model outputs make the benchmark reproducible but do not measure model-output variability. The separate bounded live run supplies real token and latency evidence.", accent=ORANGE, body_size=11.5)
    slides.append(s)

    # Slide 6 — synthesis.
    s = SlideBuilder()
    header(s, "Overall Interpretation and Teaching Sequence", "Use multiple evaluation lenses; no single method is sufficient.", "Σ")
    rows = [
        ("Deterministic code checks", "Is the observable result correct?", "Objective PASS/FAIL against expected state", BLUE),
        ("Trace-based checks", "Was the required process followed?", "Ordering, required events, prohibited behavior", ORANGE),
        ("Operational metrics", "What did the run consume?", "Calls, tokens, cost, latency, retries, transfers", GREEN),
        ("Validation set", "Does behavior generalize across cases?", "10 independent, reproducible scenarios", CYAN),
    ]
    for index, (method, question, evidence, accent) in enumerate(rows):
        y = 1.48 + index * 0.92
        s.shape(0.55, y, 12.25, 0.72, fill=PANEL, line=LINE)
        s.shape(0.55, y, 0.08, 0.72, fill=accent, line=accent, radius=False)
        s.text(0.82, y + 0.12, 3.15, 0.42, method, size=12, color=accent, bold=True)
        s.text(4.05, y + 0.12, 3.55, 0.42, question, size=11.5, bold=True)
        s.text(7.75, y + 0.12, 4.75, 0.42, evidence, size=11, color=MUTED)
    card(s, 0.55, 5.35, 5.95, 1.20, "RECOMMENDED LIVE DEMO", "1. Successful scenario: both check types pass.\n2. Hidden failure: final state passes, trace fails.\n3. Full benchmark: compare scenarios.\n4. Live metrics: explain tokens, cost, and latency.", accent=CYAN, body_size=11)
    card(s, 6.75, 5.35, 6.05, 1.20, "TAKEAWAY", "Trust requires evidence of both outcome and process. Add operational measurements and a reusable validation set to make that evidence explainable, repeatable, and cost-aware.", accent=GREEN, body_size=12)
    s.text(0.75, 6.87, 12.00, 0.24, "Scope intentionally excludes LLM-as-a-judge and human-review grading for this educational implementation.", size=10.5, color=MUTED, align="ctr")
    slides.append(s)
    return slides


def package(slides: list[SlideBuilder]) -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"PPTX template not found: {TEMPLATE}")
    with ZipFile(TEMPLATE) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}

    content_types = files["[Content_Types].xml"].decode()
    extra_overrides = "".join(
        f'<Override PartName="/ppt/slides/slide{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for index in range(2, len(slides) + 1)
    )
    content_types = content_types.replace("</Types>", extra_overrides + "</Types>")

    slide_ids = "".join(f'<p:sldId id="{255 + index}" r:id="rId{index + 1}"/>' for index in range(1, len(slides) + 1))
    presentation = files["ppt/presentation.xml"].decode()
    start = presentation.index("<p:sldIdLst>")
    end = presentation.index("</p:sldIdLst>") + len("</p:sldIdLst>")
    presentation = presentation[:start] + f"<p:sldIdLst>{slide_ids}</p:sldIdLst>" + presentation[end:]

    relationships = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    relationships.extend(
        f'<Relationship Id="rId{index + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{index}.xml"/>'
        for index in range(1, len(slides) + 1)
    )
    next_id = len(slides) + 2
    relationships.extend(
        [
            f'<Relationship Id="rId{next_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>',
            f'<Relationship Id="rId{next_id + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>',
            f'<Relationship Id="rId{next_id + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>',
        ]
    )
    presentation_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(relationships) + "</Relationships>"
    app = files["docProps/app.xml"].decode().replace("<Slides>1</Slides>", f"<Slides>{len(slides)}</Slides>")
    slide_rels = files["ppt/slides/_rels/slide1.xml.rels"]

    excluded = {
        "[Content_Types].xml",
        "ppt/presentation.xml",
        "ppt/_rels/presentation.xml.rels",
        "docProps/app.xml",
        "ppt/slides/slide1.xml",
        "ppt/slides/_rels/slide1.xml.rels",
    }
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            if name not in excluded:
                archive.writestr(name, data)
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/_rels/presentation.xml.rels", presentation_rels)
        archive.writestr("docProps/app.xml", app)
        for index, slide in enumerate(slides, start=1):
            archive.writestr(f"ppt/slides/slide{index}.xml", slide.xml())
            archive.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", slide_rels)


def main() -> None:
    ensure_artifact_dirs()
    slides = build_slides()
    package(slides)
    print(OUTPUT)


if __name__ == "__main__":
    main()
