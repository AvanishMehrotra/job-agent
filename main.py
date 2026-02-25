"""Daily job search agent — entry point.

Usage:
    python main.py              # Full run: search → rank → email
    python main.py --dry-run    # Search + rank, write HTML to /tmp (no email sent)
    python main.py --preview    # Use sample data, write HTML to /tmp
"""

import argparse
import json
import sys
from datetime import datetime

from src.search import fetch_jobs
from src.ranker import rank_jobs
from src.email_sender import send_email, build_email_html


def main():
    parser = argparse.ArgumentParser(description="Daily job search agent")
    parser.add_argument("--dry-run", action="store_true", help="Search and rank but don't send email")
    parser.add_argument("--preview", action="store_true", help="Use sample data to preview email template")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  Job Search Agent — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if args.preview:
        jobs = _sample_jobs()
        print(f"[main] Using {len(jobs)} sample jobs for preview")
    else:
        # Step 1: Fetch jobs
        print("\n[1/3] Fetching job listings...")
        jobs = fetch_jobs()

        if not jobs:
            print("[main] No new jobs found. Sending empty digest.")
            send_email([])
            return

        # Step 2: Rank with Claude
        print(f"\n[2/3] Ranking {len(jobs)} jobs with Claude...")
        jobs = rank_jobs(jobs)

    # Step 3: Send email (or write preview)
    if args.dry_run or args.preview:
        html = build_email_html(jobs)
        output_path = "/tmp/job-digest-preview.html"
        with open(output_path, "w") as f:
            f.write(html)
        print(f"\n[3/3] Preview written to {output_path}")
        print(f"       Open with: open {output_path}")
    else:
        print(f"\n[3/3] Sending email digest with {len(jobs)} jobs...")
        send_email(jobs)

    # Summary
    print("\n" + "-" * 40)
    print(f"Total jobs: {len(jobs)}")
    if jobs:
        top = jobs[0]
        print(f"Top match:  {top['title']} @ {top['company']} (score: {top.get('scores', {}).get('overall', '?')})")
        high = len([j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7])
        print(f"Strong matches (7+): {high}")
    print("-" * 40)


def _sample_jobs() -> list[dict]:
    """Generate sample jobs for template preview."""
    return [
        {
            "id": "sample001",
            "title": "Senior Partner, Digital Transformation",
            "company": "McKinsey & Company",
            "location": "Chicago, IL",
            "description": "Lead our manufacturing digital transformation practice across the Midwest. You will advise Fortune 500 manufacturing clients on Industry 4.0 strategy, AI/ML adoption, and operational excellence. Requires 15+ years of consulting experience with a proven track record of $50M+ engagement sales.",
            "salary": "$350,000 - $500,000 / year",
            "posted": "2 days ago",
            "url": "https://example.com/job/1",
            "via": "LinkedIn",
            "scores": {
                "title_fit": 10,
                "industry_fit": 10,
                "skill_match": 9,
                "company_prestige": 10,
                "overall": 9.5,
                "one_liner": "Perfect match — senior consulting partner role at a priority firm, manufacturing & digital transformation focus.",
            },
        },
        {
            "id": "sample002",
            "title": "Managing Director, Industrial Technology",
            "company": "Accenture",
            "location": "Chicago, IL (Hybrid)",
            "description": "Drive growth in our industrial technology practice. Responsible for P&L management, client relationships, and team development. Focus on smart manufacturing, IoT, and AI-driven operations. Must have experience selling and delivering $20M+ programs.",
            "salary": "$300,000 - $450,000 / year",
            "posted": "1 day ago",
            "url": "https://example.com/job/2",
            "via": "Company Site",
            "scores": {
                "title_fit": 9,
                "industry_fit": 9,
                "skill_match": 9,
                "company_prestige": 10,
                "overall": 9.0,
                "one_liner": "Excellent fit — MD role at priority firm with direct manufacturing technology focus and P&L ownership.",
            },
        },
        {
            "id": "sample003",
            "title": "Chief Digital Officer",
            "company": "Illinois Tool Works",
            "location": "Chicago, IL",
            "description": "Enterprise-wide digital transformation leadership for a $15B diversified manufacturer. Oversee data strategy, AI/ML capabilities, and digital product development across 7 business segments. Reports to CEO.",
            "salary": "$400,000 - $550,000 / year",
            "posted": "3 days ago",
            "url": "https://example.com/job/3",
            "via": "Indeed",
            "scores": {
                "title_fit": 10,
                "industry_fit": 10,
                "skill_match": 8,
                "company_prestige": 7,
                "overall": 8.5,
                "one_liner": "Strong match — C-suite digital role at major manufacturer. Slightly less consulting focus but exceptional scope.",
            },
        },
        {
            "id": "sample004",
            "title": "VP, Strategy & Operations",
            "company": "Bain & Company",
            "location": "Remote (US)",
            "description": "Lead strategy engagements for industrial clients focused on operational improvement and digital enablement. Partner-track role with significant business development responsibility.",
            "salary": "",
            "posted": "5 days ago",
            "url": "https://example.com/job/4",
            "via": "Glassdoor",
            "scores": {
                "title_fit": 8,
                "industry_fit": 8,
                "skill_match": 8,
                "company_prestige": 10,
                "overall": 8.0,
                "one_liner": "Good fit — partner-track at MBB with industrial focus. VP title slightly below target seniority.",
            },
        },
        {
            "id": "sample005",
            "title": "SVP, Digital Solutions",
            "company": "Rockwell Automation",
            "location": "Chicago, IL (Hybrid)",
            "description": "Own the digital solutions P&L for industrial automation leader. Build and scale SaaS offerings for smart manufacturing. Lead a team of 200+ across product, engineering, and go-to-market.",
            "salary": "$280,000 - $380,000 / year",
            "posted": "1 week ago",
            "url": "https://example.com/job/5",
            "via": "LinkedIn",
            "scores": {
                "title_fit": 9,
                "industry_fit": 10,
                "skill_match": 7,
                "company_prestige": 6,
                "overall": 7.5,
                "one_liner": "Solid fit — senior role at major industrial company. More product-focused than consulting but strong domain overlap.",
            },
        },
        {
            "id": "sample006",
            "title": "Director, Technology Consulting",
            "company": "Slalom",
            "location": "Chicago, IL",
            "description": "Lead technology consulting engagements for manufacturing and industrial clients. Drive practice growth and thought leadership in cloud, data, and AI.",
            "salary": "$200,000 - $280,000 / year",
            "posted": "4 days ago",
            "url": "https://example.com/job/6",
            "via": "Slalom Careers",
            "scores": {
                "title_fit": 5,
                "industry_fit": 8,
                "skill_match": 7,
                "company_prestige": 8,
                "overall": 5.5,
                "one_liner": "Below target seniority (Director vs Partner/MD). Salary below $250K floor. Priority firm but role may be a step back.",
            },
        },
    ]


if __name__ == "__main__":
    main()
