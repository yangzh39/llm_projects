"""Central locations for generated, shareable project artifacts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
PRESENTATIONS = ARTIFACTS / "presentations"
IMAGES = ARTIFACTS / "images"
VIDEOS = ARTIFACTS / "videos"
DIAGRAMS = ARTIFACTS / "diagrams"


def ensure_artifact_dirs() -> None:
    for directory in (PRESENTATIONS, IMAGES, VIDEOS, DIAGRAMS):
        directory.mkdir(parents=True, exist_ok=True)
