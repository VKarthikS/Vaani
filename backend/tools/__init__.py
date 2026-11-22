"""Vaani tools (docs/CONTRACTS.md §2). Importing this package registers every tool."""

from backend.tools import areas, confirm, control, faq, hospitals, restaurants  # noqa: F401
from backend.tools.base import REGISTRY, ToolContext, ToolError, run_tool

__all__ = ["REGISTRY", "ToolContext", "ToolError", "run_tool"]
