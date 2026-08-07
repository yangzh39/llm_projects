"""Build the two approved AI-evolution pages as fully editable PowerPoint slides."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_design_slide as ppt
from artifact_paths import PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
TEMPLATE = PRESENTATIONS / "Fraud_Block_Agent_Design.pptx"
OUTPUT = PRESENTATIONS / "AI_Product_Evolution_and_Agentic_Transition_Editable.pptx"

BG = "FFFFFF"
INK = "172033"
MUTED = "5F6B7A"
BLUE = "2563A8"
CYAN = "087EA4"
GREEN = "168653"
ORANGE = "B65F00"
PURPLE = "7651A8"
LINE = "D8DEE8"


def add_event_card(
    s: ppt.SlideBuilder,
    x: float,
    y: float,
    w: float,
    date: str,
    title: str,
    detail: str,
    accent: str,
    fill: str,
    node_x: float,
    top: bool,
) -> None:
    h = 1.20
    s.shape(x, y, w, h, fill=fill, line=accent)
    s.text(x + 0.15, y + 0.12, w - 0.30, 0.18, date, size=8.2, color=accent, bold=True)
    title_lines = title.split("\n")
    s.text(x + 0.15, y + 0.38, w - 0.30, 0.40 if len(title_lines) > 1 else 0.24, title, size=11.7 if len(title_lines) == 1 else 9.8, color=INK, bold=True, valign="top")
    detail_y = y + (0.78 if len(title_lines) > 1 else 0.69)
    s.text(x + 0.15, detail_y, w - 0.30, 0.35, detail, size=7.7, color=MUTED, valign="top")
    if top:
        s.line(node_x, y + h, node_x, 3.45, color=accent, width=1.2)
    else:
        s.line(node_x, 3.63, node_x, y, color=accent, width=1.2)
    s.circle(node_x - 0.09, 3.45, 0.18, fill=accent, line=BG)


def build_timeline() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()
    s.text(0.50, 0.23, 9.40, 0.36, "AI Product Evolution — From Conversation to Action", size=20.5, color=INK, bold=True)
    s.text(0.50, 0.66, 9.40, 0.19, "2022–2026  |  Models became multimodal and agentic as adoption expanded from individuals to institutions.", size=9.5, color=MUTED)
    s.circle(10.14, 0.70, 0.10, fill=BLUE)
    s.text(10.28, 0.66, 0.62, 0.18, "OpenAI", size=7.8, color=MUTED)
    s.circle(10.96, 0.70, 0.10, fill=PURPLE)
    s.text(11.10, 0.66, 0.72, 0.18, "Anthropic", size=7.8, color=MUTED)
    s.circle(11.92, 0.70, 0.10, fill=GREEN)
    s.text(12.06, 0.66, 0.72, 0.18, "Adoption", size=7.8, color=MUTED)
    s.line(0.50, 1.03, 12.84, 1.03, color="53C7ED", width=2.0)

    s.text(0.50, 1.28, 3.00, 0.18, "CAPABILITY MILESTONES", size=10.5, color=BLUE, bold=True)
    s.text(9.50, 1.28, 3.34, 0.18, "Curated public milestones—not an exhaustive product history", size=7.4, color=MUTED, align="r")
    s.line(0.72, 3.54, 12.65, 3.54, color="9AA7B8", width=2.8, arrow=True)

    # Opening tweet card
    s.shape(0.38, 1.65, 2.35, 1.38, fill="F3F8FC", line="AAC3E4")
    s.circle(0.50, 1.79, 0.32, fill=INK)
    s.text(0.50, 1.84, 0.32, 0.16, "SA", size=8.5, color=BG, bold=True, align="ctr")
    s.text(0.91, 1.76, 1.20, 0.18, "Sam Altman", size=8.5, color=INK, bold=True)
    s.text(0.91, 1.97, 1.55, 0.16, "@sama • Nov 30, 2022", size=7.2, color=MUTED)
    s.text(0.56, 2.25, 1.98, 0.40, "“today we launched ChatGPT.\ntry talking with it here:”", size=9.0, color=INK, bold=True, valign="top")
    s.text(0.56, 2.72, 1.80, 0.17, "The public starting point", size=7.7, color=BLUE)
    s.line(1.50, 3.03, 1.50, 3.45, color=BLUE, width=1.2)
    s.circle(1.41, 3.45, 0.18, fill=BLUE, line=BG)

    add_event_card(s, 2.50, 4.02, 1.85, "MAR 2023", "GPT-4 + Claude", "Frontier assistants:\nmultimodal + steerable", PURPLE, "F8F5FC", 3.42, False)
    add_event_card(s, 4.30, 1.74, 1.85, "MAY–NOV 2024", "Multimodal + tools", "GPT-4o • Computer Use\n• Model Context Protocol", CYAN, "F3FBFE", 5.21, True)
    add_event_card(s, 6.05, 4.02, 1.78, "FEB 2025", "Claude Code", "An agent works directly\ninside the terminal", PURPLE, "F8F5FC", 6.96, False)
    add_event_card(s, 7.79, 1.74, 1.78, "MAY 2025", "Codex", "Cloud agent edits, tests\nand proposes changes", BLUE, "F3F8FC", 8.67, True)
    add_event_card(s, 9.49, 4.02, 1.85, "JAN–JUL 2025", "Institutional AI", "ChatGPT Gov • Claude Gov\nenterprise + defense use", GREEN, "F7FCF9", 10.42, False)
    add_event_card(s, 11.15, 1.74, 1.85, "JUN–JUL 2026", "Fable / Mythos 5\nGPT-5.6 Sol", "Long-horizon, tool-rich\nfrontier systems", ORANGE, "FFF7E8", 12.08, True)

    s.text(0.50, 5.67, 1.72, 0.18, "ADOPTION EXPANDS", size=10.0, color=GREEN, bold=True)
    s.text(2.22, 5.67, 5.10, 0.18, "Each stage adds users, workflows, controls, and institutional responsibility.", size=7.6, color=MUTED)
    adoption = [
        ("PERSONAL USERS", "Everyday conversations", "E8F1FB", BLUE),
        ("BUILDERS", "Apps through APIs", "EEF4FC", BLUE),
        ("ENTERPRISES", "Secure business workflows", "F3FBFE", CYAN),
        ("AGENTIC WORK", "Delegated, multi-step tasks", "F8F5FC", PURPLE),
        ("PUBLIC SECTOR + DEFENSE", "Governed institutional deployment", "EDF9F2", GREEN),
    ]
    for i, (title, detail, fill, color) in enumerate(adoption):
        x = 0.50 + i * 2.47
        w = 2.41
        s.shape(x, 5.95, w, 0.64, fill=fill, line=BG, radius=False)
        s.text(x, 6.07, w, 0.18, title, size=8.5 if i < 4 else 7.8, color=color, bold=True, align="ctr")
        s.text(x, 6.34, w, 0.16, detail, size=7.2, color=MUTED, align="ctr")
        if i < 4:
            s.line(x + w - 0.08, 6.27, x + w + 0.10, 6.27, color=BG, width=4.0, arrow=True)

    s.shape(0.50, 6.83, 12.35, 0.42, fill=INK, line=INK)
    s.text(0.67, 6.91, 12.01, 0.20, "The trajectory is not only smarter models—it is a shift from answering questions to completing consequential work.", size=9.2, color=BG, bold=True, align="ctr")
    s.text(9.80, 7.31, 3.00, 0.12, "Dates: official OpenAI and Anthropic launch announcements.", size=5.6, color=MUTED, align="r")
    return s


def add_driver(s: ppt.SlideBuilder, x: float, number: str, title: str, detail: str, fill: str, line: str, accent: str) -> None:
    s.shape(x, 1.88, 2.36, 0.65, fill=fill, line=line)
    s.circle(x + 0.15, 2.05, 0.31, fill=line, line=line)
    s.text(x + 0.15, 2.11, 0.31, 0.15, number, size=9.2, color=accent, bold=True, align="ctr")
    s.text(x + 0.54, 2.02, 1.67, 0.17, title, size=8.9, color=INK, bold=True)
    s.text(x + 0.54, 2.28, 1.67, 0.15, detail, size=7.0, color=MUTED)


def build_transition() -> ppt.SlideBuilder:
    s = ppt.SlideBuilder()
    s.text(0.40, 0.22, 8.60, 0.52, "From ChatGPT to Codex", size=29, color=INK, bold=True)
    s.text(0.40, 0.78, 11.90, 0.24, "Scaling improves intelligence. Engineering turns intelligence into action.", size=14, color=MUTED)
    s.line(0.00, 1.31, 13.33, 1.31, color="53C7ED", width=3.0)
    s.text(0.40, 1.57, 4.20, 0.18, "WHAT MAKES THE MODEL MORE CAPABLE?", size=10.5, color=BLUE, bold=True)

    add_driver(s, 0.40, "1", "Compute & scale", "Parameters, training compute", "F3F8FC", "DCEAFB", BLUE)
    add_driver(s, 2.94, "2", "Better training data", "Quality, diversity, feedback", "F7FCF9", "E1F5E9", GREEN)
    add_driver(s, 5.49, "3", "Model architecture", "Efficiency and longer context", "FFF7E8", "FCE9C9", ORANGE)
    add_driver(s, 8.04, "4", "Post-training", "Instruction following, alignment", "F8F5FC", "EEE3F7", PURPLE)
    add_driver(s, 10.59, "5", "Inference reasoning", "More work on hard problems", "FFF5F1", "F8E4DC", "AD5C3E")

    s.text(0.40, 2.78, 5.40, 0.18, "THE UNLOCK: AUGMENT THE MODEL WITH A SYSTEM AROUND IT", size=10.3, color=BLUE, bold=True)

    # Foundation LLM
    s.shape(0.40, 3.12, 2.83, 2.52, fill="F8FAFF", line="4B79B5")
    s.shape(0.63, 3.36, 0.70, 0.55, fill="E8F1FB", line="4B79B5")
    s.line(0.78, 3.57, 1.16, 3.57, color=BLUE, width=1.7)
    s.line(0.78, 3.72, 1.08, 3.72, color=BLUE, width=1.7)
    s.text(1.51, 3.38, 1.35, 0.18, "FOUNDATION LLM", size=8.5, color=BLUE, bold=True)
    s.text(1.51, 3.66, 1.45, 0.42, "Think &\ncommunicate", size=13.8, color=INK, bold=True, valign="top")
    s.line(0.63, 4.23, 2.98, 4.23, color=LINE, width=0.8)
    for index, label in enumerate(["Understand language", "Reason over context", "Generate a response"]):
        yy = 4.49 + index * 0.34
        s.circle(0.70, yy + 0.04, 0.12, fill="4B79B5")
        s.text(0.93, yy, 1.93, 0.20, label, size=9.5, color=INK)
    s.shape(0.63, 5.38, 2.35, 0.34, fill="E8F1FB", line="E8F1FB")
    s.text(0.63, 5.45, 2.35, 0.17, "OUTPUT: WORDS", size=9.1, color=BLUE, bold=True, align="ctr")

    # Plus
    s.circle(3.34, 4.18, 0.42, fill=BG, line="53C7ED")
    s.text(3.34, 4.20, 0.42, 0.31, "+", size=22, color=CYAN, bold=True, align="ctr")

    # Augmentation layer
    s.shape(3.88, 3.12, 4.92, 2.52, fill="F3FBFE", line="20A7D3")
    s.text(4.12, 3.33, 1.75, 0.18, "AUGMENTATION LAYER", size=8.5, color=CYAN, bold=True)
    s.text(4.12, 3.61, 4.30, 0.26, "Give the model context and capabilities", size=14.0, color=INK, bold=True)
    aug = [
        (4.12, 3.98, "Context & memory", "Relevant knowledge and state", "AAC3E4", BLUE, "+"),
        (6.42, 3.98, "Tools & APIs", "Search, calculate, transact", "A9D8BE", GREEN, "+"),
        (4.12, 4.76, "Runtime & terminal", "Execute code and commands", "E4B264", ORANGE, ">_"),
        (6.42, 4.76, "Orchestration", "Planning, controls, guardrails", "C7AFE0", PURPLE, "✓"),
    ]
    for x, y, title, detail, border, color, icon in aug:
        s.shape(x, y, 2.15, 0.62, fill=BG, line=border)
        s.circle(x + 0.15, y + 0.17, 0.29, fill="F1F5F9", line="F1F5F9")
        s.text(x + 0.15, y + 0.22, 0.29, 0.14, icon, size=10.5, color=color, bold=True, align="ctr")
        s.text(x + 0.53, y + 0.13, 1.47, 0.17, title, size=8.5, color=color, bold=True)
        s.text(x + 0.53, y + 0.37, 1.52, 0.15, detail, size=6.9, color=MUTED)

    s.line(8.82, 4.38, 9.32, 4.38, color=GREEN, width=2.5, arrow=True)

    # Agentic system
    s.shape(9.50, 3.12, 3.43, 2.52, fill="F7FCF9", line="2F9A67")
    s.text(9.75, 3.33, 1.70, 0.18, "AGENTIC AI SYSTEM", size=8.5, color=GREEN, bold=True)
    s.text(9.75, 3.61, 2.70, 0.26, "Reason, act, and adapt", size=14.0, color=INK, bold=True)
    s.circle(10.78, 4.12, 1.42, fill=BG, line="A9D8BE")
    s.circle(11.23, 4.55, 0.55, fill="E1F5E9", line="E1F5E9")
    s.text(11.23, 4.67, 0.55, 0.15, "GOAL", size=7.8, color=GREEN, bold=True, align="ctr")
    s.text(11.23, 4.84, 0.55, 0.13, "completion", size=6.2, color=INK, align="ctr")
    labels = [
        (10.95, 4.02, 0.85, "UNDERSTAND", BLUE),
        (11.93, 4.57, 0.50, "PLAN", ORANGE),
        (11.02, 5.28, 0.47, "ACT", GREEN),
        (10.08, 4.57, 0.64, "OBSERVE", PURPLE),
    ]
    for x, y, w, label, color in labels:
        s.shape(x, y, w, 0.25, fill="F4F7FA", line="F4F7FA")
        s.text(x, y + 0.05, w, 0.13, label, size=6.7, color=color, bold=True, align="ctr")
    s.line(11.78, 4.16, 12.16, 4.55, color="7F8EA3", width=1.1, arrow=True)
    s.line(12.15, 4.83, 11.56, 5.30, color="7F8EA3", width=1.1, arrow=True)
    s.line(10.98, 5.30, 10.40, 4.84, color="7F8EA3", width=1.1, arrow=True)
    s.line(10.40, 4.55, 10.92, 4.16, color="7F8EA3", width=1.1, arrow=True)

    # Takeaway
    s.shape(0.40, 6.10, 12.53, 0.95, fill=INK, line=INK)
    s.text(0.66, 6.31, 1.30, 0.17, "THE TRANSITION", size=8.4, color="53C7ED", bold=True)
    s.text(0.66, 6.58, 5.85, 0.23, "Model intelligence determines what AI can reason about.", size=13.5, color=BG, bold=True)
    s.text(7.05, 6.58, 5.40, 0.23, "Tools + runtime determine what it can do.", size=13.5, color="53D89A", bold=True)
    s.text(0.66, 6.84, 11.80, 0.15, "This is the bridge from conversational AI to systems that can complete work across software, devices, and real-world workflows.", size=7.4, color="A8B4C7")
    return s


def white_xml(slide: ppt.SlideBuilder) -> str:
    return slide.xml().replace(
        f'<a:srgbClr val="{ppt.BG}"/>',
        f'<a:srgbClr val="{BG}"/>',
        1,
    )


def package_two_slides(slide_xmls: list[str], output: Path) -> None:
    with ZipFile(TEMPLATE) as source:
        files = {name: source.read(name) for name in source.namelist()}

    content_types = files["[Content_Types].xml"].decode("utf-8")
    if 'PartName="/ppt/slides/slide2.xml"' not in content_types:
        content_types = content_types.replace(
            "</Types>",
            '<Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>',
        )
    files["[Content_Types].xml"] = content_types.encode("utf-8")

    presentation = files["ppt/presentation.xml"].decode("utf-8").replace(
        '<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>',
        '<p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId6"/></p:sldIdLst>',
    )
    files["ppt/presentation.xml"] = presentation.encode("utf-8")

    rels = files["ppt/_rels/presentation.xml.rels"].decode("utf-8").replace(
        "</Relationships>",
        '<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/></Relationships>',
    )
    files["ppt/_rels/presentation.xml.rels"] = rels.encode("utf-8")

    slide_rel = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
    for index, xml in enumerate(slide_xmls, start=1):
        files[f"ppt/slides/slide{index}.xml"] = xml.encode("utf-8")
        files[f"ppt/slides/_rels/slide{index}.xml.rels"] = slide_rel

    with ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)


def main() -> None:
    ensure_artifact_dirs()
    package_two_slides([white_xml(build_timeline()), white_xml(build_transition())], OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
