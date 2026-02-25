"""HTML email builder and sender via Resend."""

import resend
from datetime import datetime

from . import config


def _score_bar(score: float, max_score: float = 10.0) -> str:
    """Generate an inline HTML score bar."""
    pct = min(100, (score / max_score) * 100)
    color = "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
    return (
        f'<div style="background:#e5e7eb;border-radius:4px;height:8px;width:80px;display:inline-block;vertical-align:middle;">'
        f'<div style="background:{color};border-radius:4px;height:8px;width:{pct}%;"></div>'
        f'</div>'
        f' <span style="font-size:12px;color:#6b7280;">{score:.1f}</span>'
    )


def _priority_badge(company: str) -> str:
    """Return a badge if the company is on the priority list."""
    company_lower = company.lower()
    for p in config.PRIORITIZE_COMPANIES:
        if p.lower() in company_lower:
            return ' <span style="background:#dbeafe;color:#1d4ed8;font-size:10px;padding:2px 6px;border-radius:3px;font-weight:600;">PRIORITY</span>'
    return ""


def _build_job_card(job: dict, rank: int) -> str:
    """Build an HTML card for a single job listing."""
    scores = job.get("scores", {})
    overall = scores.get("overall", 0)
    one_liner = scores.get("one_liner", "")
    title_fit = scores.get("title_fit", 0)
    industry_fit = scores.get("industry_fit", 0)
    skill_match = scores.get("skill_match", 0)
    company_prestige = scores.get("company_prestige", 0)

    # Border color based on overall score
    border_color = "#22c55e" if overall >= 7 else "#f59e0b" if overall >= 5 else "#e5e7eb"

    url = job.get("url", "")
    apply_link = f'<a href="{url}" style="color:#2563eb;text-decoration:none;font-size:13px;">Apply &rarr;</a>' if url else ""

    salary = job.get("salary", "")
    salary_html = f'<span style="color:#059669;font-weight:600;">{salary}</span>' if salary else '<span style="color:#9ca3af;">Salary not listed</span>'

    via = job.get("via", "")
    via_html = f' <span style="color:#9ca3af;font-size:11px;">via {via}</span>' if via else ""

    return f"""
    <div style="border:1px solid {border_color};border-left:4px solid {border_color};border-radius:8px;padding:16px;margin-bottom:12px;background:#ffffff;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div style="font-size:11px;color:#9ca3af;font-weight:600;">#{rank}</div>
          <div style="font-size:16px;font-weight:700;color:#111827;margin:2px 0;">
            {job['title']}{_priority_badge(job.get('company', ''))}
          </div>
          <div style="font-size:14px;color:#4b5563;">
            {job['company']}{via_html}
          </div>
          <div style="font-size:13px;color:#6b7280;margin-top:2px;">
            {job.get('location', 'Location not specified')} &middot; {salary_html}
          </div>
        </div>
        <div style="text-align:right;min-width:60px;">
          <div style="font-size:28px;font-weight:800;color:{border_color};">{overall:.0f}</div>
          <div style="font-size:10px;color:#9ca3af;">/ 10</div>
        </div>
      </div>

      <div style="margin-top:10px;font-size:13px;color:#374151;font-style:italic;border-left:3px solid #e5e7eb;padding-left:10px;">
        {one_liner}
      </div>

      <div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:12px;color:#6b7280;">
        <div>Title Fit: {_score_bar(title_fit)}</div>
        <div>Industry: {_score_bar(industry_fit)}</div>
        <div>Skills: {_score_bar(skill_match)}</div>
        <div>Company: {_score_bar(company_prestige)}</div>
      </div>

      <div style="margin-top:10px;font-size:12px;color:#6b7280;">
        {job.get('description', '')[:300]}{'...' if len(job.get('description', '')) > 300 else ''}
      </div>

      <div style="margin-top:10px;">
        {apply_link}
      </div>
    </div>
    """


def build_email_html(jobs: list[dict]) -> str:
    """Build the full HTML email digest."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    job_count = len(jobs)

    # Summary stats
    high_score = len([j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7])
    priority_count = sum(
        1 for j in jobs
        if any(p.lower() in j.get("company", "").lower() for p in config.PRIORITIZE_COMPANIES)
    )

    if not jobs:
        cards_html = """
        <div style="text-align:center;padding:40px;color:#9ca3af;">
          <div style="font-size:48px;">&#128269;</div>
          <div style="font-size:16px;margin-top:12px;">No new matching jobs found today.</div>
          <div style="font-size:13px;margin-top:4px;">The agent searched for Partner, VP, CIO, and MD roles in Chicago + remote.</div>
        </div>
        """
    else:
        cards_html = "\n".join(_build_job_card(job, i + 1) for i, job in enumerate(jobs))

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
      <div style="max-width:640px;margin:0 auto;padding:20px;">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:12px;padding:24px;color:#ffffff;margin-bottom:16px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:2px;color:#94a3b8;">Daily Job Digest</div>
          <div style="font-size:22px;font-weight:700;margin-top:4px;">{today}</div>
          <div style="margin-top:12px;display:flex;gap:16px;">
            <div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:8px 14px;">
              <div style="font-size:20px;font-weight:700;">{job_count}</div>
              <div style="font-size:11px;color:#94a3b8;">New Listings</div>
            </div>
            <div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:8px 14px;">
              <div style="font-size:20px;font-weight:700;color:#4ade80;">{high_score}</div>
              <div style="font-size:11px;color:#94a3b8;">Strong Matches</div>
            </div>
            <div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:8px 14px;">
              <div style="font-size:20px;font-weight:700;color:#60a5fa;">{priority_count}</div>
              <div style="font-size:11px;color:#94a3b8;">Priority Firms</div>
            </div>
          </div>
        </div>

        <!-- Job Cards -->
        {cards_html}

        <!-- Footer -->
        <div style="text-align:center;padding:20px;font-size:11px;color:#9ca3af;">
          Searched: Partner, Senior Partner, VP, SVP, CIO, CDO, MD roles<br>
          Location: Chicago, IL + Remote | Salary Floor: $250K+<br>
          Industries: Manufacturing, Industrial, Technology, Consulting<br>
          <br>
          Scored by Claude AI &middot; Delivered via Resend
        </div>

      </div>
    </body>
    </html>
    """


def send_email(jobs: list[dict]) -> bool:
    """Build and send the daily digest email."""
    if not config.RESEND_API_KEY:
        print("[email] No RESEND_API_KEY set — writing HTML to local file instead")
        html = build_email_html(jobs)
        output_path = "/tmp/job-digest-preview.html"
        with open(output_path, "w") as f:
            f.write(html)
        print(f"[email] Preview written to {output_path}")
        return False

    resend.api_key = config.RESEND_API_KEY

    today = datetime.now().strftime("%b %d")
    high_score = len([j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7])
    subject = f"Job Digest ({today}) — {len(jobs)} new listings"
    if high_score > 0:
        subject += f", {high_score} strong matches"

    html = build_email_html(jobs)

    try:
        result = resend.Emails.send({
            "from": config.EMAIL_FROM,
            "to": [config.EMAIL_TO],
            "subject": subject,
            "html": html,
        })
        print(f"[email] Sent to {config.EMAIL_TO} — ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"[email] Send failed: {e}")
        # Write to file as fallback
        output_path = "/tmp/job-digest-preview.html"
        with open(output_path, "w") as f:
            f.write(html)
        print(f"[email] Fallback: preview written to {output_path}")
        return False
