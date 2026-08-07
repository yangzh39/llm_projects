"""Build an editable Excalidraw decision-flow diagram and PNG preview."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from artifact_paths import DIAGRAMS, IMAGES, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
EXCALIDRAW_PATH = DIAGRAMS / "Fraud_Block_Agent_Decision_Flow.excalidraw"
PREVIEW_PATH = IMAGES / "Fraud_Block_Agent_Decision_Flow_preview.png"

CANVAS_W = 2400
CANVAS_H = 1420
BG = "#f8fafc"
INK = "#172033"
MUTED = "#64748b"
BLUE = "#2563eb"
BLUE_BG = "#dbeafe"
PURPLE = "#7c3aed"
PURPLE_BG = "#ede9fe"
GREEN = "#15803d"
GREEN_BG = "#dcfce7"
ORANGE = "#c2410c"
ORANGE_BG = "#ffedd5"
RED = "#b91c1c"
RED_BG = "#fee2e2"
GRAY_BG = "#e2e8f0"
LINE = "#475569"


class Diagram:
    def __init__(self) -> None:
        self.arrows: list[dict[str, Any]] = []
        self.shapes: list[dict[str, Any]] = []
        self.texts: list[dict[str, Any]] = []
        self.counter = 1

    def _base(self, kind: str, x: float, y: float, w: float, h: float) -> dict[str, Any]:
        current = self.counter
        self.counter += 1
        return {
            "id": f"element-{current}",
            "type": kind,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "angle": 0,
            "strokeColor": INK,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "index": f"a{current:03d}",
            "roundness": None,
            "seed": 1000 + current,
            "version": 1,
            "versionNonce": 5000 + current,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1785984000000,
            "link": None,
            "locked": False,
        }

    def rect(self, x: float, y: float, w: float, h: float, *, fill: str, stroke: str, radius: bool = True) -> None:
        item = self._base("rectangle", x, y, w, h)
        item.update({"backgroundColor": fill, "strokeColor": stroke, "roundness": {"type": 3} if radius else None})
        self.shapes.append(item)

    def diamond(self, x: float, y: float, w: float, h: float, *, fill: str = PURPLE_BG, stroke: str = PURPLE) -> None:
        item = self._base("diamond", x, y, w, h)
        item.update({"backgroundColor": fill, "strokeColor": stroke, "roundness": {"type": 2}})
        self.shapes.append(item)

    def text(self, x: float, y: float, w: float, h: float, value: str, *, size: int = 24, color: str = INK, align: str = "center", bold: bool = False) -> None:
        item = self._base("text", x, y, w, h)
        item.update(
            {
                "strokeColor": color,
                "backgroundColor": "transparent",
                "strokeWidth": 1,
                "fontSize": size,
                "fontFamily": 2,
                "text": value,
                "originalText": value,
                "textAlign": align,
                "verticalAlign": "middle",
                "containerId": None,
                "autoResize": False,
                "lineHeight": 1.25,
                "roundness": None,
                "bold": bold,
            }
        )
        self.texts.append(item)

    def arrow(self, x: float, y: float, points: list[list[float]], *, color: str = LINE, label: str | None = None, label_x: float = 0, label_y: float = 0) -> None:
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        item = self._base("arrow", x, y, max(xs) - min(xs), max(ys) - min(ys))
        item.update(
            {
                "strokeColor": color,
                "backgroundColor": "transparent",
                "points": points,
                "lastCommittedPoint": None,
                "startBinding": None,
                "endBinding": None,
                "startArrowhead": None,
                "endArrowhead": "arrow",
                "elbowed": len(points) > 2,
                "roundness": {"type": 2},
            }
        )
        self.arrows.append(item)
        if label:
            self.text(label_x, label_y, 95, 32, label, size=18, color=color, bold=True)

    def elements(self) -> list[dict[str, Any]]:
        return [*self.arrows, *self.shapes, *self.texts]


def add_card(diagram: Diagram, x: float, y: float, w: float, h: float, title: str, body: str, *, fill: str, stroke: str, title_color: str | None = None) -> None:
    diagram.rect(x, y, w, h, fill=fill, stroke=stroke)
    diagram.text(x + 20, y + 16, w - 40, 34, title, size=23, color=title_color or stroke, bold=True)
    diagram.text(x + 24, y + 56, w - 48, h - 70, body, size=18, color=INK)


def build_diagram() -> Diagram:
    d = Diagram()

    d.text(65, 30, 1450, 58, "Fraud Block Agent — Decision Flow", size=40, align="left", bold=True)
    d.text(65, 92, 1700, 36, "Every customer message is interpreted by the LLM; protected banking actions remain deterministic.", size=22, color=MUTED, align="left")

    # Entry and LLM routing.
    add_card(d, 65, 210, 235, 125, "CUSTOMER", "Any natural-language\nmessage", fill="#ffffff", stroke=LINE)
    add_card(d, 390, 195, 300, 155, "LLM INTERPRETATION", "Human response\n+ structured JSON instruction", fill=BLUE_BG, stroke=BLUE)
    d.diamond(790, 190, 250, 170)
    d.text(835, 225, 160, 95, "What service\nis needed?", size=23, color=PURPLE, bold=True)
    d.arrow(300, 272, [[0, 0], [85, 0]], color=BLUE)
    d.arrow(690, 272, [[0, 0], [90, 0]], color=BLUE)

    # Three top-level routes.
    add_card(d, 1135, 155, 300, 120, "NON-FRAUD", "Explain scope + offer\ncorresponding-team transfer", fill=GRAY_BG, stroke=LINE)
    d.diamond(1535, 140, 230, 150, fill="#f1f5f9", stroke=LINE)
    d.text(1580, 174, 140, 80, "Customer\nchoice?", size=21, color=INK, bold=True)
    add_card(d, 1870, 55, 260, 95, "TRANSFER", "Corresponding team", fill=BLUE_BG, stroke=BLUE)
    add_card(d, 1870, 180, 260, 95, "CLOSE", "One polite closing", fill="#ffffff", stroke=LINE)
    add_card(d, 1870, 305, 365, 105, "FRAUD HELP REQUESTED", "Start a fresh fraud-routing chain\nwith up to 3 interpretation turns", fill=PURPLE_BG, stroke=PURPLE)
    d.arrow(1000, 220, [[0, 0], [125, 0]], color=LINE, label="non-fraud", label_x=1018, label_y=176)
    d.arrow(1435, 215, [[0, 0], [90, 0]], color=LINE)
    d.arrow(1765, 190, [[0, 0], [55, 0], [55, -88], [95, -88]], color=BLUE, label="transfer", label_x=1775, label_y=65)
    d.arrow(1765, 215, [[0, 0], [95, 0]], color=LINE, label="no", label_x=1780, label_y=218)
    d.arrow(1650, 290, [[0, 0], [0, 68], [210, 68]], color=PURPLE, label="fraud need", label_x=1680, label_y=315)

    add_card(d, 1135, 330, 300, 115, "SUSPECTED FRAUD", "Unrecognized activity\nor suspected fraud", fill=ORANGE_BG, stroke=ORANGE)
    add_card(d, 1535, 330, 300, 115, "FRAUD SPECIALIST", "Immediate transfer\nNo authentication first", fill=RED_BG, stroke=RED)
    d.arrow(995, 276, [[0, 0], [65, 0], [65, 110], [65, 110], [130, 110]], color=ORANGE, label="fraud", label_x=1010, label_y=335)
    d.arrow(1435, 387, [[0, 0], [90, 0]], color=RED)

    add_card(d, 1135, 505, 300, 115, "BLOCK REMOVAL", "Card is blocked or customer\nwants it unblocked", fill=GREEN_BG, stroke=GREEN)
    d.diamond(1535, 480, 240, 170, fill=GREEN_BG, stroke=GREEN)
    d.text(1580, 520, 150, 90, "Explicit request\nto remove?", size=21, color=GREEN, bold=True)
    add_card(d, 1870, 470, 390, 145, "PLAIN-LANGUAGE CHOICE", "If the transaction was yours → removal\nIf you suspect fraud → specialist\nNext message returns to LLM routing", fill="#ffffff", stroke=GREEN)
    d.arrow(995, 306, [[0, 0], [35, 0], [35, 256], [95, 256], [130, 256]], color=GREEN, label="blocked", label_x=1010, label_y=515)
    d.arrow(1435, 562, [[0, 0], [90, 0]], color=GREEN)
    d.arrow(1775, 555, [[0, 0], [85, 0]], color=GREEN, label="not yet", label_x=1780, label_y=515)
    d.arrow(2260, 540, [[0, 0], [40, 0], [40, -182], [-15, -182]], color=PURPLE, label="next message", label_x=2130, label_y=490)
    d.arrow(2050, 305, [[0, 0], [0, -155], [-1275, -155], [-1275, 40]], color=PURPLE)

    # Protected block-removal pipeline.
    d.text(65, 720, 1200, 38, "PROTECTED BLOCK-REMOVAL WORKFLOW", size=24, color=GREEN, align="left", bold=True)
    d.text(65, 756, 1200, 30, "Executed by deterministic code and tools—not by the language model", size=18, color=MUTED, align="left")
    add_card(d, 65, 820, 235, 115, "AUTHENTICATE", "Full fake card number\n+ date of birth", fill=GREEN_BG, stroke=GREEN)
    d.diamond(355, 805, 190, 145, fill=GREEN_BG, stroke=GREEN)
    d.text(395, 840, 110, 70, "Identity\nverified?", size=20, color=GREEN, bold=True)
    add_card(d, 600, 820, 230, 115, "MATCH", "Locate customer + card\nand verify ownership", fill=GREEN_BG, stroke=GREEN)
    add_card(d, 880, 820, 240, 115, "MOST RECENT TXN", "Retrieve and present\nlatest flagged transaction", fill=GREEN_BG, stroke=GREEN)
    d.diamond(1170, 805, 190, 145, fill=GREEN_BG, stroke=GREEN)
    d.text(1208, 840, 115, 70, "Customer\nrecognizes it?", size=19, color=GREEN, bold=True)
    d.diamond(1410, 805, 190, 145, fill=GREEN_BG, stroke=GREEN)
    d.text(1447, 840, 118, 70, "Eligible for\nauto-removal?", size=19, color=GREEN, bold=True)
    add_card(d, 1650, 820, 210, 115, "REMOVE BLOCK", "Execute protected\nbanking action", fill=GREEN_BG, stroke=GREEN)
    add_card(d, 1910, 820, 210, 115, "VERIFY STATUS", "Confirm card is\nactive", fill=GREEN_BG, stroke=GREEN)
    add_card(d, 2170, 820, 165, 115, "SUCCESS", "Block removed\nand verified", fill="#bbf7d0", stroke=GREEN)

    # Route the explicit-removal decision into the deterministic workflow.
    d.arrow(1655, 650, [[0, 0], [0, 140], [-1470, 140], [-1470, 160]], color=GREEN, label="yes", label_x=1550, label_y=667)
    for x, length in [(300, 45), (545, 45), (830, 40), (1120, 40), (1360, 40), (1600, 40), (1860, 40), (2120, 40)]:
        d.arrow(x, 877, [[0, 0], [length, 0]], color=GREEN)

    # Failure paths under their decision gates.
    add_card(d, 275, 1010, 350, 110, "AUTHENTICATION FAILS", "No account details disclosed\nTransfer to a specialist", fill=RED_BG, stroke=RED)
    add_card(d, 1045, 1010, 345, 110, "TRANSACTION NOT RECOGNIZED", "Keep the block in place\nTransfer to fraud specialist", fill=RED_BG, stroke=RED)
    add_card(d, 1435, 1010, 320, 110, "NOT ELIGIBLE", "No automatic removal\nTransfer to specialist", fill=ORANGE_BG, stroke=ORANGE)
    d.arrow(450, 950, [[0, 0], [0, 50]], color=RED, label="no", label_x=462, label_y=960)
    d.arrow(1265, 950, [[0, 0], [0, 50]], color=RED, label="no", label_x=1277, label_y=960)
    d.arrow(1505, 950, [[0, 0], [0, 50]], color=ORANGE, label="no", label_x=1517, label_y=960)

    # Cross-cutting boundaries.
    add_card(d, 65, 1210, 705, 145, "SAFETY BOUNDARY", "LLM: understand, converse, and emit instructions\nCode + tools: authenticate, disclose, decide, remove, and verify", fill=BLUE_BG, stroke=BLUE)
    add_card(d, 835, 1210, 705, 145, "DATA + TOOL LAYER", "Separate customer, card, fraud-case, and transaction datasets\nCredentials never go to the LLM", fill=GREEN_BG, stroke=GREEN)
    add_card(d, 1605, 1210, 730, 145, "DETERMINISTIC EVALUATION", "10 scenarios • outcome • trajectory • safety gates • efficiency\nDesigned to catch hidden workflow failures", fill=PURPLE_BG, stroke=PURPLE)
    return d


def write_excalidraw(diagram: Diagram) -> None:
    payload = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": diagram.elements(),
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": BG,
            "currentItemFontFamily": 2,
            "currentItemStrokeColor": INK,
            "currentItemBackgroundColor": "transparent",
            "currentItemFillStyle": "solid",
            "currentItemStrokeWidth": 2,
            "currentItemRoughness": 0,
            "zoom": {"value": 0.5},
            "scrollX": 0,
            "scrollY": 0,
        },
        "files": {},
    }
    EXCALIDRAW_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def write_preview(diagram: Diagram) -> None:
    scale = 0.72
    image = Image.new("RGB", (round(CANVAS_W * scale), round(CANVAS_H * scale)), BG)
    draw = ImageDraw.Draw(image)

    def pt(value: float) -> float:
        return value * scale

    # Draw arrows first.
    for item in diagram.arrows:
        points = [(pt(item["x"] + p[0]), pt(item["y"] + p[1])) for p in item["points"]]
        draw.line(points, fill=item["strokeColor"], width=max(2, round(3 * scale)), joint="curve")
        if len(points) >= 2:
            x2, y2 = points[-1]
            x1, y1 = points[-2]
            if abs(x2 - x1) >= abs(y2 - y1):
                sign = 1 if x2 > x1 else -1
                head = [(x2, y2), (x2 - sign * 12, y2 - 7), (x2 - sign * 12, y2 + 7)]
            else:
                sign = 1 if y2 > y1 else -1
                head = [(x2, y2), (x2 - 7, y2 - sign * 12), (x2 + 7, y2 - sign * 12)]
            draw.polygon(head, fill=item["strokeColor"])

    for item in diagram.shapes:
        box = (pt(item["x"]), pt(item["y"]), pt(item["x"] + item["width"]), pt(item["y"] + item["height"]))
        if item["type"] == "diamond":
            x1, y1, x2, y2 = box
            draw.polygon(((x1 + x2) / 2, y1, x2, (y1 + y2) / 2, (x1 + x2) / 2, y2, x1, (y1 + y2) / 2), fill=item["backgroundColor"], outline=item["strokeColor"])
        else:
            draw.rounded_rectangle(box, radius=10, fill=item["backgroundColor"], outline=item["strokeColor"], width=2)

    for item in diagram.texts:
        value = item["text"]
        f = get_font(max(9, round(item["fontSize"] * scale)), item.get("bold", False))
        x = pt(item["x"] + item["width"] / 2)
        y = pt(item["y"] + item["height"] / 2)
        anchor = "mm"
        if item["textAlign"] == "left":
            x = pt(item["x"])
            anchor = "lm"
        draw.multiline_text((x, y), value, font=f, fill=item["strokeColor"], spacing=3, align=item["textAlign"], anchor=anchor)
    image.save(PREVIEW_PATH)


def main() -> None:
    ensure_artifact_dirs()
    diagram = build_diagram()
    write_excalidraw(diagram)
    write_preview(diagram)
    print(EXCALIDRAW_PATH)
    print(PREVIEW_PATH)


if __name__ == "__main__":
    main()
