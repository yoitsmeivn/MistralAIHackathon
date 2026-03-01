# pyright: basic, reportMissingImports=false
"""Generate a PDF audit report and upload it to Supabase storage."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, cast

from fpdf import FPDF

from app.db.client import get_supabase

LOGGER = logging.getLogger(__name__)

_AUDITS_BUCKET = "audits"


def _ensure_audits_bucket() -> None:
    """Create the audits bucket if it doesn't exist."""
    try:
        get_supabase().storage.create_bucket(
            _AUDITS_BUCKET,
            options={"public": False},
        )
        LOGGER.info("Created Supabase storage bucket: %s", _AUDITS_BUCKET)
    except Exception:
        # Bucket likely already exists — ignore
        pass


def _risk_color(score: int) -> tuple[int, int, int]:
    if score >= 70:
        return (239, 68, 68)  # red
    if score >= 40:
        return (245, 158, 11)  # amber
    return (34, 197, 94)  # green


def _compliance_label(compliance: str) -> str:
    if compliance == "failed":
        return "Failed"
    if compliance == "partial":
        return "Partial"
    return "Passed"


def _safe_text(text: str) -> str:
    """Strip characters that fpdf2 can't encode in latin-1."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_audit_pdf(
    *,
    call_id: str,
    call_date: str,
    campaign_name: str,
    employee_name: str,
    department: str,
    job_title: str,
    risk_score: int,
    compliance: str,
    ai_summary: str,
    flags: list[str],
    transcript_json: list[dict],
) -> bytes:
    """Build a PDF audit report and return the raw bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Header ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(37, 42, 57)
    pdf.cell(0, 12, _safe_text("Canard Security — Audit Report"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Call metadata ──
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"Call ID: {call_id}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Date: {call_date}", new_x="LMARGIN", new_y="NEXT")
    if campaign_name:
        pdf.cell(0, 6, f"Campaign: {_safe_text(campaign_name)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Employee info ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(37, 42, 57)
    pdf.cell(0, 8, "Employee", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"Name: {_safe_text(employee_name)}", new_x="LMARGIN", new_y="NEXT")
    if department:
        pdf.cell(0, 6, f"Department: {_safe_text(department)}", new_x="LMARGIN", new_y="NEXT")
    if job_title:
        pdf.cell(0, 6, f"Job Title: {_safe_text(job_title)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Risk score ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(37, 42, 57)
    pdf.cell(40, 8, "Risk Score: ")
    r, g, b = _risk_color(risk_score)
    pdf.set_text_color(r, g, b)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"{risk_score}/100", new_x="LMARGIN", new_y="NEXT")

    # ── Compliance ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(37, 42, 57)
    pdf.cell(40, 8, "Compliance: ")
    pdf.set_font("Helvetica", "", 12)
    label = _compliance_label(compliance)
    if compliance == "failed":
        pdf.set_text_color(239, 68, 68)
    elif compliance == "partial":
        pdf.set_text_color(245, 158, 11)
    else:
        pdf.set_text_color(34, 197, 94)
    pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── AI Summary ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(37, 42, 57)
    pdf.cell(0, 8, "AI Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 5, _safe_text(ai_summary or "No summary available."))
    pdf.ln(4)

    # ── Flags ──
    if flags:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(37, 42, 57)
        pdf.cell(0, 8, "Flags", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        for flag in flags:
            pdf.cell(0, 6, f"  - {_safe_text(flag)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # ── Transcript ──
    if transcript_json:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(37, 42, 57)
        pdf.cell(0, 8, "Full Transcript", new_x="LMARGIN", new_y="NEXT")

        for turn in transcript_json:
            role = (turn.get("role") or "").upper()
            text = turn.get("redacted_text") or turn.get("text") or ""
            timestamp = turn.get("timestamp_utc") or ""

            # Role label (bold)
            pdf.set_font("Helvetica", "B", 9)
            if role == "AGENT":
                pdf.set_text_color(37, 42, 57)
            else:
                pdf.set_text_color(80, 80, 80)
            label = f"[{role}]"
            if timestamp:
                label += f"  {timestamp}"
            pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")

            # Turn text
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(55, 65, 81)
            pdf.multi_cell(0, 4.5, _safe_text(text))
            pdf.ln(2)

    # ── Footer line ──
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(113, 113, 130)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    pdf.cell(0, 5, f"Generated by Canard Security on {now_str}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


def upload_audit_pdf(call_id: str, pdf_bytes: bytes) -> str | None:
    """Upload PDF to Supabase audits bucket. Returns signed URL or None on failure."""
    try:
        _ensure_audits_bucket()
        path = f"{call_id}/report.pdf"
        get_supabase().storage.from_(_AUDITS_BUCKET).upload(
            path,
            pdf_bytes,
            cast(Any, {"content-type": "application/pdf", "upsert": "true"}),
        )
        # Create a signed URL valid for 10 years (effectively permanent)
        signed = get_supabase().storage.from_(_AUDITS_BUCKET).create_signed_url(
            path, 60 * 60 * 24 * 365 * 10
        )
        url = signed.get("signedURL") if isinstance(signed, dict) else None
        if url:
            LOGGER.info("Uploaded audit PDF for call %s: %s", call_id, url)
        else:
            LOGGER.warning("Audit PDF uploaded but no signed URL returned for call %s", call_id)
        return url
    except Exception:
        LOGGER.warning("Failed to upload audit PDF for call %s", call_id, exc_info=True)
        return None
