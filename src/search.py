"""Job search module — fetches listings from SerpAPI or JSearch."""

import hashlib
import json
import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import httpx

from . import config

SEEN_JOBS_PATH = Path(__file__).parent.parent / "data" / "seen_jobs.json"


def _load_seen() -> dict:
    """Load previously seen job IDs with their first-seen date."""
    if SEEN_JOBS_PATH.exists():
        return json.loads(SEEN_JOBS_PATH.read_text())
    return {}


def _save_seen(seen: dict) -> None:
    """Persist seen job IDs."""
    SEEN_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_JOBS_PATH.write_text(json.dumps(seen, indent=2))


def _job_id(job: dict) -> str:
    """Generate a stable hash for deduplication."""
    raw = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('location', '')}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _is_excluded(company: str) -> bool:
    """Check if company is in the exclusion list."""
    company_lower = company.lower()
    return any(exc.lower() in company_lower for exc in config.EXCLUDE_COMPANIES)


def _google_search_url(title: str, company: str) -> str:
    """Build a Google search URL as fallback when no direct apply link exists."""
    query = f"{title} {company} job apply"
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def _build_search_queries() -> list[str]:
    """Build search query strings from job titles and industries."""
    title_groups = [
        '"Partner" OR "Senior Partner" OR "Managing Director"',
        '"Vice President" OR "VP" OR "SVP"',
        '"CIO" OR "Chief Digital Officer" OR "Chief Information Officer"',
    ]
    industry_terms = "consulting OR manufacturing OR technology OR digital transformation"
    queries = []
    for titles in title_groups:
        queries.append(f"({titles}) AND ({industry_terms})")
    return queries


# ---------------------------------------------------------------------------
# SerpAPI Google Jobs
# ---------------------------------------------------------------------------

def search_serpapi() -> list[dict]:
    """Search via SerpAPI Google Jobs endpoint."""
    if not config.SERPAPI_KEY:
        print("[search] No SERPAPI_KEY set, skipping SerpAPI")
        return []

    all_jobs = []
    queries = _build_search_queries()

    for query in queries:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": config.LOCATION,
            "api_key": config.SERPAPI_KEY,
            "num": 20,
        }
        if config.INCLUDE_REMOTE:
            params_remote = {**params, "ltype": "1"}

        try:
            # On-site / Chicago search
            resp = httpx.get("https://serpapi.com/search", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for job in data.get("jobs_results", []):
                all_jobs.append(_normalize_serpapi(job))

            # Remote search
            if config.INCLUDE_REMOTE:
                resp_r = httpx.get("https://serpapi.com/search", params=params_remote, timeout=30)
                resp_r.raise_for_status()
                for job in resp_r.json().get("jobs_results", []):
                    all_jobs.append(_normalize_serpapi(job))

        except Exception as e:
            print(f"[search] SerpAPI error for query '{query[:50]}...': {e}")

    return all_jobs


def _normalize_serpapi(job: dict) -> dict:
    """Normalize SerpAPI job result to common schema."""
    extensions = job.get("detected_extensions", {})

    # Extract all apply links from the job
    apply_options = job.get("apply_options", [])
    apply_links = []
    for opt in apply_options:
        link = opt.get("link", "")
        title = opt.get("title", "")
        if link:
            apply_links.append({"url": link, "source": title})

    # Primary URL: first apply link > share_link > related_links > google fallback
    primary_url = ""
    if apply_links:
        primary_url = apply_links[0]["url"]
    elif job.get("share_link"):
        primary_url = job["share_link"]
    elif job.get("related_links"):
        primary_url = job["related_links"][0].get("link", "")

    # Extract highlights (qualifications, responsibilities, benefits)
    highlights = job.get("job_highlights", [])
    qualifications = []
    responsibilities = []
    benefits = []
    for h in highlights:
        title = h.get("title", "").lower()
        items = h.get("items", [])
        if "qualif" in title or "require" in title:
            qualifications = items
        elif "responsib" in title or "duties" in title:
            responsibilities = items
        elif "benefit" in title:
            benefits = items

    return {
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": job.get("location", ""),
        "description": job.get("description", "")[:3000],
        "salary": extensions.get("salary", ""),
        "posted": extensions.get("posted_at", ""),
        "schedule": extensions.get("schedule_type", ""),
        "url": primary_url,
        "apply_links": apply_links,
        "via": job.get("via", ""),
        "qualifications": qualifications[:8],
        "responsibilities": responsibilities[:6],
        "benefits": benefits[:5],
        "source": "serpapi",
    }


# ---------------------------------------------------------------------------
# JSearch (RapidAPI) — fallback / alternative
# ---------------------------------------------------------------------------

def search_jsearch() -> list[dict]:
    """Search via JSearch API on RapidAPI."""
    if not config.RAPIDAPI_KEY:
        print("[search] No RAPIDAPI_KEY set, skipping JSearch")
        return []

    all_jobs = []
    queries = _build_search_queries()
    headers = {
        "X-RapidAPI-Key": config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    for query in queries:
        try:
            params = {
                "query": f"{query} in Chicago, IL",
                "page": "1",
                "num_pages": "2",
                "date_posted": "week",
                "remote_jobs_only": "false",
            }
            resp = httpx.get(
                "https://jsearch.p.rapidapi.com/search",
                headers=headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            for job in resp.json().get("data", []):
                all_jobs.append(_normalize_jsearch(job))

            if config.INCLUDE_REMOTE:
                params_r = {**params, "query": query, "remote_jobs_only": "true"}
                resp_r = httpx.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers=headers,
                    params=params_r,
                    timeout=30,
                )
                resp_r.raise_for_status()
                for job in resp_r.json().get("data", []):
                    all_jobs.append(_normalize_jsearch(job))

        except Exception as e:
            print(f"[search] JSearch error: {e}")

    return all_jobs


def _normalize_jsearch(job: dict) -> dict:
    """Normalize JSearch result to common schema."""
    salary_min = job.get("job_min_salary") or 0
    salary_max = job.get("job_max_salary") or 0
    salary_str = ""
    if salary_min or salary_max:
        period = job.get("job_salary_period", "YEAR")
        salary_str = f"${salary_min:,.0f} - ${salary_max:,.0f} / {period.lower()}"

    apply_link = job.get("job_apply_link", "")
    return {
        "title": job.get("job_title", ""),
        "company": job.get("employer_name", ""),
        "location": job.get("job_city", "") or job.get("job_country", ""),
        "description": (job.get("job_description") or "")[:3000],
        "salary": salary_str,
        "posted": job.get("job_posted_at_datetime_utc", ""),
        "schedule": job.get("job_employment_type", ""),
        "url": apply_link,
        "apply_links": [{"url": apply_link, "source": job.get("job_publisher", "")}] if apply_link else [],
        "via": job.get("job_publisher", ""),
        "qualifications": [],
        "responsibilities": [],
        "benefits": [],
        "source": "jsearch",
    }


# ---------------------------------------------------------------------------
# Unified search entry point
# ---------------------------------------------------------------------------

def fetch_jobs() -> list[dict]:
    """Fetch jobs from all configured sources, deduplicate, filter exclusions."""
    print(f"[search] Starting job search — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    raw_jobs = []

    if config.SERPAPI_KEY:
        raw_jobs.extend(search_serpapi())
    if config.RAPIDAPI_KEY:
        raw_jobs.extend(search_jsearch())

    # Direct career page scanning (opt-in, uses extra API quota)
    from .career_pages import search_career_pages
    career_jobs = search_career_pages()
    if career_jobs:
        raw_jobs.extend(career_jobs)

    if not raw_jobs:
        print("[search] WARNING: No API keys configured. Set SERPAPI_KEY or RAPIDAPI_KEY.")
        return []

    print(f"[search] Raw results: {len(raw_jobs)}")

    # Deduplicate
    seen = _load_seen()
    unique_jobs = []
    today = datetime.now().isoformat()[:10]

    for job in raw_jobs:
        jid = _job_id(job)
        if jid in seen:
            continue
        if _is_excluded(job.get("company", "")):
            continue
        seen[jid] = today
        job["id"] = jid

        # Always ensure a clickable URL exists
        if not job.get("url"):
            job["url"] = _google_search_url(job["title"], job["company"])
            job["url_is_search"] = True
        else:
            job["url_is_search"] = False

        unique_jobs.append(job)

    _save_seen(seen)

    # Prune seen list older than 30 days
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()[:10]
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    _save_seen(seen)

    print(f"[search] New unique jobs after dedup + exclusions: {len(unique_jobs)}")
    return unique_jobs
