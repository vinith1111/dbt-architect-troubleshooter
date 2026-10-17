"""Typed contracts for deterministic diagnostics."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class DiagnosticInput:
    """Evidence supplied by parsers, dbt artifacts, logs, or a user."""
    error_code: str | None = None
    message: str = ""
    file_path: str | None = None
    project_files: tuple[str, ...] = ()
    failed_test_name: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosticFinding:
    """A rule-backed finding with verifiable next steps."""
    rule_id: str
    title: str
    category: str
    severity: Severity
    diagnosis: str
    explanation: str
    recommended_fix: str
    validation_steps: tuple[str, ...]
    prevention: str
    evidence: tuple[str, ...]
    confidence: str = "high"
