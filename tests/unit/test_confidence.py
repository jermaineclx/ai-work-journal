import pytest

from app.domain.rules.confidence import ConfidenceTier, classify_confidence


@pytest.mark.parametrize(
    "confidence,expected",
    [
        (0.99, ConfidenceTier.AUTO_APPLY),
        (0.95, ConfidenceTier.AUTO_APPLY),
        (0.94, ConfidenceTier.CONFIRM),
        (0.80, ConfidenceTier.CONFIRM),
        (0.79, ConfidenceTier.CLARIFY),
        (0.0, ConfidenceTier.CLARIFY),
        (1.0, ConfidenceTier.AUTO_APPLY),
    ],
)
def test_classify_confidence_boundaries(confidence, expected):
    tier = classify_confidence(confidence, auto_apply_threshold=0.95, confirm_threshold=0.80)
    assert tier == expected


def test_classify_confidence_rejects_out_of_range():
    with pytest.raises(ValueError):
        classify_confidence(1.5, auto_apply_threshold=0.95, confirm_threshold=0.80)
    with pytest.raises(ValueError):
        classify_confidence(-0.1, auto_apply_threshold=0.95, confirm_threshold=0.80)


def test_classify_confidence_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        classify_confidence(0.9, auto_apply_threshold=0.7, confirm_threshold=0.8)
