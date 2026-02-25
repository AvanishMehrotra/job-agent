"""Daily job search agent — entry point.

Usage:
    python main.py              # Full run: search -> rank -> email
    python main.py --dry-run    # Search + rank, write HTML to /tmp (no email sent)
    python main.py --preview    # Use sample data, write HTML to /tmp
"""

import argparse
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
        print("\n[1/3] Fetching job listings...")
        jobs = fetch_jobs()

        if not jobs:
            print("[main] No new jobs found. Sending empty digest.")
            send_email([])
            return

        print(f"\n[2/3] Ranking {len(jobs)} jobs with Claude...")
        jobs = rank_jobs(jobs)

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

    print("\n" + "-" * 40)
    print(f"Total jobs: {len(jobs)}")
    if jobs:
        top = jobs[0]
        print(f"Top match:  {top['title']} @ {top['company']} (score: {top.get('scores', {}).get('overall', '?')})")
        high = len([j for j in jobs if j.get("scores", {}).get("overall", 0) >= 7])
        print(f"Strong matches (7+): {high}")
    print("-" * 40)


def _sample_jobs() -> list[dict]:
    """Generate sample jobs for template preview with full enriched data."""
    return [
        {
            "id": "sample001",
            "title": "Senior Partner, Digital Transformation",
            "company": "McKinsey & Company",
            "location": "Chicago, IL",
            "description": "Lead our manufacturing digital transformation practice across the Midwest. You will advise Fortune 500 manufacturing clients on Industry 4.0 strategy, AI/ML adoption, and operational excellence. Requires 15+ years of consulting experience with a proven track record of $50M+ engagement sales. This role involves building client relationships at the C-suite level, developing thought leadership, and mentoring a team of 20+ consultants.",
            "salary": "$350,000 - $500,000 / year",
            "posted": "2 days ago",
            "url": "https://example.com/job/1",
            "url_is_search": False,
            "apply_links": [
                {"url": "https://example.com/apply/mckinsey", "source": "McKinsey Careers"},
                {"url": "https://linkedin.com/jobs/123", "source": "LinkedIn"},
            ],
            "via": "LinkedIn",
            "qualifications": ["15+ years consulting experience", "$50M+ engagement sales track record", "Manufacturing or industrial sector expertise"],
            "responsibilities": ["Lead digital transformation engagements", "Build C-suite client relationships", "Develop thought leadership"],
            "benefits": ["Competitive compensation", "Global mobility", "Partner equity"],
            "scores": {
                "title_fit": 10, "industry_fit": 10, "skill_match": 9, "company_prestige": 10, "overall": 9.5,
                "one_liner": "Perfect match: senior consulting partner role at MBB, manufacturing digital transformation focus, Chicago-based.",
                "key_requirements": ["15+ years consulting with $50M+ sales track record", "Manufacturing/industrial sector depth", "C-suite relationship management"],
                "why_apply": "This maps directly to your 20+ years of consulting-led growth and $5B+ enterprise value creation. Your AI-enabled modernization and Industry 4.0 expertise is exactly what McKinsey's manufacturing practice needs.",
                "talking_points": ["Your $140M+ existing logo pipeline demonstrates the commercial scale they need", "Your track record of leading 1500+ global teams shows the leadership capacity for a senior partner role"],
                "red_flags": [],
                "deep_insight": "McKinsey has been aggressively expanding its QuantumBlack AI practice into manufacturing. This Senior Partner opening in Chicago signals they're building a dedicated Midwest manufacturing hub, likely driven by reshoring demand from automotive and industrial clients. As a new practice build, the upside is significant: you'd be shaping the team, not inheriting one.",
                "networking_angle": "Target McKinsey's Chicago office managing partners through the Economic Club of Chicago or Manufacturing Leadership Council events. Partners in the Operations Practice (Katy George's network) would be the warm intro path.",
                "comp_intel": "McKinsey acquired QuantumBlack (AI) and Iguazio (ML ops) to build an end-to-end digital transformation capability. Their manufacturing practice grew 30%+ last year driven by reshoring advisory and smart factory engagements.",
            },
        },
        {
            "id": "sample002",
            "title": "Managing Director, Industrial Technology",
            "company": "Accenture",
            "location": "Chicago, IL (Hybrid)",
            "description": "Drive growth in our industrial technology practice. Responsible for P&L management, client relationships, and team development. Focus on smart manufacturing, IoT, and AI-driven operations. Must have experience selling and delivering $20M+ programs. Lead cross-functional teams of 50+ across strategy, technology, and change management.",
            "salary": "$300,000 - $450,000 / year",
            "posted": "1 day ago",
            "url": "https://example.com/job/2",
            "url_is_search": False,
            "apply_links": [{"url": "https://example.com/apply/accenture", "source": "Accenture Careers"}],
            "via": "Company Site",
            "qualifications": ["$20M+ program delivery experience", "Smart manufacturing expertise", "P&L ownership"],
            "responsibilities": [],
            "benefits": [],
            "scores": {
                "title_fit": 9, "industry_fit": 9, "skill_match": 9, "company_prestige": 10, "overall": 9.0,
                "one_liner": "Excellent fit: MD at priority firm with direct manufacturing technology focus, P&L ownership, and Chicago base.",
                "key_requirements": ["$20M+ program sales and delivery", "Smart manufacturing and IoT expertise", "P&L management experience"],
                "why_apply": "Your $100M+ portfolio management and AI-first capability model development directly exceeds their $20M+ threshold. Accenture's Industry X.0 practice aligns perfectly with your digital transformation offering.",
                "talking_points": ["Highlight your $60M+ new logo pipeline to demonstrate growth mindset", "Reference your Insights-as-a-Service offering as a differentiator vs traditional consulting"],
                "red_flags": [],
                "deep_insight": "Accenture's Industry X division (formerly Digital) is their fastest-growing practice. This MD opening likely signals a departure or a new team standup in Chicago to serve the concentration of industrial clients in the Midwest. The hybrid model suggests they're flexible, which is unusual for Accenture at this level.",
                "networking_angle": "Accenture MDs often speak at Hannover Messe and IMTS (Chicago). Check if any Industry X leaders are presenting at upcoming Manufacturing Leadership Council summits where you could make a direct connection.",
                "comp_intel": "Accenture invested $3B in Industry X capabilities and acquired multiple IoT/digital twin companies. They're positioning against McKinsey and BCG by combining strategy advisory with implementation at scale.",
            },
        },
        {
            "id": "sample003",
            "title": "Chief Digital Officer",
            "company": "Illinois Tool Works",
            "location": "Chicago, IL",
            "description": "Enterprise-wide digital transformation leadership for a $15B diversified manufacturer. Oversee data strategy, AI/ML capabilities, and digital product development across 7 business segments. Reports to CEO. This is a newly created role reflecting ITW's strategic commitment to digital innovation.",
            "salary": "$400,000 - $550,000 / year",
            "posted": "3 days ago",
            "url": "https://example.com/job/3",
            "url_is_search": False,
            "apply_links": [{"url": "https://example.com/apply/itw", "source": "ITW Careers"}],
            "via": "Indeed",
            "qualifications": [],
            "responsibilities": [],
            "benefits": [],
            "scores": {
                "title_fit": 10, "industry_fit": 10, "skill_match": 8, "company_prestige": 7, "overall": 8.5,
                "one_liner": "Strong match: C-suite digital role at a $15B manufacturer. Less consulting, but exceptional scope and impact potential.",
                "key_requirements": ["Enterprise-wide digital strategy across multiple business units", "AI/ML capability building", "CEO-level reporting and board engagement"],
                "why_apply": "Your experience enabling $5B+ enterprise value creation through consulting-led transformation is exactly what a newly created CDO role needs. You'd be building the function from scratch with a CEO mandate.",
                "talking_points": ["Your experience across global cross-functional teams of 1500+ maps to leading transformation across ITW's 7 business segments", "Position your consulting background as an advantage: you've seen digital transformation succeed and fail across dozens of manufacturers"],
                "red_flags": ["This is an operating role, not a consulting role. Ensure you're ready for the shift from advisory to ownership."],
                "deep_insight": "ITW is known for its '80/20' operational philosophy and decentralized business model. A newly created CDO role reporting to the CEO is a major strategic shift, suggesting the board has decided that digital can no longer be left to individual divisions. This is a company-defining hire with high visibility but also high execution risk across 7 independent-minded business units.",
                "networking_angle": "ITW's board includes several former GE and Honeywell executives. If you have connections in those networks, a board-level referral would carry significant weight for a role of this profile.",
                "comp_intel": "ITW has historically underinvested in digital compared to peers like Honeywell and Siemens. This CDO hire signals a strategic pivot, likely driven by competitive pressure and margin erosion in their automotive and food equipment segments.",
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
            "url_is_search": False,
            "apply_links": [{"url": "https://example.com/apply/bain", "source": "Bain Careers"}],
            "via": "Glassdoor",
            "qualifications": [],
            "responsibilities": [],
            "benefits": [],
            "scores": {
                "title_fit": 8, "industry_fit": 8, "skill_match": 8, "company_prestige": 10, "overall": 8.0,
                "one_liner": "Good fit: partner-track at MBB with industrial focus. VP title slightly below your current seniority but the trajectory is strong.",
                "key_requirements": ["Strategy engagement leadership", "Industrial client business development", "Operational improvement expertise"],
                "why_apply": "MBB partner-track roles are rare. Even though VP is one level below your current seniority, the partner trajectory at Bain with your industrial expertise could accelerate quickly.",
                "talking_points": ["Emphasize your GTM strategy experience and $60M+ new logo pipeline", "Highlight the $5B+ enterprise value creation as evidence of impact at scale"],
                "red_flags": ["VP title may represent a step back from your current Partner/MD level", "No salary listed: ensure it meets your $250K+ floor before investing time"],
                "deep_insight": "Bain has been growing its Advanced Manufacturing practice through partners recruited from industry. A VP-level opening suggests they're building bench strength below the partner level. If you're open to a brief VP stint with a fast track to Partner, this could work. But negotiate hard on the title and timeline.",
                "networking_angle": "Bain's industrial practice often recruits through former Bain alumni who are now in C-suite manufacturing roles. Tap your C-suite network for warm referrals back into Bain.",
                "comp_intel": "Bain recently launched a dedicated 'Digital@Scale' offering for manufacturers and acquired a data analytics firm. Their industrial practice has grown 25% year-over-year.",
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
            "url_is_search": False,
            "apply_links": [],
            "via": "LinkedIn",
            "qualifications": [],
            "responsibilities": [],
            "benefits": [],
            "scores": {
                "title_fit": 9, "industry_fit": 10, "skill_match": 7, "company_prestige": 6, "overall": 7.5,
                "one_liner": "Solid fit: senior role at a major industrial company. More product-focused than consulting but strong domain overlap.",
                "key_requirements": ["SaaS P&L ownership", "200+ person team leadership", "Smart manufacturing domain"],
                "why_apply": "Your Insights-as-a-Service and AI-first capability model experience translates directly to building SaaS offerings for smart manufacturing.",
                "talking_points": ["Position your consulting experience as an asset: you understand what manufacturers actually need from digital tools"],
                "red_flags": ["This is a product/SaaS role, not consulting. Different operating rhythm.", "Salary cap of $380K is below some of the other opportunities."],
                "deep_insight": "Rockwell is in a multi-year transition from hardware (PLCs, drives) to software (FactoryTalk, Plex). This SVP role likely exists because their software transformation isn't moving fast enough. You'd be expected to accelerate the pivot, which is high-impact but also high-pressure.",
                "networking_angle": "Rockwell's leadership team frequently speaks at Automation Fair (their flagship event) and CSIA. If you've attended any industrial automation events, leverage those connections.",
                "comp_intel": "Rockwell acquired Plex Systems ($2.2B) and Fiix to build a cloud MES/EAM platform. They're competing directly with Siemens and PTC for the industrial software market.",
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
            "url": "",
            "url_is_search": True,
            "apply_links": [],
            "via": "Slalom Careers",
            "qualifications": [],
            "responsibilities": [],
            "benefits": [],
            "scores": {
                "title_fit": 5, "industry_fit": 8, "skill_match": 7, "company_prestige": 8, "overall": 5.5,
                "one_liner": "Below target seniority (Director vs Partner/MD). Salary below $250K floor. Priority firm but this role would be a step back.",
                "key_requirements": ["Technology consulting leadership", "Manufacturing client experience", "Cloud/data/AI practice growth"],
                "why_apply": "",
                "talking_points": [],
                "red_flags": ["Director title is 2 levels below your current seniority", "Salary caps at $280K, below your $250K floor once you factor in the title gap", "Slalom is a strong firm but this specific role underutilizes your experience"],
                "deep_insight": "Slalom is growing rapidly in the Midwest but their manufacturing practice is still early stage. This Director role is likely a practice builder position. While the firm is a priority target, you should aim for a Partner or VP-level conversation instead.",
                "networking_angle": "Slalom's Chicago market leader would be the right person to approach about a more senior role. They often create Partner positions for the right candidate.",
                "comp_intel": "Slalom has been expanding beyond their Salesforce/cloud roots into AI and data engineering. Their manufacturing practice is nascent but growing, backed by a strategic partnership with AWS.",
            },
        },
    ]


if __name__ == "__main__":
    main()
