"""
conftest.py — Shared pytest fixtures for gate tests.

Gate tests must never read the real data/syllabus.yaml, so every test that
needs the syllabus gets a tiny fake one instead. The syllabus loader is
lru_cache'd, so the cache is cleared at both ends of each test.
"""

import sys
from pathlib import Path

import pytest
import yaml

# App modules import as "app.*", exactly like the server does from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm import checkquestion  # noqa: E402

# ---------------------------------------------------------------------------
# Minimal syllabus — same shape as data/syllabus.yaml, two subjects only
# ---------------------------------------------------------------------------
FAKE_SYLLABUS = {
    "subjects": [
        {
            "name": "Computer Network",
            "code": "NCS-601",
            "folder": "CN",
            "units": [
                {
                    "number": 1,
                    "title": "Introduction Concepts",
                    "topics": [
                        "Goals and applications of networks",
                        "OSI reference model and services",
                        "Network topology design",
                    ],
                },
                {
                    "number": 2,
                    "title": "Medium Access Sub Layer",
                    "topics": [
                        "LAN protocols - ALOHA protocols",
                        "Sliding window protocols",
                        "Physical address formats",
                    ],
                },
            ],
        },
        {
            "name": "Digital Image Processing",
            "code": "NCS-602",
            "folder": "DIP",
            "units": [
                {
                    "number": 1,
                    "title": "Fundamentals",
                    "topics": [
                        "Image sampling and quantization",
                        "Review technique comparisons",
                    ],
                },
            ],
        },
        {
            "name": "Essentials of Machine Learning",
            "code": "NCS-603",
            "folder": "EML",
            "units": [
                {
                    "number": 1,
                    "title": "Supervised Learning",
                    "topics": [
                        "Classification accuracy basics",
                        "Regression models",
                        "Overfitting and underfitting",
                        "Machine Learning and Deep Learning",
                    ],
                },
            ],
        },
        {
            "name": "Soft Computing Techniques",
            "code": "NCS-605",
            "folder": "SCT",
            "units": [
                {
                    "number": 1,
                    "title": "Fuzzy Logic",
                    "topics": [
                        "Fuzzy sets and membership",
                        "Defuzzification methods",
                    ],
                },
            ],
        },
        {
            "name": "Quantum Computing",
            "code": "NCS-604",
            "folder": "QC",
            "units": [
                {
                    "number": 1,
                    "title": "Foundations",
                    "topics": [
                        "Qubits and superposition",
                        "Quantum entanglement",
                    ],
                },
            ],
        },
    ]
}


@pytest.fixture
def fake_syllabus(tmp_path, monkeypatch):
    """
    Point the gate at a temporary copy of FAKE_SYLLABUS.

    Yields the same dict so tests can assert against the exact topics in use.
    """
    syllabus_file = tmp_path / "syllabus.yaml"
    syllabus_file.write_text(yaml.safe_dump(FAKE_SYLLABUS), encoding="utf-8")

    checkquestion._load_subject_data.cache_clear()
    monkeypatch.setattr(checkquestion, "SYLLABUS_PATH", syllabus_file)

    yield FAKE_SYLLABUS

    checkquestion._load_subject_data.cache_clear()


@pytest.fixture
def academic_history():
    """
    Chat history whose last assistant turn is a real academic answer.

    Must be 150+ chars: _MIN_ACADEMIC_LENGTH filters shorter turns out of memory.
    """
    return [
        {"role": "user", "content": "Explain the OSI reference model"},
        {
            "role": "assistant",
            "content": (
                "The OSI reference model is a seven layer architecture that "
                "standardises how network protocols communicate. The layers are "
                "physical, data link, network, transport, session, presentation "
                "and application, and each layer offers services to the layer "
                "above it."
            ),
        },
    ]