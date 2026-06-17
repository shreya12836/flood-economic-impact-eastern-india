from __future__ import annotations

# ── Type alias ────────────────────────────────────────────────────────────────
Icon = str  # Bootstrap Icons class name, e.g. "bar-chart-line" (from utils/icons.py)

# ── Color tokens ──────────────────────────────────────────────────────────────
BG_CARD    = "#1a2332"
BG_ICON    = "#1e3a5f"
BG_CHIP    = "#1e2d3d"
ACCENT_BAR = "#2c6fad"

TEXT_PRIMARY = "#ffffff"
TEXT_BODY    = "#e8e8e8"
TEXT_ACCENT  = "#90b8d4"
TEXT_MUTED   = "#7a9bb5"

# ── Dimension tokens ──────────────────────────────────────────────────────────
CARD_RADIUS = "12px"
CHIP_RADIUS = "16px"
ICON_SM     = "40px"   # finding / metadata icon circles
ICON_LG     = "50px"   # KPI icon circles
ICON_FS_SM  = "18px"   # font-size inside ICON_SM circle
ICON_FS_LG  = "22px"   # font-size inside ICON_LG circle
KPI_MIN_H   = "88px"   # equalises KPI card heights across columns
META_MIN_H  = "160px"  # equalises metadata card heights across columns

# ── CDN injection ─────────────────────────────────────────────────────────────
_BI_CDN = (
    '<link rel="stylesheet" href="'
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
    '">'
)


def inject_bootstrap_icons() -> None:
    import streamlit as st
    st.markdown(_BI_CDN, unsafe_allow_html=True)


# ── Private render helper ─────────────────────────────────────────────────────
def _bi(name: str, size: str = "18px") -> str:
    return f'<i class="bi bi-{name}" style="font-size:{size}"></i>'


# ── Builder functions ─────────────────────────────────────────────────────────
def _icon_circle(icon: Icon, size: str, fs: str) -> str:
    return (
        f'<span style="background:{BG_ICON};border-radius:50%;min-width:{size};'
        f'height:{size};display:flex;align-items:center;justify-content:center;'
        f'color:{TEXT_ACCENT};flex-shrink:0">{_bi(icon, fs)}</span>'
    )


def chip(icon: Icon, label: str) -> str:
    return (
        f'<span style="background:{BG_CHIP};border-radius:{CHIP_RADIUS};'
        f'padding:5px 14px;font-size:13px;color:{TEXT_ACCENT};display:inline-flex;'
        f'align-items:center;gap:6px;margin:0 6px 4px 0">'
        f"{_bi(icon)}<span>{label}</span></span>"
    )


def chip_row(tags: list[tuple[Icon, str]]) -> str:
    return (
        f'<div style="margin:8px 0 16px;display:flex;flex-wrap:wrap">'
        f'{"".join(chip(i, l) for i, l in tags)}</div>'
    )


def kpi_card(icon: Icon, value: object, label: str) -> str:
    return (
        f'<div style="background:{BG_CARD};border-radius:{CARD_RADIUS};'
        f'padding:20px 18px;display:flex;align-items:center;gap:16px;'
        f'min-height:{KPI_MIN_H};overflow:hidden">'
        f"{_icon_circle(icon, ICON_LG, ICON_FS_LG)}"
        f'<div style="min-width:0">'
        f'<div style="font-size:26px;font-weight:700;color:{TEXT_PRIMARY};'
        f'line-height:1.1;overflow-wrap:break-word">{value}</div>'
        f'<div style="font-size:12px;color:{TEXT_MUTED};margin-top:5px;'
        f'line-height:1.4;overflow-wrap:break-word">{label}</div>'
        f"</div></div>"
    )


def accent_header(text: str) -> str:
    return (
        f'<div style="border-left:3px solid {ACCENT_BAR};padding-left:10px;'
        f'margin-bottom:10px;font-size:17px;font-weight:600;color:{TEXT_BODY}">'
        f"{text}</div>"
    )


def finding_card(
    icon: Icon,
    label: str,
    coef_str: str,
    sig: str,
    interpretation: str,
) -> str:
    return (
        f'<div style="background:{BG_CARD};border-radius:10px;padding:14px 16px;'
        f'margin-bottom:10px;display:flex;gap:14px;align-items:flex-start">'
        f"{_icon_circle(icon, ICON_SM, ICON_FS_SM)}"
        f'<div style="min-width:0;overflow-wrap:break-word">'
        f'<div style="font-weight:600;color:{TEXT_BODY};margin-bottom:4px">{label}</div>'
        f'<div style="font-size:12px;color:{TEXT_ACCENT}">{coef_str} · {sig}</div>'
        f'<div style="font-size:12px;color:{TEXT_MUTED};margin-top:5px">'
        f"{interpretation}</div></div></div>"
    )


def finding_missing_card(label: str) -> str:
    return (
        f'<div style="background:{BG_CARD};border-radius:10px;padding:14px 16px;'
        f'margin-bottom:10px;opacity:0.5">'
        f'<div style="font-size:12px;color:{TEXT_MUTED};font-style:italic">'
        f"{label}: data not available — run regression pipeline first.</div></div>"
    )


def pooled_note_card(note: str) -> str:
    return (
        f'<div style="background:{BG_CARD};border-radius:10px;padding:14px 16px">'
        f'<div style="font-weight:600;color:{TEXT_BODY};margin-bottom:6px">Pooled Sample</div>'
        f'<div style="font-size:12px;color:{TEXT_MUTED};overflow-wrap:break-word">'
        f"{note}</div></div>"
    )


def meta_card(icon: Icon, header: str, items: list[str]) -> str:
    rows = "".join(
        f'<div style="font-size:12px;color:{TEXT_MUTED};padding:2px 0;'
        f'overflow-wrap:break-word">· {item}</div>'
        for item in items
    )
    return (
        f'<div style="background:{BG_CARD};border-radius:10px;padding:20px 18px;'
        f'min-height:{META_MIN_H}">'
        f'<div style="font-size:13px;font-weight:700;color:{TEXT_ACCENT};'
        f'margin-bottom:10px;display:flex;align-items:center;gap:8px">'
        f"{_bi(icon)}<span>{header}</span></div>"
        f"{rows}</div>"
    )
