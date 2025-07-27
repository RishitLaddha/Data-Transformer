"""
Agent 3 executor

• For PIVOTED / UNPIVOTED sheets: executes Gemini‑generated code.
• For MULTIHEADER sheets: bypasses LLM code entirely and calls
  convert_multi_to_long() from agent4_code.py.
"""

import pandas as pd
import traceback
from typing import Optional


def run_agent3_and_save_output(
    code_str: str,
    output_path: str,
    path: str,
    format_classification: str = "",
) -> str:
    """
    Execute LLM‑generated code or direct multi‑header logic, then save to Excel.

    Parameters
    ----------
    code_str : str
        The Python code block produced by Agent 2 or 4.
    output_path : str
        Where to save the resulting Excel file.
    path : str
        Original input Excel file (needed for execution env).
    format_classification : str, optional
        One of {"PIVOTED", "UNPIVOTED", "MULTIHEADER"}.

    Returns
    -------
    str
        "SUCCESS" or an error message prefixed with "ERROR:".
    """
    # ──────────────────────────────────────────────
    # Fast‑path: MULTIHEADER -> call local converter
    # ──────────────────────────────────────────────
    if format_classification.upper() == "MULTIHEADER":
        try:
            from agent4_code import convert_multi_to_long

            convert_multi_to_long(path, output_path)
            return "SUCCESS"
        except Exception:
            return (
                "ERROR: Exception during multi‑header transformation:\n"
                + traceback.format_exc()
            )

    # ──────────────────────────────────────────────
    # Otherwise run the Gemini‑generated code
    # ──────────────────────────────────────────────
    try:
        exec_globals = {
            "__builtins__": __builtins__,
            "pd": pd,
            "path": path,
            "format_classification": format_classification,
        }
        exec_locals: Optional[dict] = {}

        exec(code_str, exec_globals, exec_locals)

        # Retrieve DataFrame named output_df
        output_df = exec_globals.get("output_df") or exec_locals.get("output_df")
        if output_df is None:
            return "ERROR: output_df not found in executed code."
        if not isinstance(output_df, pd.DataFrame):
            return "ERROR: output_df is not a DataFrame."

        output_df.to_excel(output_path, index=True)
        return "SUCCESS"

    except Exception:
        return "ERROR: Exception during execution:\n" + traceback.format_exc()
