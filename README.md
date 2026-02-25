# Job Search Agent

Automated daily job search agent that finds senior executive and consulting roles, scores them with Claude AI, and delivers an HTML email digest every morning.

## What It Does

1. **Searches** job boards (via SerpAPI or JSearch) for Partner, VP, CIO, MD roles
2. **Filters** by location (Chicago + remote), industry, and salary floor ($250K+)
3. **Deduplicates** against previously seen listings (30-day rolling window)
4. **Excludes** blacklisted companies (Deloitte)
5. **Scores** each job on 4 dimensions using Claude Haiku (~$0.05/day)
6. **Emails** a formatted HTML digest with ranked results via Resend

## Search Criteria

| Parameter | Value |
|-----------|-------|
| Titles | Partner, Senior Partner, VP, SVP, CIO, CDO, Managing Director |
| Location | Chicago, IL + Remote |
| Industries | Manufacturing, Industrial, Technology, Consulting |
| Salary Floor | $250,000/year |
| Priority Firms | BCG, McKinsey, Bain, Accenture, Oliver Wyman, Slalom, IBM, EY, PwC, KPMG |
| Excluded | Deloitte |

## Setup (10 minutes)

### 1. Create a GitHub repo

```bash
cd ~/job-agent
git init
git add .
git commit -m "Initial commit"
gh repo create job-agent --private --source=. --push
```

### 2. Get API keys (all have free tiers)

| Service | Free Tier | Sign Up |
|---------|-----------|---------|
| **SerpAPI** | 100 searches/month | https://serpapi.com |
| **Anthropic** | Pay-as-you-go (~$1.50/month) | https://console.anthropic.com |
| **Resend** | 100 emails/day | https://resend.com |

> **Note on Resend**: You need a verified domain to send from. Resend provides a free
> `onboarding@resend.dev` sender for testing, but for daily use you'll need to verify
> a domain you own (takes 5 minutes with DNS records).

### 3. Add secrets to GitHub

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `SERPAPI_KEY` | Your SerpAPI key |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `RESEND_API_KEY` | Your Resend API key |
| `EMAIL_TO` | `avanish.mehrotra@gmail.com` |
| `EMAIL_FROM` | `jobs@yourdomain.com` (must match Resend verified domain) |

Optional (if using JSearch as fallback):
| `RAPIDAPI_KEY` | Your RapidAPI key |

### 4. Enable the workflow

The GitHub Action runs automatically at **7:00 AM Central** every day. You can also
trigger it manually: Actions tab → Daily Job Search → Run workflow.

## Local Development

```bash
# Clone and setup
cd ~/job-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys

# Preview the email template with sample data
python main.py --preview
open /tmp/job-digest-preview.html

# Run a real search without sending email
python main.py --dry-run

# Full run (search + rank + email)
python main.py
```

## Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| SerpAPI | Free (100 searches, we use ~30) |
| Claude Haiku | ~$1.50 (scoring ~50 jobs/day) |
| Resend | Free (1 email/day) |
| GitHub Actions | Free (< 5 min/day) |
| **Total** | **~$1.50/month** |

## Customization

All search criteria are in `src/config.py`:
- Add/remove job titles, industries, locations
- Change salary floor
- Update priority/exclude company lists
- Edit candidate profile for better LLM scoring

## File Structure

```
job-agent/
├── main.py                          # Entry point
├── src/
│   ├── config.py                    # Search criteria + candidate profile
│   ├── search.py                    # SerpAPI + JSearch fetchers
│   ├── ranker.py                    # Claude Haiku scoring
│   └── email_sender.py             # HTML builder + Resend sender
├── data/
│   └── seen_jobs.json               # Dedup cache (auto-managed)
├── .github/workflows/
│   └── daily-search.yml             # Daily cron job
├── .env.example                     # API key template
├── requirements.txt
└── README.md
```
