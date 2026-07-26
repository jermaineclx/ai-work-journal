from app.domain.enums import DecisionAction
from app.domain.rules.decision import TaskMatchCandidate, decide

THRESHOLDS = {"auto_apply_threshold": 0.95, "confirm_threshold": 0.80}


def test_high_confidence_existing_match_auto_saves():
    best = TaskMatchCandidate(task_id="T001", title="Settlement Reconciliation", similarity=0.97)
    decision = decide(confidence=0.97, best_match=best, candidates=[best], **THRESHOLDS)
    assert decision.action == DecisionAction.AUTO_SAVE_EXISTING_TASK
    assert decision.matched_task_id == "T001"


def test_medium_confidence_existing_match_requires_confirmation():
    best = TaskMatchCandidate(task_id="T001", title="Settlement Reconciliation", similarity=0.85)
    decision = decide(confidence=0.85, best_match=best, candidates=[best], **THRESHOLDS)
    assert decision.action == DecisionAction.CONFIRM_EXISTING_TASK
    assert decision.matched_task_id == "T001"


def test_low_confidence_existing_match_asks_for_clarification():
    best = TaskMatchCandidate(task_id="T001", title="Settlement Reconciliation", similarity=0.5)
    candidates = [
        best,
        TaskMatchCandidate(task_id="T002", title="AUM Dashboard", similarity=0.48),
    ]
    decision = decide(confidence=0.5, best_match=best, candidates=candidates, **THRESHOLDS)
    assert decision.action == DecisionAction.ASK_CLARIFICATION
    assert decision.matched_task_id is None
    assert decision.candidates == candidates


def test_no_match_high_extraction_confidence_confirms_new_task():
    decision = decide(confidence=0.9, best_match=None, candidates=[], **THRESHOLDS)
    assert decision.action == DecisionAction.CONFIRM_NEW_TASK
    assert decision.matched_task_id is None


def test_no_match_low_extraction_confidence_asks_for_clarification():
    decision = decide(confidence=0.4, best_match=None, candidates=[], **THRESHOLDS)
    assert decision.action == DecisionAction.ASK_CLARIFICATION


def test_new_task_is_never_auto_saved_regardless_of_confidence():
    """Creating a new persistent workstream is higher-stakes than
    appending to an existing one, so it always requires confirmation,
    even at near-100% extraction confidence."""
    decision = decide(confidence=0.999, best_match=None, candidates=[], **THRESHOLDS)
    assert decision.action == DecisionAction.CONFIRM_NEW_TASK
