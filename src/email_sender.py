"""HTML email builder and sender via Resend."""

import resend
from datetime import datetime

from . import config


def _score_color(score: float) -> str:
    if score >= 7:
        return "#22c55e"
    elif score >= 5:
        return "#f59e0b"
    return "#ef4444"


def _score_bar(score: float, max_score: float = 10.0) -> str:
    pct = min(100, (score / max_score) * 100)
    color = _score_color(score)
    return (
        f'<div style="background:#e5e7eb;border-radius:4px;height:8px;width:80px;display:inline-block;vertical-align:middle;">'
        f'<div style="background:{color};border-radius:4px;height:8px;width:{pct}%;"></div>'
        f'</div>'
        f' <span style="font-size:12px;color:#6b7280;">{score:.1f}</span>'
    )


def _priority_badge(company: str) -> str:
    company_lower = company.lower()
    for p in config.PRIORITIZE_COMPANIES:
        if p.lower() in company_lower:
            return ' <span style="background:#dbeafe;color:#1d4ed8;font-size:10px;padding:2px 6px;border-radius:3px;font-weight:600;letter-spacing:0.5px;">PRIORITY</span>'
    return ""


def _remote_badge(location: str) -> str:
    if "remote" in location.lower():
        return ' <span style="background:#f0fdf4;color:#166534;font-size:10px;padding:2px 6px;border-radius:3px;font-weight:600;">REMOTE</span>'
    return ""


def _build_apply_section(job: dict) -> str:
    """Build the How to Apply section with all available links."""
    apply_links = job.get("apply_links", [])
    url = job.get("url", "")
    is_search = job.get("url_is_search", False)

    if not apply_links and not url:
        return ""

    links_html = ""
    if apply_links:
        for i, link in enumerate(apply_links[:4]):
            source = link.get("source", "Apply")
            link_url = link.get("url", "")
            if i == 0:
                links_html += f'<a href="{link_url}" style="display:inline-block;background:#2563eb;color:#ffffff;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;">Apply on {source} &rarr;</a> '
            else:
                links_html += f'<a href="{link_url}" style="color:#2563eb;text-decoration:none;font-size:12px;margin-left:8px;">{source}</a> '
    elif url:
        label = "Search for posting" if is_search else "View posting"
        links_html = f'<a href="{url}" style="display:inline-block;background:#2563eb;color:#ffffff;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600;">{label} &rarr;</a>'

    return f"""
    <div style="margin-top:12px;padding-top:12px;border-top:1px solid #e5e7eb;">
      <div style="font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">How to Apply</div>
      {links_html}
    </div>
    """


def _build_list_html(items: list, color: str = "#6b7280") -> str:
    if not items:
        return ""
    list_items = "".join(f'<li style="margin-bottom:2px;">{item}</li>' for item in items)
    return f'<ul style="margin:4px 0;padding-left:18px;font-size:12px;color:{color};list-style:disc;">{list_items}</ul>'


def _build_job_card(job: dict, rank: int, expanded: bool = True) -> str:
    """Build an HTML card for a single job listing."""
    scores = job.get("scores", {})
    overall = scores.get("overall", 0)
    one_liner = scores.get("one_liner", "")
    title_fit = scores.get("title_fit", 0)
    industry_fit = scores.get("industry_fit", 0)
    skill_match = scores.get("skill_match", 0)
    company_prestige = scores.get("company_prestige", 0)

    border_color = _score_color(overall)

    url = job.get("url", "")
    salary = job.get("salary", "")
    salary_html = f'<span style="color:#059669;font-weight:600;">{salary}</span>' if salary else '<span style="color:#9ca3af;">Salary not listed</span>'

    via = job.get("via", "")
    via_html = f' <span style="color:#9ca3af;font-size:11px;">via {via}</span>' if via else ""

    posted = job.get("posted", "")
    posted_html = f' &middot; <span style="font-size:12px;color:#9ca3af;">{posted}</span>' if posted else ""

    # Title as clickable link
    title_html = f'<a href="{url}" style="color:#111827;text-decoration:none;font-size:16px;font-weight:700;">{job["title"]}</a>' if url else f'<span style="font-size:16px;font-weight:700;color:#111827;">{job["title"]}</span>'

    # --- Deep insights section (collapsible via <details>) ---
    key_reqs = scores.get("key_requirements", [])
    why_apply = scores.get("why_apply", "")
    talking_points = scores.get("talking_points", [])
    red_flags = scores.get("red_flags", [])
    deep_insight = scores.get("deep_insight", "")
    networking_angle = scores.get("networking_angle", "")
    comp_intel = scores.get("comp_intel", "")

    # Why Apply
    why_section = ""
    if why_apply:
        why_section = f"""
        <div style="margin-top:8px;">
          <div style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.5px;">Why Apply</div>
          <div style="font-size:13px;color:#374151;margin-top:2px;">{why_apply}</div>
        </div>
        """

    # Key Requirements
    reqs_section = ""
    if key_reqs:
        reqs_section = f"""
        <div style="margin-top:8px;">
          <div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;">Key Requirements</div>
          {_build_list_html(key_reqs, '#374151')}
        </div>
        """

    # Talking Points
    tp_section = ""
    if talking_points:
        tp_section = f"""
        <div style="margin-top:8px;">
          <div style="font-size:11px;font-weight:700;color:#2563eb;text-transform:uppercase;letter-spacing:0.5px;">Your Talking Points</div>
          {_build_list_html(talking_points, '#1e40af')}
        </div>
        """

    # Red Flags
    rf_section = ""
    if red_flags:
        rf_section = f"""
        <div style="margin-top:8px;">
          <div style="font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.5px;">Watch Out</div>
          {_build_list_html(red_flags, '#dc2626')}
        </div>
        """

    # Deep Insight
    insight_section = ""
    if deep_insight:
        insight_section = f"""
        <div style="margin-top:8px;background:#f8fafc;border-radius:6px;padding:10px;">
          <div style="font-size:11px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:0.5px;">Strategic Insight</div>
          <div style="font-size:12px;color:#374151;margin-top:2px;">{deep_insight}</div>
        </div>
        """

    # Networking Angle
    network_section = ""
    if networking_angle:
        network_section = f"""
        <div style="margin-top:6px;background:#f0fdf4;border-radius:6px;padding:10px;">
          <div style="font-size:11px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:0.5px;">Networking Angle</div>
          <div style="font-size:12px;color:#374151;margin-top:2px;">{networking_angle}</div>
        </div>
        """

    # Competitive Intelligence
    ci_section = ""
    if comp_intel:
        ci_section = f"""
        <div style="margin-top:6px;background:#eff6ff;border-radius:6px;padding:10px;">
          <div style="font-size:11px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.5px;">Company Intel</div>
          <div style="font-size:12px;color:#374151;margin-top:2px;">{comp_intel}</div>
        </div>
        """

    # Collapsible details section
    has_details = any([why_apply, key_reqs, talking_points, deep_insight, networking_angle, comp_intel])
    details_html = ""
    if has_details:
        open_attr = "open" if expanded and overall >= 8 else ""
        details_html = f"""
        <details {open_attr} style="margin-top:10px;">
          <summary style="cursor:pointer;font-size:12px;font-weight:600;color:#2563eb;list-style:none;user-select:none;">
            &#9660; Full Analysis &amp; Apply Guidance
          </summary>
          <div style="margin-top:8px;">
            {why_section}
            {reqs_section}
            {tp_section}
            {rf_section}
            {insight_section}
            {network_section}
            {ci_section}
          </div>
        </details>
        """

    # Apply section
    apply_section = _build_apply_section(job)

    # Description excerpt
    desc = job.get("description", "")[:400]
    desc_html = f"{desc}{'...' if len(job.get('description', '')) > 400 else ''}"

    anchor_id = f"job-{job.get('id', rank)}"

    return f"""
    <div id="{anchor_id}" style="border:1px solid {border_color};border-left:4px solid {border_color};border-radius:8px;padding:16px;margin-bottom:14px;background:#ffffff;">
      <!-- Header -->
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div style="flex:1;">
          <div style="font-size:11px;color:#9ca3af;font-weight:600;">#{rank}</div>
          <div style="margin:2px 0;">
            {title_html}{_priority_badge(job.get('company', ''))}{_remote_badge(job.get('location', ''))}
          </div>
          <div style="font-size:14px;color:#4b5563;">
            {job['company']}{via_html}
          </div>
          <div style="font-size:13px;color:#6b7280;margin-top:2px;">
            {job.get('location', 'Location not specified')} &middot; {salary_html}{posted_html}
          </div>
        </div>
        <div style="text-align:right;min-width:55px;">
          <div style="font-size:28px;font-weight:800;color:{border_color};">{overall:.0f}</div>
          <div style="font-size:10px;color:#9ca3af;">/ 10</div>
        </div>
      </div>

      <!-- AI Assessment -->
      <div style="margin-top:10px;font-size:13px;color:#374151;font-style:italic;border-left:3px solid {border_color};padding-left:10px;">
        {one_liner}
      </div>

      <!-- Score Bars -->
      <div style="margin-top:10px;font-size:12px;color:#6b7280;">
        Title: {_score_bar(title_fit)} &nbsp; Industry: {_score_bar(industry_fit)} &nbsp; Skills: {_score_bar(skill_match)} &nbsp; Company: {_score_bar(company_prestige)}
      </div>

      <!-- Description -->
      <div style="margin-top:10px;font-size:12px;color:#6b7280;line-height:1.5;">
        {desc_html}
      </div>

      <!-- Collapsible Deep Analysis -->
      {details_html}

      <!-- Apply -->
      {apply_section}
    </div>
    """


def _build_summary_row(job: dict, rank: int) -> str:
    """Build a compact table row for lower-scored jobs."""
    scores = job.get("scores", {})
    overall = scores.get("overall", 0)
    color = _score_color(overall)
    url = job.get("url", "")
    title_link = f'<a href="{url}" style="color:#2563eb;text-decoration:none;">{job["title"]}</a>' if url else job["title"]
    salary = job.get("salary", "")
    salary_html = f'<span style="color:#059669;">{salary}</span>' if salary else '-'
    anchor_id = f"job-{job.get('id', rank)}"

    return f"""
    <tr id="{anchor_id}" style="border-bottom:1px solid #f3f4f6;">
      <td style="padding:8px 6px;font-size:12px;color:#9ca3af;">{rank}</td>
      <td style="padding:8px 6px;font-size:12px;font-weight:600;color:{color};">{overall:.0f}</td>
      <td style="padding:8px 6px;font-size:13px;">{title_link}</td>
      <td style="padding:8px 6px;font-size:12px;color:#6b7280;">{job['company']}{_priority_badge(job.get('company', ''))}</td>
      <td style="padding:8px 6px;font-size:12px;">{salary_html}</td>
    </tr>
    """


def _build_toc_table(jobs: list[dict]) -> str:
    """Build a quick-reference summary table at the top with anchor links to each job."""
    if not jobs:
        return ""

    rows = ""
    for i, job in enumerate(jobs):
        scores = job.get("scores", {})
        overall = scores.get("overall", 0)
        color = _score_color(overall)
        anchor_id = f"job-{job.get('id', i + 1)}"
        title = job.get("title", "Untitled")
        company = job.get("company", "")
        location = job.get("location", "")
        salary = job.get("salary", "")

        # Truncate long titles
        if len(title) > 45:
            title = title[:42] + "..."

        loc_short = location.split(",")[0] if location else ""
        if "remote" in location.lower():
            loc_short = "Remote" if not loc_short or "remote" in loc_short.lower() else f"{loc_short} / Remote"

        salary_html = f'<span style="color:#059669;font-size:11px;">{salary}</span>' if salary else ''

        badge = ""
        company_lower = company.lower()
        for p in config.PRIORITIZE_COMPANIES:
            if p.lower() in company_lower:
                badge = ' <span style="color:#2563eb;font-size:9px;">&#9733;</span>'
                break

        # Compact salary for TOC
        sal_short = ""
        if salary:
            sal_short = salary.replace(" a year", "").replace(" per year", "").replace("per year", "").replace("a year", "").strip()
            if len(sal_short) > 25:
                sal_short = sal_short[:22] + "..."

        rows += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:5px 4px;font-size:11px;color:#9ca3af;text-align:center;">{i + 1}</td>
          <td style="padding:5px 4px;text-align:center;"><span style="font-size:12px;font-weight:700;color:{color};">{overall:.0f}</span></td>
          <td style="padding:5px 4px;font-size:12px;"><a href="#{anchor_id}" style="color:#111827;text-decoration:none;">{title}</a></td>
          <td style="padding:5px 4px;font-size:11px;color:#6b7280;">{company}{badge}</td>
          <td style="padding:5px 4px;font-size:11px;color:#6b7280;">{loc_short}</td>
          <td style="padding:5px 4px;font-size:11px;color:#059669;">{sal_short}</td>
        </tr>
        """

    # Google Jobs search URL for past/all listings with the same criteria
    past_url = "https://www.google.com/search?q=Partner+OR+VP+OR+CIO+OR+%22Managing+Director%22+manufacturing+OR+consulting+OR+technology+Chicago&ibp=htl;jobs"

    return f"""
    <div style="background:#ffffff;border-radius:8px;padding:14px;margin-bottom:16px;border:1px solid #e5e7eb;">
      <div style="font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
        All Listings at a Glance
      </div>
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="border-bottom:2px solid #e5e7eb;">
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:center;width:28px;">#</th>
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:center;width:36px;">Score</th>
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:left;">Role</th>
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:left;">Company</th>
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:left;">Location</th>
            <th style="padding:4px;font-size:10px;color:#9ca3af;text-align:left;">Salary</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid #f3f4f6;text-align:center;">
        <a href="{past_url}" style="font-size:12px;color:#2563eb;text-decoration:none;">Browse all matching listings on Google Jobs &rarr;</a>
      </div>
    </div>
    """


def build_email_html(jobs: list[dict]) -> str:
    """Build the full HTML email digest."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    job_count = len(jobs)

    high_score = len([j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7])
    priority_count = sum(
        1 for j in jobs
        if any(p.lower() in j.get("company", "").lower() for p in config.PRIORITIZE_COMPANIES)
    )
    remote_count = sum(1 for j in jobs if "remote" in j.get("location", "").lower())

    if not jobs:
        toc_html = ""
        cards_html = """
        <div style="text-align:center;padding:40px;color:#9ca3af;">
          <div style="font-size:48px;">&#128269;</div>
          <div style="font-size:16px;margin-top:12px;">No new matching jobs found today.</div>
          <div style="font-size:13px;margin-top:4px;">The agent searched for Partner, VP, CIO, and MD roles in Chicago + remote.</div>
        </div>
        """
        other_section = ""
    else:
        # Build table of contents at the top
        toc_html = _build_toc_table(jobs)

        # Split: top matches (7+) get full cards, rest go in summary table
        top_jobs = [j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7]
        other_jobs = [j for j in jobs if j.get("scores", {}).get("overall", 0) < 7]

        if top_jobs:
            cards_html = f"""
            <div style="font-size:13px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #22c55e;">
              Top Matches ({len(top_jobs)})
            </div>
            """ + "\n".join(_build_job_card(job, i + 1, expanded=True) for i, job in enumerate(top_jobs))
        else:
            cards_html = """
            <div style="text-align:center;padding:20px;color:#9ca3af;font-size:14px;">
              No strong matches (7+) today. See all listings below.
            </div>
            """

        if other_jobs:
            rows = "\n".join(_build_summary_row(job, i + len(top_jobs) + 1) for i, job in enumerate(other_jobs))
            other_section = f"""
            <div style="margin-top:20px;">
              <div style="font-size:13px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #f59e0b;">
                Other Listings ({len(other_jobs)})
              </div>
              <table style="width:100%;border-collapse:collapse;">
                <thead>
                  <tr style="border-bottom:2px solid #e5e7eb;">
                    <th style="padding:6px;font-size:11px;color:#9ca3af;text-align:left;">#</th>
                    <th style="padding:6px;font-size:11px;color:#9ca3af;text-align:left;">Score</th>
                    <th style="padding:6px;font-size:11px;color:#9ca3af;text-align:left;">Role</th>
                    <th style="padding:6px;font-size:11px;color:#9ca3af;text-align:left;">Company</th>
                    <th style="padding:6px;font-size:11px;color:#9ca3af;text-align:left;">Salary</th>
                  </tr>
                </thead>
                <tbody>
                  {rows}
                </tbody>
              </table>
            </div>
            """
        else:
            other_section = ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
      <div style="max-width:680px;margin:0 auto;padding:20px;">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:12px;padding:24px;color:#ffffff;margin-bottom:16px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:2px;color:#94a3b8;">Daily Job Digest</div>
          <div style="font-size:22px;font-weight:700;margin-top:4px;">{today}</div>
          <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;">
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
            <div style="background:rgba(255,255,255,0.1);border-radius:8px;padding:8px 14px;">
              <div style="font-size:20px;font-weight:700;color:#c084fc;">{remote_count}</div>
              <div style="font-size:11px;color:#94a3b8;">Remote</div>
            </div>
          </div>
        </div>

        <!-- Quick Reference Table -->
        {toc_html}

        <!-- Job Cards (Top Matches) -->
        {cards_html}

        <!-- Other Listings (Summary Table) -->
        {other_section}

        <!-- Footer -->
        <div style="text-align:center;padding:20px;font-size:11px;color:#9ca3af;">
          Searched: Partner, Senior Partner, VP, SVP, CIO, CDO, MD roles<br>
          Location: Chicago, IL + Remote | Salary Floor: $250K+<br>
          Industries: Manufacturing, Industrial, Technology, Consulting<br>
          Priority: BCG, McKinsey, Bain, Accenture, Oliver Wyman, Slalom, IBM, EY, PwC, KPMG<br>
          <br>
          Click &#9660; Full Analysis on each card to expand insights<br>
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
        output_path = "/tmp/job-digest-preview.html"
        with open(output_path, "w") as f:
            f.write(html)
        print(f"[email] Fallback: preview written to {output_path}")
        return False
