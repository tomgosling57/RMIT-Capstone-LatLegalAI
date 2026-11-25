from typing import List, Dict, Any

from sklearn.metrics import precision_score, recall_score, f1_score
from jiwer import wer


def calculate_wer(expected: str, actual: str) -> float:
    """
    Calculate the Word Error Rate (WER) between an expected (reference)
    and an actual (hypothesis) transcription.

    WER is computed as:
        WER = (S + D + I) / N
    where:
        S = number of substitutions
        D = number of deletions
        I = number of insertions
        N = number of words in the reference (expected) text

    Parameters
    ----------
    expected : str
        The reference (ground-truth) transcription.
    actual : str
        The hypothesis (system output) transcription.

    Returns
    -------
    float
        The Word Error Rate. A value of 0.0 indicates a perfect match;
        values greater than 0.0 indicate increasing divergence. The value
        can exceed 1.0 in cases where insertions dominate.
    """
    return wer(expected, actual)


def per_label_metrics(
    y_true: List[Dict[str, int]], y_pred: List[Dict[str, int]], labels: List[str]
) -> tuple[Dict[str, Dict[str, float]], float]:
    results: Dict[str, Dict[str, float]] = {}

    for label in labels:
        y_t = [t[label] for t in y_true]
        y_p = [p[label] for p in y_pred]

        results[label] = {
            "precision": precision_score(y_t, y_p, zero_division=0),
            "recall": recall_score(y_t, y_p, zero_division=0),
            "f1": f1_score(y_t, y_p, zero_division=0),
        }

    macro_f1 = sum(results[label]["f1"] for label in labels) / len(labels)

    return results, macro_f1


def exact_match_accuracy(y_true: List[Any], y_pred: List[Any]) -> float:
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)
