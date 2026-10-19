"""Built-in deterministic diagnostic rules."""
from .common import COMMON_RULES as _COMMON_RULES
from .performance import performance_issue

COMMON_RULES = (*_COMMON_RULES, performance_issue)

__all__ = ["COMMON_RULES", "performance_issue"]
