"""Package the two approved AI-evolution SVG pages into a PowerPoint deck."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from artifact_paths import DIAGRAMS, IMAGES, PRESENTATIONS, ensure_artifact_dirs


ROOT = Path(__file__).resolve().parent
TEMPLATE = PRESENTATIONS / "Fraud_Block_Agent_Design.pptx"
OUTPUT = PRESENTATIONS / "AI_Product_Evolution_and_Agentic_Transition.pptx"

SLIDES = [
    (
        DIAGRAMS / "ai_product_evolution_timeline_preview.svg",
        IMAGES / "ai_product_evolution_timeline_ppt.png",
    ),
    (
        DIAGRAMS / "from_chatgpt_to_codex_preview.svg",
        IMAGES / "from_chatgpt_to_codex_ppt.png",
    ),
]

SLIDE_W = 12191695
SLIDE_H = 6858000


def slide_xml(index: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
 xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main">
 <p:cSld name="AI Evolution Page {index}"><p:spTree>
  <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
  <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  <p:pic>
   <p:nvPicPr><p:cNvPr id="2" name="Approved slide visual {index}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
   <p:blipFill><a:blip r:embed="rId2"><a:extLst><a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}"><asvg:svgBlip r:embed="rId3"/></a:ext></a:extLst></a:blip><a:stretch><a:fillRect/></a:stretch></p:blipFill>
   <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:ln><a:noFill/></a:ln></p:spPr>
  </p:pic>
 </p:spTree></p:cSld>
 <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def slide_rels(index: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide{index}.png"/>
 <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide{index}.svg"/>
</Relationships>'''


def build() -> None:
    ensure_artifact_dirs()
    with ZipFile(TEMPLATE) as source:
        files = {name: source.read(name) for name in source.namelist()}

    content_types = files["[Content_Types].xml"].decode("utf-8")
    if 'Extension="svg"' not in content_types:
        content_types = content_types.replace(
            "</Types>",
            '<Default Extension="svg" ContentType="image/svg+xml"/></Types>',
        )
    if 'Extension="png"' not in content_types:
        content_types = content_types.replace(
            "</Types>",
            '<Default Extension="png" ContentType="image/png"/></Types>',
        )
    if 'PartName="/ppt/slides/slide2.xml"' not in content_types:
        content_types = content_types.replace(
            "</Types>",
            '<Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>',
        )
    files["[Content_Types].xml"] = content_types.encode("utf-8")

    presentation = files["ppt/presentation.xml"].decode("utf-8")
    presentation = presentation.replace(
        '<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>',
        '<p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId6"/></p:sldIdLst>',
    )
    files["ppt/presentation.xml"] = presentation.encode("utf-8")

    presentation_rels = files["ppt/_rels/presentation.xml.rels"].decode("utf-8")
    presentation_rels = presentation_rels.replace(
        "</Relationships>",
        '<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/></Relationships>',
    )
    files["ppt/_rels/presentation.xml.rels"] = presentation_rels.encode("utf-8")

    for index, (svg_path, png_path) in enumerate(SLIDES, start=1):
        files[f"ppt/slides/slide{index}.xml"] = slide_xml(index).encode("utf-8")
        files[f"ppt/slides/_rels/slide{index}.xml.rels"] = slide_rels(index).encode("utf-8")
        files[f"ppt/media/slide{index}.svg"] = svg_path.read_bytes()
        files[f"ppt/media/slide{index}.png"] = png_path.read_bytes()

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as target:
        for name, data in files.items():
            target.writestr(name, data)

    print(OUTPUT)


if __name__ == "__main__":
    build()
