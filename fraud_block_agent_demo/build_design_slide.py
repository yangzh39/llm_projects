"""Generate a single-slide, editable PowerPoint architecture overview.

The implementation uses only Python's standard library for the PPTX package and
Pillow for a matching PNG preview, keeping generation reproducible.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw, ImageFont

from artifact_paths import IMAGES, PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
PPTX_PATH = PRESENTATIONS / "Fraud_Block_Agent_Design.pptx"
PREVIEW_PATH = IMAGES / "Fraud_Block_Agent_Design_preview.png"

EMU = 914400
SLIDE_W = 13.333
SLIDE_H = 7.5

BG = "09111F"
PANEL = "111D2E"
PANEL_2 = "16243A"
WHITE = "F7FAFC"
MUTED = "A8B4C7"
CYAN = "35C2E3"
BLUE = "5B8CFF"
GREEN = "39D98A"
ORANGE = "FFB454"
RED = "FF6B6B"
LINE = "2A3A53"


def emu(value: float) -> int:
    return round(value * EMU)


def rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def xml_text(value: str) -> str:
    return escape(value, quote=False)


class SlideBuilder:
    def __init__(self) -> None:
        self.items: list[str] = []
        self.next_id = 2

    def _id(self) -> int:
        value = self.next_id
        self.next_id += 1
        return value

    def shape(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: str,
        line: str = LINE,
        radius: bool = True,
        name: str = "Shape",
    ) -> None:
        shape_id = self._id()
        geometry = "roundRect" if radius else "rect"
        self.items.append(
            f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name} {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
<a:prstGeom prst="{geometry}"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln></p:spPr></p:sp>"""
        )

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        value: str,
        *,
        size: float = 12,
        color: str = WHITE,
        bold: bool = False,
        align: str = "l",
        valign: str = "mid",
        margin: float = 0.0,
        font: str = "Arial",
        name: str = "Text",
    ) -> None:
        shape_id = self._id()
        paragraphs = []
        for line_value in value.split("\n"):
            paragraphs.append(
                f"""<a:p><a:pPr algn="{align}"/><a:r><a:rPr lang="en-US" sz="{round(size * 100)}" b="{1 if bold else 0}" dirty="0"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/></a:rPr><a:t>{xml_text(line_value)}</a:t></a:r><a:endParaRPr lang="en-US" sz="{round(size * 100)}"/></a:p>"""
            )
        m = emu(margin)
        self.items.append(
            f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name} {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
<p:txBody><a:bodyPr wrap="square" lIns="{m}" tIns="{m}" rIns="{m}" bIns="{m}" anchor="{valign}"/><a:lstStyle/>{''.join(paragraphs)}</p:txBody></p:sp>"""
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, *, color: str = LINE, width: float = 1.5, arrow: bool = False) -> None:
        shape_id = self._id()
        head = '<a:headEnd type="none"/>'
        tail = '<a:tailEnd type="triangle"/>' if arrow else '<a:tailEnd type="none"/>'
        self.items.append(
            f"""<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="Connector {shape_id}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
<p:spPr><a:xfrm><a:off x="{emu(x1)}" y="{emu(y1)}"/><a:ext cx="{emu(x2-x1)}" cy="{emu(y2-y1)}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>
<a:ln w="{round(width * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{tail}{head}</a:ln></p:spPr></p:cxnSp>"""
        )

    def circle(self, x: float, y: float, d: float, *, fill: str, line: str | None = None) -> None:
        shape_id = self._id()
        line = line or fill
        self.items.append(
            f"""<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Circle {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(d)}" cy="{emu(d)}"/></a:xfrm><a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill><a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln></p:spPr></p:sp>"""
        )

    def xml(self) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld name="Fraud Block Agent Design"><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{BG}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
{''.join(self.items)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''


def add_pill(slide: SlideBuilder, x: float, y: float, w: float, label: str, color: str) -> None:
    slide.shape(x, y, w, 0.28, fill=color, line=color)
    slide.text(x, y + 0.005, w, 0.265, label, size=8.5, color=BG, bold=True, align="ctr")


def build_slide() -> SlideBuilder:
    s = SlideBuilder()

    # Header
    s.text(0.5, 0.28, 9.6, 0.48, "Fraud Block Agent | End-to-End Design", size=25, bold=True)
    s.text(0.5, 0.78, 9.8, 0.30, "DeepSeek interprets every customer message; deterministic controls protect decisions and actions.", size=10.5, color=MUTED)
    add_pill(s, 10.45, 0.38, 2.36, "BEGINNER-FRIENDLY  •  REPRODUCIBLE", CYAN)
    s.line(0.5, 1.15, 12.82, 1.15, color=LINE, width=1)

    # Customer/channel card
    s.shape(0.5, 1.42, 1.45, 3.82, fill=PANEL, line=LINE)
    s.circle(0.93, 1.75, 0.58, fill=BLUE, line=BLUE)
    s.text(0.93, 1.77, 0.58, 0.52, "C", size=17, color=WHITE, bold=True, align="ctr")
    s.text(0.68, 2.46, 1.08, 0.35, "CUSTOMER", size=9, color=CYAN, bold=True, align="ctr")
    s.text(0.66, 2.88, 1.12, 0.72, "Streamlit chat\nCLI explorer", size=12, bold=True, align="ctr")
    s.text(0.67, 3.86, 1.10, 0.65, "Free-form\nnatural language", size=9.5, color=MUTED, align="ctr")
    s.text(0.67, 4.66, 1.10, 0.25, "Every turn → LLM", size=8.5, color=GREEN, bold=True, align="ctr")

    # Main orchestration stages
    s.line(1.95, 3.28, 2.22, 3.28, color=CYAN, width=2.2, arrow=True)

    s.shape(2.25, 1.42, 2.18, 3.82, fill=PANEL, line=LINE)
    add_pill(s, 2.50, 1.66, 1.18, "01  UNDERSTAND", CYAN)
    s.text(2.50, 2.10, 1.68, 0.34, "DeepSeek API", size=17, bold=True)
    s.text(2.50, 2.55, 1.67, 0.82, "Interprets intent\nWrites human response\nEmits structured JSON", size=10.5, color=MUTED)
    s.line(2.50, 3.52, 4.15, 3.52, color=LINE, width=1)
    s.text(2.50, 3.70, 1.67, 0.75, "Handles topic switches\nand natural replies", size=10.5, bold=True)
    s.shape(2.50, 4.55, 1.66, 0.42, fill="102D37", line="1E5966")
    s.text(2.56, 4.60, 1.54, 0.31, "≤ 3 clarification turns", size=9, color=CYAN, bold=True, align="ctr")

    s.line(4.43, 3.28, 4.70, 3.28, color=CYAN, width=2.2, arrow=True)

    s.shape(4.73, 1.42, 2.28, 3.82, fill=PANEL, line=LINE)
    add_pill(s, 4.98, 1.66, 0.92, "02  ROUTE", BLUE)
    s.text(4.98, 2.08, 1.78, 0.58, "Python\norchestrator", size=14, bold=True)
    s.text(4.98, 2.68, 1.78, 0.30, "Consumes the JSON instruction", size=9.2, color=MUTED)
    s.shape(4.98, 3.00, 1.78, 0.47, fill="173B31", line="28664F")
    s.circle(5.12, 3.13, 0.18, fill=GREEN)
    s.text(5.42, 3.07, 1.18, 0.30, "Remove block", size=10.5, bold=True)
    s.shape(4.98, 3.61, 1.78, 0.47, fill="3A2B1A", line="684B25")
    s.circle(5.12, 3.74, 0.18, fill=ORANGE)
    s.text(5.42, 3.68, 1.18, 0.30, "Suspected fraud", size=10.5, bold=True)
    s.shape(4.98, 4.22, 1.78, 0.47, fill="202B3C", line="35455E")
    s.circle(5.12, 4.35, 0.18, fill=MUTED)
    s.text(5.42, 4.29, 1.18, 0.30, "Non-fraud", size=10.5, bold=True)

    s.line(7.01, 3.28, 7.28, 3.28, color=GREEN, width=2.2, arrow=True)

    s.shape(7.31, 1.42, 2.72, 3.82, fill=PANEL, line=LINE)
    add_pill(s, 7.56, 1.66, 0.76, "03  ACT", GREEN)
    s.text(7.56, 2.10, 2.22, 0.34, "Protected removal path", size=15.5, bold=True)
    steps = [
        ("1", "Authenticate full card + DOB"),
        ("2", "Match customer and card"),
        ("3", "Confirm latest transaction only"),
        ("4", "Check removal eligibility"),
        ("5", "Remove fraud block"),
        ("6", "Verify final card status"),
    ]
    for idx, (number, label) in enumerate(steps):
        yy = 2.57 + idx * 0.40
        s.circle(7.57, yy, 0.24, fill="173B31", line="28664F")
        s.text(7.57, yy + 0.005, 0.24, 0.22, number, size=8.5, color=GREEN, bold=True, align="ctr")
        s.text(7.91, yy - 0.015, 1.85, 0.28, label, size=9.5, color=WHITE, bold=idx in {0, 2, 5})

    # Right rail: guardrails + evaluation
    s.shape(10.29, 1.42, 2.53, 1.79, fill=PANEL_2, line="335071")
    s.text(10.55, 1.68, 2.00, 0.27, "SAFETY BOUNDARY", size=9, color=CYAN, bold=True)
    s.text(10.55, 2.06, 2.00, 0.40, "LLM does not approve\nor execute bank actions", size=12.5, bold=True)
    s.text(10.55, 2.59, 2.00, 0.38, "Tools enforce identity, ownership,\neligibility and final-state checks.", size=9.2, color=MUTED)

    s.shape(10.29, 3.44, 2.53, 1.80, fill=PANEL_2, line="335071")
    s.text(10.55, 3.70, 2.00, 0.27, "EVALUATION HARNESS", size=9, color=GREEN, bold=True)
    s.text(10.55, 4.08, 2.00, 0.32, "10 deterministic scenarios", size=12.5, bold=True)
    s.text(10.55, 4.47, 2.00, 0.52, "Outcome  •  trajectory\nSafety gates  •  efficiency", size=9.5, color=MUTED)
    s.text(10.55, 4.98, 2.00, 0.18, "Catches hidden workflow failures", size=8.5, color=ORANGE, bold=True)

    # Branch outcomes
    s.text(0.5, 5.55, 2.0, 0.23, "ROUTING OUTCOMES", size=8.5, color=MUTED, bold=True)
    cards = [
        (0.50, 3.82, GREEN, "BLOCK REMOVAL", "Authenticate → verify latest transaction → remove → confirm active"),
        (4.50, 3.78, ORANGE, "SUSPECTED FRAUD", "Immediate specialist transfer; no authentication or account disclosure"),
        (8.45, 4.37, MUTED, "NON-FRAUD", "Polite boundary + team transfer offer; decline → one closing message"),
    ]
    for x, w, accent, title, body in cards:
        s.shape(x, 5.88, w, 0.80, fill=PANEL, line=LINE)
        s.shape(x, 5.88, 0.08, 0.80, fill=accent, line=accent, radius=False)
        s.text(x + 0.22, 6.03, w - 0.40, 0.19, title, size=8.7, color=accent, bold=True)
        s.text(x + 0.22, 6.28, w - 0.40, 0.25, body, size=8.7, color=WHITE)

    # Footer principle
    s.shape(0.5, 6.92, 12.32, 0.34, fill="102D37", line="1E5966")
    s.text(0.72, 6.95, 11.90, 0.27, "DESIGN PRINCIPLE   LLM = understand & converse     |     Code + tools = verify, decide & act     |     Two runnable scripts = explore + evaluate", size=9, color=CYAN, bold=True, align="ctr")
    return s


def package_pptx(slide_xml: str) -> None:
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>
<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>
<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
<p:sldSz cx="12191695" cy="6858000" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>'''
    presentation_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>
</Relationships>'''
    slide_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'''
    master = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/><p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'''
    master_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>'''
    layout = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'''
    layout_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>'''
    theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Fraud Agent"><a:themeElements><a:clrScheme name="Fraud Agent"><a:dk1><a:srgbClr val="09111F"/></a:dk1><a:lt1><a:srgbClr val="F7FAFC"/></a:lt1><a:dk2><a:srgbClr val="111D2E"/></a:dk2><a:lt2><a:srgbClr val="A8B4C7"/></a:lt2><a:accent1><a:srgbClr val="35C2E3"/></a:accent1><a:accent2><a:srgbClr val="5B8CFF"/></a:accent2><a:accent3><a:srgbClr val="39D98A"/></a:accent3><a:accent4><a:srgbClr val="FFB454"/></a:accent4><a:accent5><a:srgbClr val="FF6B6B"/></a:accent5><a:accent6><a:srgbClr val="A8B4C7"/></a:accent6><a:hlink><a:srgbClr val="35C2E3"/></a:hlink><a:folHlink><a:srgbClr val="5B8CFF"/></a:folHlink></a:clrScheme><a:fontScheme name="Arial"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Simple"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>'''
    core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Fraud Block Agent | End-to-End Design</dc:title><dc:subject>Agentic system architecture</dc:subject><dc:creator>OpenAI Codex</dc:creator><cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">2026-08-06T00:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-08-06T00:00:00Z</dcterms:modified></cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft Office PowerPoint</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>1</Slides><Notes>0</Notes><HiddenSlides>0</HiddenSlides><Company></Company><AppVersion>16.0000</AppVersion></Properties>'''
    files = {
        "[Content_Types].xml": content_types,
        "_rels/.rels": root_rels,
        "docProps/core.xml": core,
        "docProps/app.xml": app,
        "ppt/presentation.xml": presentation,
        "ppt/_rels/presentation.xml.rels": presentation_rels,
        "ppt/slides/slide1.xml": slide_xml,
        "ppt/slides/_rels/slide1.xml.rels": slide_rels,
        "ppt/slideMasters/slideMaster1.xml": master,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": master_rels,
        "ppt/slideLayouts/slideLayout1.xml": layout,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": layout_rels,
        "ppt/theme/theme1.xml": theme,
        "ppt/presProps.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentationPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>',
        "ppt/viewProps.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:viewPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:normalViewPr/><p:slideViewPr><p:cSldViewPr><p:cViewPr varScale="1"><p:scale><a:sx n="100" d="100"/><a:sy n="100" d="100"/></p:scale><p:origin x="0" y="0"/></p:cViewPr><p:guideLst/></p:cSldViewPr></p:slideViewPr><p:notesTextViewPr><p:cViewPr><p:scale><a:sx n="100" d="100"/><a:sy n="100" d="100"/></p:scale><p:origin x="0" y="0"/></p:cViewPr></p:notesTextViewPr><p:gridSpacing cx="72008" cy="72008"/></p:viewPr>',
        "ppt/tableStyles.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>',
    }
    with ZipFile(PPTX_PATH, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_preview() -> None:
    scale = 144
    image = Image.new("RGB", (round(SLIDE_W * scale), round(SLIDE_H * scale)), rgb(BG))
    draw = ImageDraw.Draw(image)

    def box(x: float, y: float, w: float, h: float, fill: str, outline: str = LINE, radius: int = 12) -> None:
        draw.rounded_rectangle((x * scale, y * scale, (x + w) * scale, (y + h) * scale), radius=radius, fill=rgb(fill), outline=rgb(outline), width=2)

    def txt(x: float, y: float, value: str, size: int, color: str = WHITE, bold: bool = False, anchor: str | None = None) -> None:
        draw.multiline_text((x * scale, y * scale), value, font=font(size, bold=bold), fill=rgb(color), spacing=5, anchor=anchor)

    txt(0.5, 0.28, "Fraud Block Agent | End-to-End Design", 36, bold=True)
    txt(0.5, 0.80, "DeepSeek interprets every customer message; deterministic controls protect decisions and actions.", 16, MUTED)
    box(10.45, 0.38, 2.36, 0.28, CYAN, CYAN, 16)
    txt(11.63, 0.52, "BEGINNER-FRIENDLY  •  REPRODUCIBLE", 11, BG, True, "mm")
    draw.line((0.5 * scale, 1.15 * scale, 12.82 * scale, 1.15 * scale), fill=rgb(LINE), width=2)

    box(0.5, 1.42, 1.45, 3.82, PANEL)
    draw.ellipse((0.93 * scale, 1.75 * scale, 1.51 * scale, 2.33 * scale), fill=rgb(BLUE))
    txt(1.22, 2.04, "C", 25, WHITE, True, "mm")
    txt(1.22, 2.63, "CUSTOMER", 13, CYAN, True, "mm")
    txt(1.22, 3.13, "Streamlit chat\nCLI explorer", 17, WHITE, True, "mm")
    txt(1.22, 4.18, "Free-form\nnatural language", 13, MUTED, False, "mm")
    txt(1.22, 4.80, "Every turn → LLM", 12, GREEN, True, "mm")

    stage_specs = [(2.25, 2.18, CYAN, "01  UNDERSTAND"), (4.73, 2.28, BLUE, "02  ROUTE"), (7.31, 2.72, GREEN, "03  ACT")]
    for x, w, accent, label in stage_specs:
        box(x, 1.42, w, 3.82, PANEL)
        pill_w = 0.72 if x == 2.25 else 0.59 if x == 4.73 else 0.52
        box(x + 0.25, 1.66, pill_w, 0.28, accent, accent, 14)
        txt(x + 0.25 + pill_w / 2, 1.80, label, 10, BG, True, "mm")
    for x1, x2, color in [(1.95, 2.22, CYAN), (4.43, 4.70, CYAN), (7.01, 7.28, GREEN)]:
        draw.line((x1 * scale, 3.28 * scale, x2 * scale, 3.28 * scale), fill=rgb(color), width=5)
        draw.polygon(((x2 * scale, 3.28 * scale), ((x2 - 0.08) * scale, 3.23 * scale), ((x2 - 0.08) * scale, 3.33 * scale)), fill=rgb(color))

    txt(2.50, 2.10, "DeepSeek API", 24, WHITE, True)
    txt(2.50, 2.55, "Interprets intent\nWrites human response\nEmits structured JSON", 15, MUTED)
    draw.line((2.50 * scale, 3.52 * scale, 4.15 * scale, 3.52 * scale), fill=rgb(LINE), width=2)
    txt(2.50, 3.70, "Handles topic switches\nand natural replies", 15, WHITE, True)
    box(2.50, 4.55, 1.66, 0.42, "102D37", "1E5966")
    txt(3.33, 4.76, "≤ 3 clarification turns", 12, CYAN, True, "mm")

    txt(4.98, 2.10, "Python orchestrator", 21, WHITE, True)
    txt(4.98, 2.49, "Consumes the JSON instruction", 13, MUTED)
    route_data = [(3.00, "173B31", GREEN, "Remove block"), (3.61, "3A2B1A", ORANGE, "Suspected fraud"), (4.22, "202B3C", MUTED, "Non-fraud")]
    for yy, fill, accent, label in route_data:
        box(4.98, yy, 1.78, 0.47, fill)
        draw.ellipse((5.12 * scale, (yy + 0.13) * scale, 5.30 * scale, (yy + 0.31) * scale), fill=rgb(accent))
        txt(5.42, yy + 0.12, label, 15, WHITE, True)

    txt(7.56, 2.10, "Protected removal path", 21, WHITE, True)
    labels = ["Authenticate full card + DOB", "Match customer and card", "Confirm latest transaction only", "Check removal eligibility", "Remove fraud block", "Verify final card status"]
    for idx, label in enumerate(labels):
        yy = 2.57 + idx * 0.40
        draw.ellipse((7.57 * scale, yy * scale, 7.81 * scale, (yy + 0.24) * scale), fill=rgb("173B31"), outline=rgb("28664F"))
        txt(7.69, yy + 0.12, str(idx + 1), 11, GREEN, True, "mm")
        txt(7.91, yy + 0.03, label, 13, WHITE, idx in {0, 2, 5})

    for y, h, heading, accent, title, body in [
        (1.42, 1.79, "SAFETY BOUNDARY", CYAN, "LLM does not approve\nor execute bank actions", "Tools enforce identity, ownership,\neligibility and final-state checks."),
        (3.44, 1.80, "EVALUATION HARNESS", GREEN, "10 deterministic scenarios", "Outcome  •  trajectory\nSafety gates  •  efficiency"),
    ]:
        box(10.29, y, 2.53, h, PANEL_2, "335071")
        txt(10.55, y + 0.26, heading, 13, accent, True)
        txt(10.55, y + 0.64, title, 17, WHITE, True)
        txt(10.55, y + 1.16, body, 12, MUTED)
    txt(10.55, 4.98, "Catches hidden workflow failures", 11, ORANGE, True)

    txt(0.5, 5.55, "ROUTING OUTCOMES", 12, MUTED, True)
    cards = [(0.50, 3.82, GREEN, "BLOCK REMOVAL", "Authenticate → verify latest transaction → remove → confirm active"), (4.50, 3.78, ORANGE, "SUSPECTED FRAUD", "Immediate specialist transfer; no authentication or account disclosure"), (8.45, 4.37, MUTED, "NON-FRAUD", "Polite boundary + team transfer offer; decline → one closing message")]
    for x, w, accent, title, body in cards:
        box(x, 5.88, w, 0.80, PANEL)
        draw.rectangle((x * scale, 5.88 * scale, (x + 0.08) * scale, 6.68 * scale), fill=rgb(accent))
        txt(x + 0.22, 6.03, title, 12, accent, True)
        txt(x + 0.22, 6.30, body, 11, WHITE)

    box(0.5, 6.92, 12.32, 0.34, "102D37", "1E5966", 14)
    txt(6.66, 7.09, "DESIGN PRINCIPLE   LLM = understand & converse     |     Code + tools = verify, decide & act     |     Two runnable scripts = explore + evaluate", 12, CYAN, True, "mm")
    image.save(PREVIEW_PATH)


def main() -> None:
    ensure_artifact_dirs()
    slide = build_slide()
    package_pptx(slide.xml())
    build_preview()
    print(PPTX_PATH)
    print(PREVIEW_PATH)


if __name__ == "__main__":
    main()
