"""Curated registry of popular community skills and plugins."""
from typing import Dict, Any, List, Optional

CURATED_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ponytail": {
        "name": "ponytail",
        "type": "plugin",
        "description": "Lazy senior dev mode: the smallest change that fully solves the task, plus review, audit, and debt harvester.",
        "source": "https://github.com/DietrichGebert/ponytail.git",
        "author": "Dietrich Gebert",
        "tags": ["coding", "review", "refactor", "plugin", "popular"],
    },
    "deep-research": {
        "name": "deep-research",
        "type": "skill",
        "description": "Rigorous multi-agent research pipeline for academic, scientific, and technical topic analysis.",
        "source": "https://github.com/google/deep-research.git",
        "author": "Community",
        "tags": ["research", "academic", "literature-review"],
    },
    "academic-paper": {
        "name": "academic-paper",
        "type": "skill",
        "description": "Academic manuscript drafting, structure calibration, citation checks, and LaTeX/Pandoc formatting.",
        "source": "https://github.com/academic-agent/academic-paper.git",
        "author": "Community",
        "tags": ["academic", "paper", "writing", "latex"],
    },
    "frontend-design": {
        "name": "frontend-design",
        "type": "skill",
        "description": "Build distinctive, production-grade frontend interfaces with high aesthetic quality without generic AI cliches.",
        "source": "https://github.com/agent-skills/frontend-design.git",
        "author": "Design Collective",
        "tags": ["frontend", "ui", "design", "css", "react"],
    },
    "threejs-essentials": {
        "name": "threejs-essentials",
        "type": "skill",
        "description": "Modern Three.js (r160+) WebGL design patterns, PBR lighting, animation loops, and memory cleanup.",
        "source": "https://github.com/agent-skills/threejs-essentials.git",
        "author": "WebGL Guild",
        "tags": ["threejs", "3d", "webgl", "graphics"],
    },
    "mediapipe-vision": {
        "name": "mediapipe-vision",
        "type": "skill",
        "description": "Webcam computer vision tracking using MediaPipe Tasks Vision (HandLandmarker, PoseLandmarker, FaceLandmarker).",
        "source": "https://github.com/agent-skills/mediapipe-vision.git",
        "author": "Vision Agents",
        "tags": ["vision", "mediapipe", "ai", "tracking"],
    },
    "vfx-mcp": {
        "name": "vfx-mcp",
        "type": "skill",
        "description": "Video processing, editing, filtering, green-screen compositing, and audio mixing with ffmpeg.",
        "source": "https://github.com/agent-skills/vfx-mcp.git",
        "author": "VFX Tools",
        "tags": ["video", "ffmpeg", "vfx", "multimedia"],
    },
}


def find_in_curated(query: str) -> List[Dict[str, Any]]:
    """Search the curated catalogue by query (matches name, description, tags)."""
    q = query.lower().strip()
    results = []
    for item in CURATED_REGISTRY.values():
        if (
            q in item["name"].lower()
            or q in item["description"].lower()
            or any(q in tag.lower() for tag in item.get("tags", []))
        ):
            results.append(item)
    return results


def get_curated_item(name: str) -> Optional[Dict[str, Any]]:
    return CURATED_REGISTRY.get(name.lower().strip())
