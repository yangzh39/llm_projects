"""Render deterministic, captioned frames for the Fraud Block Agent demo video."""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
BG = "#09111f"
PANEL = "#111d2e"
PANEL_2 = "#16243a"
WHITE = "#f7fafc"
MUTED = "#a8b4c7"
BLUE = "#5b8cff"
CYAN = "#35c2e3"
GREEN = "#39d98a"
ORANGE = "#ffb454"
RED = "#ff6b6b"
LINE = "#2a3a53"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def wrap(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    return lines


def multiline(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, *, size: int, color: str, width: int, bold: bool = False, spacing: int = 8) -> int:
    lines = wrap(text, width)
    draw.multiline_text(xy, "\n".join(lines), font=font(size, bold), fill=color, spacing=spacing)
    return len(lines) * (size + spacing)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None, radius: int = 24, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def header(draw: ImageDraw.ImageDraw, title: str, kicker: str, scene_no: int, total: int) -> None:
    draw.text((72, 46), kicker.upper(), font=font(22, True), fill=CYAN)
    draw.text((72, 82), title, font=font(42, True), fill=WHITE)
    rounded(draw, (1550, 48, 1848, 94), PANEL_2, LINE, 18)
    draw.text((1699, 61), "FICTIONAL DATA ONLY", font=font(16, True), fill=MUTED, anchor="ma")
    draw.line((72, 146, 1848, 146), fill=LINE, width=2)
    progress = int(1776 * scene_no / total)
    draw.rectangle((72, 1043, 1848, 1049), fill=LINE)
    draw.rectangle((72, 1043, 72 + progress, 1049), fill=CYAN)


def chat_panel(draw: ImageDraw.ImageDraw, messages: list[tuple[str, str]]) -> None:
    rounded(draw, (72, 178, 1120, 1008), PANEL, LINE, 28)
    draw.text((104, 206), "CUSTOMER CONVERSATION", font=font(19, True), fill=CYAN)
    y = 252
    for role, text in messages[-5:]:
        is_user = role == "Customer"
        box_w = 770 if is_user else 850
        lines = wrap(text, 47 if is_user else 53)
        box_h = 60 + len(lines) * 30
        x2 = 1080 if is_user else 970
        x1 = x2 - box_w
        fill = "#20314b" if is_user else "#13293a"
        border = BLUE if is_user else CYAN
        rounded(draw, (x1, y, x2, y + box_h), fill, border, 22, 2)
        draw.text((x1 + 24, y + 16), role.upper(), font=font(15, True), fill=border)
        draw.multiline_text((x1 + 24, y + 45), "\n".join(lines), font=font(24), fill=WHITE, spacing=7)
        y += box_h + 18


def activity_panel(draw: ImageDraw.ImageDraw, steps: list[tuple[str, str, str]], note: str = "") -> None:
    rounded(draw, (1150, 178, 1848, 1008), PANEL_2, "#335071", 28)
    draw.text((1182, 206), "AGENT ACTIVITY", font=font(19, True), fill=GREEN)
    y = 270
    colors = {"done": GREEN, "current": CYAN, "pending": "#65738a", "transfer": ORANGE, "blocked": RED}
    labels = {"done": "OK", "current": "•", "pending": "–", "transfer": ">", "blocked": "!"}
    for label, state, detail in steps:
        color = colors[state]
        draw.ellipse((1185, y, 1231, y + 46), fill="#102234", outline=color, width=3)
        draw.text((1208, y + 23), labels[state], font=font(16 if state == "done" else 22, True), fill=color, anchor="mm")
        draw.text((1254, y - 2), label, font=font(23, True), fill=WHITE if state != "pending" else MUTED)
        if detail:
            multiline(draw, (1254, y + 31), detail, size=17, color=color if state != "pending" else MUTED, width=45)
        if y < 760:
            draw.line((1208, y + 48, 1208, y + 98), fill=LINE, width=3)
        y += 105
    if note:
        rounded(draw, (1182, 886, 1816, 968), "#102d37", "#1e5966", 18)
        multiline(draw, (1204, 906), note, size=17, color=CYAN, width=62, bold=True)


def title_frame() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((960, 160), "FRAUD BLOCK AGENT", font=font(62, True), fill=WHITE, anchor="ma")
    d.text((960, 242), "Recorded end-to-end demonstration", font=font(30), fill=MUTED, anchor="ma")
    stages = [("UNDERSTAND", CYAN), ("ROUTE", BLUE), ("VERIFY", ORANGE), ("ACT", GREEN)]
    x = 260
    for i, (label, color) in enumerate(stages):
        rounded(d, (x, 420, x + 280, 550), PANEL, color, 25, 4)
        d.text((x + 140, 485), label, font=font(25, True), fill=color, anchor="mm")
        if i < len(stages) - 1:
            d.line((x + 285, 485, x + 355, 485), fill="#65738a", width=5)
            d.polygon([(x + 355, 485), (x + 332, 470), (x + 332, 500)], fill="#65738a")
        x += 400
    rounded(d, (430, 690, 1490, 806), "#102d37", "#1e5966", 24)
    d.text((960, 728), "LLM understands the request", font=font(25, True), fill=CYAN, anchor="ma")
    d.text((960, 770), "Deterministic code verifies identity and protects the banking action", font=font(23), fill=WHITE, anchor="ma")
    d.text((960, 965), "No live API calls • Reproducible playback • Fictional records", font=font(20), fill=MUTED, anchor="ma")
    return im


def split_frame(title: str, kicker: str, messages: list[tuple[str, str]], steps: list[tuple[str, str, str]], note: str, index: int, total: int) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    header(d, title, kicker, index, total)
    chat_panel(d, messages)
    activity_panel(d, steps, note)
    return im


def end_frame() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((960, 135), "WHAT MAKES IT AGENTIC?", font=font(48, True), fill=WHITE, anchor="ma")
    columns = [
        (250, "LLM", "Understands natural language\nand selects the service", CYAN),
        (710, "CODE", "Verifies identity, ownership\nand business rules", BLUE),
        (1170, "TOOLS", "Retrieve the latest transaction\nand execute the protected action", ORANGE),
        (1550, "STATE", "Confirms the card is active\nafter the change", GREEN),
    ]
    for x, title, detail, color in columns:
        rounded(d, (x - 185, 300, x + 185, 600), PANEL, color, 28, 4)
        d.ellipse((x - 38, 340, x + 38, 416), fill="#102234", outline=color, width=4)
        d.text((x, 378), title[0], font=font(32, True), fill=color, anchor="mm")
        d.text((x, 462), title, font=font(28, True), fill=color, anchor="ma")
        d.multiline_text((x, 520), detail, font=font(19), fill=WHITE, spacing=8, anchor="ma", align="center")
    d.line((435, 450, 525, 450), fill="#65738a", width=5)
    d.polygon([(525, 450), (503, 436), (503, 464)], fill="#65738a")
    d.line((895, 450, 985, 450), fill="#65738a", width=5)
    d.polygon([(985, 450), (963, 436), (963, 464)], fill="#65738a")
    d.line((1355, 450, 1400, 450), fill="#65738a", width=5)
    d.polygon([(1400, 450), (1378, 436), (1378, 464)], fill="#65738a")
    rounded(d, (330, 720, 1590, 832), "#173b31", "#28664f", 24)
    d.text((960, 760), "The model interprets. The system verifies, decides, and acts.", font=font(30, True), fill=GREEN, anchor="ma")
    d.text((960, 806), "Recorded from the same deterministic workflow used by the evaluation suite.", font=font(20), fill=WHITE, anchor="ma")
    d.text((960, 990), "Fraud Block Agent • Educational demonstration", font=font(20), fill=MUTED, anchor="ma")
    return im


def build_frames(output_dir: Path) -> list[int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_steps = [
        ("Intent interpretation", "pending", "Waiting for customer request"),
        ("Authentication", "pending", "Full fake card + date of birth"),
        ("Latest transaction", "pending", "Retrieve and confirm one transaction"),
        ("Block removal", "pending", "Protected banking action"),
        ("Final state", "pending", "Verify card status"),
    ]
    scenes: list[tuple[Image.Image, int]] = [(title_frame(), 5)]

    scenes.append((split_frame(
        "The customer states the goal naturally", "1 • UNDERSTAND",
        [("Customer", "Those alert purchases were mine. Please unblock my card.")],
        [("Intent interpretation", "current", "LLM reviews the message and available services"), *base_steps[1:]],
        "Every customer message is interpreted by the LLM.", 2, 11), 5))

    scenes.append((split_frame(
        "The LLM selects the block-removal route", "2 • ROUTE",
        [("Customer", "Those alert purchases were mine. Please unblock my card."),
         ("Assistant", "Certainly. I’ll authenticate your identity before removing the block.")],
        [("Intent: BLOCK_REMOVAL", "done", "Next action: START_AUTHENTICATION"), *base_steps[1:]],
        "The LLM recommends a route; deterministic code controls the workflow.", 3, 11), 5))

    scenes.append((split_frame(
        "Authentication uses the customer and card tables", "3 • VERIFY IDENTITY",
        [("Assistant", "Please enter the full fake card number and your date of birth."),
         ("Customer", "Card: 9000 0000 0000 1001\nDate of birth: 1990-01-15")],
        [("Intent: BLOCK_REMOVAL", "done", "Route selected"),
         ("Authentication", "current", "Match card → owner → date of birth"), *base_steps[2:]],
        "The card number and date of birth must resolve to the same fictional customer.", 4, 11), 6))

    scenes.append((split_frame(
        "Identity and ownership are verified", "4 • AUTHENTICATION PASSES",
        [("Customer", "Card: 9000 0000 0000 1001\nDate of birth: 1990-01-15"),
         ("Assistant", "Thank you. Your identity has been verified.")],
        [("Intent: BLOCK_REMOVAL", "done", "Route selected"),
         ("Authentication", "done", "CUST-001 ↔ CARD-001"), *base_steps[2:]],
        "No account details are disclosed before authentication succeeds.", 5, 11), 5))

    scenes.append((split_frame(
        "Only the latest flagged transaction is presented", "5 • RETRIEVE TRANSACTION",
        [("Assistant", "Please confirm the latest transaction: July 30, 2026 at Example Grocery for $42.18. Was this transaction made by you?")],
        [("Intent: BLOCK_REMOVAL", "done", "Route selected"),
         ("Authentication", "done", "CUST-001 ↔ CARD-001"),
         ("Latest transaction", "current", "TX-001-A • Example Grocery • $42.18"), *base_steps[3:]],
        "The system retrieves the most recent transaction for the authenticated card.", 6, 11), 6))

    scenes.append((split_frame(
        "The customer recognizes the transaction", "6 • CUSTOMER CONFIRMATION",
        [("Assistant", "Was this transaction made by you?"),
         ("Customer", "Yes, I made that purchase.")],
        [("Intent: BLOCK_REMOVAL", "done", "Route selected"),
         ("Authentication", "done", "CUST-001 ↔ CARD-001"),
         ("Transaction recognized", "done", "Recognition interpreted from the reply"), *base_steps[3:]],
        "A negative or uncertain answer keeps the block in place and triggers transfer.", 7, 11), 5))

    scenes.append((split_frame(
        "Protected checks approve the removal", "7 • DECIDE",
        [("Customer", "Yes, I made that purchase."),
         ("Assistant", "Thanks for confirming. I’m removing the fraud block now.")],
        [("Authentication", "done", "Identity and ownership verified"),
         ("Transaction recognized", "done", "Latest transaction confirmed"),
         ("Eligibility approved", "done", "Case permits automated removal"),
         ("Block removal", "current", "Execute protected banking action"),
         ("Final state", "pending", "Verify card status")],
        "Once all checkpoints pass, the system removes the block without another confirmation.", 8, 11), 5))

    scenes.append((split_frame(
        "The system removes the block and verifies the result", "8 • ACT + VERIFY",
        [("Assistant", "Your card ending in 1001 is active again. The fraud block was removed.")],
        [("Authentication", "done", "CUST-001 ↔ CARD-001"),
         ("Transaction recognized", "done", "TX-001-A"),
         ("Eligibility approved", "done", "All protected checks passed"),
         ("Block removed", "done", "CARD-001 updated"),
         ("Final state: ACTIVE", "done", "Post-action verification succeeded")],
        "Successful completion requires both the action and final-state verification.", 9, 11), 6))

    scenes.append((split_frame(
        "Alternative route: suspected fraud", "ROUTING EXAMPLE",
        [("Customer", "I don’t recognize the transaction on my card."),
         ("Assistant", "I’m transferring you to a fraud specialist now.")],
        [("Intent: SUSPECTED_FRAUD", "done", "Unauthorized activity reported"),
         ("Fraud specialist", "transfer", "Immediate transfer"),
         ("Authentication", "pending", "Not performed before transfer")],
        "Suspected fraud bypasses block removal and goes directly to a specialist.", 10, 11), 5))

    scenes.append((split_frame(
        "Alternative route: non-fraud request", "ROUTING EXAMPLE",
        [("Customer", "What is the current GIC rate?"),
         ("Assistant", "The Fraud Department can’t assist with GIC rates. I can transfer you to the appropriate team, or help with a fraud-related concern.")],
        [("Intent: NON_FRAUD", "done", "Outside Fraud Department scope"),
         ("Corresponding team", "transfer", "Offer transfer"),
         ("Fraud session", "pending", "Available if the customer changes topic")],
        "The conversation stays open long enough to identify any fraud-related need.", 11, 11), 6))

    scenes.append((end_frame(), 7))

    durations: list[int] = []
    for index, (image, duration) in enumerate(scenes, start=1):
        image.save(output_dir / f"scene_{index:02d}.png")
        durations.append(duration)
    (output_dir / "durations.txt").write_text("\n".join(str(x) for x in durations) + "\n")
    return durations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    durations = build_frames(args.output_dir)
    print(f"Rendered {len(durations)} scenes, {sum(durations)} seconds")


if __name__ == "__main__":
    main()
