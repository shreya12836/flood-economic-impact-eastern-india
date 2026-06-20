"""Shared reporting helpers for regression scripts and table builders."""
from __future__ import annotations

SIG_TO_STARS: dict[str, str] = {
    "p < 0.01": "***",
    "p < 0.05": "**",
    "p < 0.10": "*",
    "n.s.": "",
}


def significance_label(p: float) -> str:
    """Convert p-value to text label. Used in regression scripts."""
    if p < 0.01:
        return "p < 0.01"
    if p < 0.05:
        return "p < 0.05"
    if p < 0.10:
        return "p < 0.10"
    return "n.s."


def significance_stars(sig: str) -> str:
    """Convert text label to asterisk notation. Used in table builders."""
    return SIG_TO_STARS.get(str(sig).strip(), "")


def fmt_coef(coef: float, sig: str) -> str:
    return f"{coef:.3f}{significance_stars(sig)}"


def fmt_se(se: float) -> str:
    return f"({se:.3f})"
