"""
Scenario Harness: {{TITLE}}

Purpose:
{{PURPOSE}}

Related spec: {{RELATED_SPEC}}

A Scenario Harness drives a full workflow end-to-end:
  - initial state
  - a sequence of user actions or external events
  - the expected trajectory (state transitions, emitted events)
  - forbidden side effects

Use it for agent / multi-step flows where correctness is about the
whole path, not a single input-output pair.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple


# TODO: Replace this draft harness with a real scenario.
#       It intentionally fails until you wire up real steps and assertions.


@dataclass
class Step:
    """One action in the scenario plus the state/event checks that follow it."""
    name: str
    action: Callable[["Context"], None]
    expect: Callable[["Context"], None] = lambda ctx: None
    forbid: Callable[["Context"], None] = lambda ctx: None


@dataclass
class Context:
    """Mutable scenario state. Fields are domain-specific."""
    state: Any = None
    emitted_events: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)


def _initial_context() -> Context:
    """Build the starting state for the scenario."""
    raise NotImplementedError("Return the real initial Context for this scenario.")


def _forbid_marker(ctx: Context) -> None:
    """Hook called after every step to assert nothing forbidden happened."""
    return None


# TODO: Replace these stubs with real scenario steps.
STEPS: List[Step] = [
    Step(
        name="step-1",
        action=lambda ctx: None,
        expect=lambda ctx: None,
        forbid=lambda ctx: None,
    ),
    Step(
        name="step-2",
        action=lambda ctx: None,
        expect=lambda ctx: None,
        forbid=lambda ctx: None,
    ),
]

# Whole-trajectory invariants checked once at the end.
TRAJECTORY_CHECKS: List[Callable[[Context], None]] = [
    lambda ctx: None,
]


def _run_step(ctx: Context, step: Step) -> None:
    step.action(ctx)
    step.expect(ctx)
    step.forbid(ctx)
    _forbid_marker(ctx)


def test_{{SLUG}}_scenario():
    """Drive the full scenario and assert the trajectory is as expected."""
    ctx = _initial_context()
    for step in STEPS:
        try:
            _run_step(ctx, step)
        except AssertionError:
            raise
        except Exception as exc:  # noqa: BLE001 - surface which step blew up
            raise AssertionError(f"Scenario failed at step '{step.name}': {exc}") from exc

    for check in TRAJECTORY_CHECKS:
        check(ctx)
