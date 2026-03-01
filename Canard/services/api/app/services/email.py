# pyright: basic, reportMissingImports=false
"""Post-call test results email via Resend."""
from __future__ import annotations

import logging
from html import escape

import resend

from app.config import settings

LOGGER = logging.getLogger(__name__)


def _risk_color(score: int) -> str:
    if score >= 70:
        return "#ef4444"  # red
    if score >= 40:
        return "#f59e0b"  # amber
    return "#22c55e"  # green


def _compliance_label(compliance: str) -> tuple[str, str]:
    """Return (label, color) for compliance status."""
    if compliance in ("full_compliance", "significant_compliance", "failed"):
        return "Failed", "#ef4444"
    if compliance in ("partial_compliance", "partial"):
        return "Partial", "#f59e0b"
    if compliance in ("strong_resistance", "moderate_resistance", "passed"):
        return "Passed", "#22c55e"
    return "Partial", "#f59e0b"


def _build_flags_html(flags: list[str]) -> str:
    if not flags:
        return ""
    items = "".join(
        f'<span style="display:inline-block;background:#f4f4f5;border-radius:4px;'
        f'padding:4px 10px;margin:2px 4px 2px 0;font-size:12px;color:#252a39;">'
        f"{escape(f)}</span>"
        for f in flags
    )
    return (
        '<tr><td style="padding:16px 32px 0;">'
        '<p style="margin:0 0 8px;font-size:13px;font-weight:500;color:#252a39;">Flags</p>'
        f'<div style="line-height:2;">{items}</div>'
        "</td></tr>"
    )


def _build_transcript_html(transcript: str) -> str:
    if not transcript:
        return ""
    # Escape and convert newlines
    safe = escape(transcript).replace("\n", "<br/>")
    return (
        '<tr><td style="padding:16px 32px 0;">'
        '<p style="margin:0 0 8px;font-size:13px;font-weight:500;color:#252a39;">Call Transcript</p>'
        f'<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;'
        f'padding:16px;font-size:12px;color:#374151;line-height:1.6;max-height:400px;overflow-y:auto;">'
        f"{safe}</div>"
        "</td></tr>"
    )


def build_results_email(
    employee_name: str,
    risk_score: int,
    compliance: str,
    ai_summary: str,
    flags: list[str],
    transcript: str,
    campaign_name: str = "",
) -> str:
    """Build the HTML email body for post-call test results."""
    comp_label, comp_color = _compliance_label(compliance)
    risk_clr = _risk_color(risk_score)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Security Test Results</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:'Montserrat',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f4f4f4;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background-color:#ffffff;border-radius:14px;border:1px solid rgba(37,42,57,0.1);box-shadow:0 10px 30px rgba(37,42,57,0.05);overflow:hidden;">

          <!-- Logo -->
          <tr>
            <td align="center" style="padding:40px 32px 24px;">
              <img src="https://aokqnrsadixfgksetykj.supabase.co/storage/v1/object/public/assets/logo.png" alt="Canard Security" width="240" style="display:block;height:auto;" />
            </td>
          </tr>

          <!-- Heading -->
          <tr>
            <td align="center" style="padding:0 32px;">
              <h1 style="margin:0 0 8px;font-size:20px;font-weight:500;color:#252a39;line-height:1.4;">
                Security Awareness Test Results
              </h1>
              <p style="margin:0 0 24px;font-size:14px;color:#717182;line-height:1.6;">
                Hi {escape(employee_name)}, here are your results from a recent vishing simulation{(' — <strong>' + escape(campaign_name) + '</strong>') if campaign_name else ''}.
              </p>
            </td>
          </tr>

          <!-- Score Card -->
          <tr>
            <td style="padding:0 32px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
                <tr>
                  <td align="center" style="padding:24px 16px;background:#fafafa;width:50%;border-right:1px solid #e5e7eb;">
                    <p style="margin:0 0 4px;font-size:12px;color:#717182;">Risk Score</p>
                    <p style="margin:0;font-size:32px;font-weight:600;color:{risk_clr};">{risk_score}</p>
                    <p style="margin:4px 0 0;font-size:11px;color:#717182;">out of 100</p>
                  </td>
                  <td align="center" style="padding:24px 16px;background:#fafafa;width:50%;">
                    <p style="margin:0 0 4px;font-size:12px;color:#717182;">Compliance</p>
                    <p style="margin:0;font-size:24px;font-weight:600;color:{comp_color};">{comp_label}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- AI Summary -->
          <tr>
            <td style="padding:20px 32px 0;">
              <p style="margin:0 0 8px;font-size:13px;font-weight:500;color:#252a39;">Summary</p>
              <p style="margin:0;font-size:13px;color:#374151;line-height:1.6;">
                {escape(ai_summary or 'No summary available.')}
              </p>
            </td>
          </tr>

          <!-- Flags -->
          {_build_flags_html(flags)}

          <!-- Transcript -->
          {_build_transcript_html(transcript)}

          <!-- Tips -->
          <tr>
            <td style="padding:24px 32px 0;">
              <hr style="border:none;border-top:1px solid rgba(37,42,57,0.08);margin:0 0 20px;" />
              <p style="margin:0 0 8px;font-size:13px;font-weight:500;color:#252a39;">What to do next</p>
              <ul style="margin:0;padding:0 0 0 20px;font-size:13px;color:#374151;line-height:1.8;">
                <li>Never share passwords, MFA codes, or personal info over the phone</li>
                <li>Verify the caller by hanging up and calling back through official channels</li>
                <li>Report suspicious calls to your IT security team immediately</li>
              </ul>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding:32px 32px;border-top:1px solid rgba(37,42,57,0.08);margin-top:24px;">
              <p style="margin:0;font-size:12px;color:#717182;line-height:1.6;">
                Canard Security &copy; 2026
              </p>
              <p style="margin:4px 0 0;font-size:11px;color:#717182;line-height:1.6;">
                This is an automated security awareness report. If you have questions, contact your security team.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_test_results_email(
    to_email: str,
    employee_name: str,
    risk_score: int,
    compliance: str,
    ai_summary: str,
    flags: list[str],
    transcript: str,
    campaign_name: str = "",
) -> str | None:
    """Send post-call test results to an employee. Returns the email ID or None on failure."""
    if not settings.resend_api_key:
        LOGGER.warning("RESEND_API_KEY not set — skipping email to %s", to_email)
        return None

    resend.api_key = settings.resend_api_key

    html = build_results_email(
        employee_name=employee_name,
        risk_score=risk_score,
        compliance=compliance,
        ai_summary=ai_summary,
        flags=flags,
        transcript=transcript,
        campaign_name=campaign_name,
    )

    try:
        result = resend.Emails.send(
            {
                "from": settings.resend_from_email,
                "to": [to_email],
                "subject": f"Your Security Awareness Test Results — Score: {risk_score}/100",
                "html": html,
            }
        )
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        LOGGER.info("Test results email sent to %s (id=%s)", to_email, email_id)
        return email_id
    except Exception:
        LOGGER.exception("Failed to send test results email to %s", to_email)
        return None
