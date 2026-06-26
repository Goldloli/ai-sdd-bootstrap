"""
Evaluation Harness: {{TITLE}}

Purpose:
{{PURPOSE}}

Related spec: {{RELATED_SPEC}}

An Evaluation Harness fixes:
  - a task set (inputs and golden outputs)
  - a scoring function
  - a pass threshold

It differs from a unit harness: a unit harness asserts one invariant,
while an evaluation harness aggregates a score across many examples.
Use it for LLM / agent behaviour where correctness is statistical.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


# TODO: Replace this draft harness with real tasks and a real scorer.
#       It intentionally fails until you wire up real data.


@dataclass
class EvalCase:
    name: str
    input: dict
    expected: object
    # Optional per-case weight; defaults to 1.0 if omitted.
    weight: float = 1.0


@dataclass
class EvalResult:
    name: str
    passed: bool
    score: float
    detail: str = ""


def _run_subject(input: dict) -> object:
    """Call the system under test. Replace with the real entrypoint."""
    raise NotImplementedError("Wire this to the function / agent you are evaluating.")


def _score(output: object, expected: object) -> float:
    """Return a score in [0.0, 1.0]. 1.0 = perfect match."""
    raise NotImplementedError("Replace with a real scoring function (exact match, BLEU, etc.).")


CASES: List[EvalCase] = [
    EvalCase(name="example-1", input={}, expected=None),
    EvalCase(name="example-2", input={}, expected=None),
]

PASS_THRESHOLD = 0.8


def evaluate() -> List[EvalResult]:
    results: List[EvalResult] = []
    for case in CASES:
        try:
            output = _run_subject(case.input)
            score = _score(output, case.expected)
            results.append(
                EvalResult(
                    name=case.name,
                    passed=score >= PASS_THRESHOLD,
                    score=score,
                    detail=f"output={output!r}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - evaluation must not abort on one case
            results.append(EvalResult(name=case.name, passed=False, score=0.0, detail=str(exc)))
    return results


def test_{{SLUG}}_evaluation():
    """Run the full evaluation suite and assert the aggregate score clears the bar."""
    results = evaluate()
    total_weight = sum(c.weight for c in CASES) or 1.0
    aggregate = sum(r.score for r, c in zip(results, CASES)) / total_weight

    failures = [r for r in results if not r.passed]
    if aggregate < PASS_THRESHOLD or failures:
        detail = "\n".join(f"- {r.name}: score={r.score:.2f} {r.detail}" for r in failures)
        raise AssertionError(
            f"Evaluation below threshold {PASS_THRESHOLD}: aggregate={aggregate:.2f}\n{detail}"
        )
