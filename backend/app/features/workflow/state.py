"""
Curato AI — Workflow State Machine

Defines workflow states and valid transitions.
"""

from enum import Enum


class WorkflowStatus(str, Enum):
    """All possible states for a generation workflow."""

    PENDING = "pending"
    RUNNING = "running"
    AGENT_EXECUTING = "agent_executing"
    AWAITING_APPROVAL = "awaiting_approval"
    REVISION_LOOP = "revision_loop"
    APPROVED = "approved"
    GENERATING_OUTPUT = "generating_output"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Valid state transitions
VALID_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.PENDING: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
    WorkflowStatus.RUNNING: {
        WorkflowStatus.AGENT_EXECUTING,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    },
    WorkflowStatus.AGENT_EXECUTING: {
        WorkflowStatus.RUNNING,
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    },
    WorkflowStatus.AWAITING_APPROVAL: {
        WorkflowStatus.APPROVED,
        WorkflowStatus.REVISION_LOOP,
        WorkflowStatus.FAILED,
    },
    WorkflowStatus.REVISION_LOOP: {
        WorkflowStatus.AGENT_EXECUTING,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    },
    WorkflowStatus.APPROVED: {
        WorkflowStatus.GENERATING_OUTPUT,
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
    },
    WorkflowStatus.GENERATING_OUTPUT: {
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
    },
    WorkflowStatus.COMPLETED: set(),  # Terminal state
    WorkflowStatus.FAILED: set(),  # Terminal state
    WorkflowStatus.CANCELLED: set(),  # Terminal state
}


def is_valid_transition(current: WorkflowStatus, target: WorkflowStatus) -> bool:
    """Check if a state transition is valid."""
    return target in VALID_TRANSITIONS.get(current, set())


def is_terminal(status: WorkflowStatus) -> bool:
    """Check if a status is a terminal (final) state."""
    return status in {
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.CANCELLED,
    }
