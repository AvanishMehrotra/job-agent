"""Direct career page scanning for priority firms.

SerpAPI catches most listings via Google Jobs aggregation, but some firms
post roles on their own career sites days before they appear on aggregators.
This module checks career page RSS/API feeds where available, and falls back
to Google site-specific searches for the rest.
"""

import urllib.parse
import httpx

from . import config

# Career page search URLs — we use Google's site: operator to search
# each firm's career site directly. This catches postings that Google Jobs
# hasn't indexed yet.
FIRM_CAREER_SEARCHES = {
    "PwC": "site:pwc.com/us careers (Partner OR Director OR Managing Director) (manufacturing OR technology OR digital)",
    "KPMG": "site:kpmg.com/us careers (Partner OR Director OR Managing Director) (manufacturing OR technology OR digital)",
    "EY": "site:ey.com/en_us careers (Partner OR Director OR Managing Director) (manufacturing OR technology OR digital)",
    "BCG": "site:bcg.com careers (Partner OR Managing Director) (manufacturing OR technology OR digital)",
    "McKinsey": "site:mckinsey.com careers (Partner OR Associate Partner) (manufacturing OR technology OR digital)",
    "Bain": "site:bain.com careers (Partner OR Manager) (manufacturing OR technology OR industrial)",
    "Accenture": "site:accenture.com/us-en careers (Managing Director OR Senior Managing Director) (manufacturing OR technology OR Industry X)",
    "Oliver Wyman": "site:oliverwyman.com careers (Partner OR Principal) (manufacturing OR technology OR digital)",
    "Slalom": "site:slalom.com careers (Partner OR VP) (manufacturing OR technology OR digital)",
    "IBM": "site:ibm.com/employment careers (Partner OR VP OR Managing Director) (manufacturing OR technology OR consulting)",
}


def search_career_pages() -> list[dict]:
    """Search priority firm career pages via SerpAPI Google Search.

    Uses the regular Google Search engine (not Google Jobs) with site: operator
    to find career postings directly on each firm's website. This catches
    postings that haven't been indexed by Google Jobs yet.

    Costs: 1 SerpAPI search per firm = ~10 searches/day = ~300/month
    (exceeds the free 100/month tier, so this is opt-in via SCAN_CAREER_PAGES=true)
    """
    if not config.SERPAPI_KEY:
        return []

    if not config.SCAN_CAREER_PAGES:
        return []

    all_jobs = []
    print(f"[career] Scanning {len(FIRM_CAREER_SEARCHES)} priority firm career pages...")

    for firm, query in FIRM_CAREER_SEARCHES.items():
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": config.SERPAPI_KEY,
                "num": 10,
                "tbs": "qdr:w",  # Last week only
            }
            resp = httpx.get("https://serpapi.com/search", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("organic_results", [])
            for r in results:
                title = r.get("title", "")
                link = r.get("link", "")
                snippet = r.get("snippet", "")

                # Filter: only keep results that look like actual job postings
                title_lower = title.lower()
                if not any(kw in title_lower for kw in ["partner", "director", "vp", "vice president",
                                                          "managing", "cio", "chief", "svp", "senior"]):
                    continue

                all_jobs.append({
                    "title": title,
                    "company": firm,
                    "location": "See posting",
                    "description": snippet[:2000],
                    "salary": "",
                    "posted": "This week",
                    "schedule": "",
                    "url": link,
                    "apply_links": [{"url": link, "source": f"{firm} Careers"}],
                    "via": f"{firm} Career Site",
                    "qualifications": [],
                    "responsibilities": [],
                    "benefits": [],
                    "source": "career_page",
                })

            found = len([j for j in all_jobs if j["company"] == firm])
            if found > 0:
                print(f"[career]   {firm}: {found} potential postings")

        except Exception as e:
            print(f"[career]   {firm}: error — {e}")

    print(f"[career] Total from career pages: {len(all_jobs)}")
    return all_jobs
