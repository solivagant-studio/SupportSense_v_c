# PLAN TASK: 8 | STUDENT TASK PACK: Day 14 | EVIDENCE: TD-07
# WHERE: dashboard package entry point
# DO: expose the read-only view model without starting Streamlit on import.
from dashboard.app import build_view_model, render

__all__ = ["build_view_model", "render"]
