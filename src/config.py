"""Configuration for the job search agent."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# --- Email ---
EMAIL_TO = os.getenv("EMAIL_TO", "avanish.mehrotra@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "jobs@yourdomain.com")

# --- Search Criteria ---
JOB_TITLES = [
    "Partner",
    "Senior Partner",
    "Vice President",
    "VP",
    "SVP",
    "Senior Vice President",
    "CIO",
    "Chief Information Officer",
    "Chief Digital Officer",
    "CDO",
    "Managing Director",
    "MD",
]

LOCATION = "Chicago, IL"
INCLUDE_REMOTE = True

INDUSTRIES = [
    "manufacturing",
    "industrial",
    "technology",
    "hi-tech",
    "high-tech",
    "consulting",
    "management consulting",
    "strategy consulting",
    "digital transformation",
]

SALARY_FLOOR = 250_000

# --- Career Page Scanning ---
# Scans priority firm career sites directly (uses extra SerpAPI quota: ~10 searches/day)
# Set to "true" to enable (requires SerpAPI paid plan for >100 searches/month)
SCAN_CAREER_PAGES = os.getenv("SCAN_CAREER_PAGES", "false").lower() == "true"

PRIORITIZE_COMPANIES = [
    "BCG",
    "Boston Consulting Group",
    "McKinsey",
    "McKinsey & Company",
    "Bain",
    "Bain & Company",
    "Accenture",
    "Oliver Wyman",
    "Slalom",
    "IBM",
    "EY",
    "Ernst & Young",
    "PwC",
    "PricewaterhouseCoopers",
    "KPMG",
]

EXCLUDE_COMPANIES = [
    "Deloitte",
]

# --- Candidate Profile (for LLM scoring) ---
CANDIDATE_PROFILE = """
SENIOR CONSULTING PARTNER | DIGITAL & TECH STRATEGY & TRANSFORMATION

Consulting and transformation executive with 20+ years of experience leading consulting-led
growth, AI-enabled modernization, and Industry 4.0 transformation for global manufacturing
and industrial clients. Proven track record of consistently exceeding sales and growth targets,
leading strategic deals, account planning and GTM strategy, managing CxO/Board relationships
and ecosystem partnerships, and enabling $5B+ enterprise value creation through consulting-led
transformation initiatives. Recognized thought leader and keynote speaker on digital
transformation, strategic thinker with operational skills, and mentor to high-performance teams.

Key strengths:
- Commercial Leadership: $100M+ portfolios, $140M+ existing logo pipeline, $60M+ new logo pipeline
- Digital & AI-led Transformation: Digital strategy offering, AI-first capability model, Insights-as-a-Service
- Enterprise Value Creation: $5B+ business impact, $2B+ valuation gain, $400M+ sector growth
- People & Culture Steward: 1500+ global cross-functional teams, leader mentorship, purpose-driven culture
- Board & CXO Engagement: Trusted C-suite and board advisor, business & IT partner, keynote speaker
"""
