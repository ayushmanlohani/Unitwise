"""
test_gate.py — Tier-2 regression tests from thin-eval failures.

These queries are related to the subject but NOT explicitly in the
syllabus, so the gate must return Tier-2 (False from
is_explicitly_in_syllabus) and the UI shows the disclaimer strip.
A single shared word (exact or plural) must not promote to Tier-1.
"""

from app.llm.checkquestion import is_explicitly_in_syllabus, is_in_syllabus


def test_dip_restoration_is_tier2(fake_syllabus):
    assert is_explicitly_in_syllabus(
        "Explain image restoration techniques", "DIP"
    ) is False


def test_eml_confusion_matrix_is_tier2(fake_syllabus):
    assert is_explicitly_in_syllabus(
        "Explain the confusion matrix for classification", "EML"
    ) is False


def test_cn_nat_is_tier2(fake_syllabus):
    assert is_explicitly_in_syllabus(
        "Explain network address translation", "CN"
    ) is False


def test_typo_with_context_stays_tier1(fake_syllabus):
    """Two-signal typo query keeps Tier-1: aloha exact + protokols~protocols."""
    assert is_explicitly_in_syllabus("Explain ALOHA protokols work", "CN") is True


def test_typo_passes_bounce(fake_syllabus):
    """'overfiting' (missing t) must pass the bounce via typo tolerance."""
    assert is_in_syllabus("what is overfiting", "EML") is True


def test_typo_topic_no_warning(fake_syllabus):
    """Typo of a listed topic is Tier-1: no disclaimer strip."""
    assert is_explicitly_in_syllabus("what is overfiting", "EML") is True


def test_subject_abbr_no_warning(fake_syllabus):
    """'in ML' expands to 'machine learning': Tier-1, no strip."""
    assert is_explicitly_in_syllabus("What is overfitting in ML?", "EML") is True


def test_short_acronym_passes_bounce(fake_syllabus):
    """Single exact syllabus word like OSI must not bounce-block."""
    assert is_in_syllabus("What is OSI?", "CN") is True
    assert is_in_syllabus("Explain OSI", "CN") is True


def test_short_junk_still_blocked(fake_syllabus):
    """Single junk word must still bounce-block."""
    assert is_in_syllabus("pasta", "CN") is False
    assert is_in_syllabus("What is pasta?", "CN") is False


def test_repeated_letter_typo(fake_syllabus):
    """'fuzzzzy' (extra letters) is Tier-1 in SCT, no strip, no block."""
    assert is_in_syllabus("what is fuzzzzy set", "SCT") is True
    assert is_explicitly_in_syllabus("what is fuzzzzy set", "SCT") is True
