"""LLM-powered job ranking using Claude Haiku."""

import json
from anthropic import Anthropic

from . import config

SYSTEM_PROMPT = """You are a job relevance scoring assistant. You evaluate job listings against
a candidate's profile and return structured scores plus actionable guidance.

CANDIDATE PROFILE:
{profile}

SCORING CRITERIA (each 0-10):
1. **Title Fit** — How well does the job title match the candidate's seniority and role type?
   (Partner, SVP, CIO, Managing Director = 10; Director = 6; Manager = 2)
2. **Industry Fit** — Is this in manufacturing, industrial, technology, consulting, or digital transformation?
   (Core manufacturing consulting = 10; Adjacent tech = 7; Unrelated = 2)
3. **Skill Match** — Does the role require the candidate's core competencies?
   (AI/digital transformation + P&L + consulting = 10; Only partial overlap = 5)
4. **Company Prestige** — Is this a priority company (BCG, McKinsey, Bain, Accenture, Oliver Wyman,
   Slalom, IBM, EY, PwC, KPMG) or equivalent tier?
   (Priority list = 10; Other top-tier = 7; Mid-market = 4)
5. **Overall Relevance** — Holistic assessment: would this be a compelling opportunity?

RESPOND WITH ONLY valid JSON — no markdown, no explanation:
{{
  "scores": [
    {{
      "id": "job_id",
      "title_fit": 8,
      "industry_fit": 9,
      "skill_match": 7,
      "company_prestige": 10,
      "overall": 8.5,
      "one_liner": "Brief reason this is or isn't a good fit",
      "key_requirements": ["requirement 1", "requirement 2", "requirement 3"],
      "why_apply": "1-2 sentence compelling reason to pursue this specific role",
      "talking_points": ["Specific experience or achievement to highlight in application"],
      "red_flags": ["Any concerns about fit, seniority mismatch, or missing qualifications"],
      "deep_insight": "Strategic analysis: what signal does this opening send about the company's direction, why this role exists now, what the hiring context likely is (growth, replacement, new initiative), and how the candidate's background uniquely positions them vs other candidates",
      "networking_angle": "Specific suggestion for how to get a warm intro or stand out — e.g. who to reach out to on LinkedIn, which conference connections to leverage, or what mutual network to tap",
      "comp_intel": "Brief competitive intelligence: what this company is doing in digital/AI/manufacturing that makes this role strategically interesting"
    }}
  ]
}}

IMPORTANT:
- key_requirements: Extract the 3 most critical requirements from the job description
- why_apply: Be specific — reference the candidate's experience that maps to this role
- talking_points: Suggest 1-2 specific things from the candidate's background to emphasize
- red_flags: Note concerns like seniority mismatch, wrong industry, or missing skills. Empty array if none.
- deep_insight: Think like a strategy consultant. Analyze WHY this role is open, what it signals about the company's direction, and what unique advantage the candidate brings. Be specific, not generic.
- networking_angle: Suggest a concrete networking move — not "use LinkedIn" but rather "reach out to partners in their Chicago manufacturing practice" or "leverage Industry 4.0 conference connections"
- comp_intel: What is this company doing in digital transformation, AI, or Industry 4.0 that makes this role timely? Reference real initiatives if known.
"""


def rank_jobs(jobs: list[dict]) -> list[dict]:
    """Score and rank jobs using Claude Haiku. Returns jobs sorted by overall score."""
    if not jobs:
        return []

    if not config.ANTHROPIC_API_KEY:
        print("[ranker] No ANTHROPIC_API_KEY set — returning unranked jobs")
        for job in jobs:
            job["scores"] = {
                "overall": 5.0,
                "one_liner": "Unranked (no API key)",
                "key_requirements": [],
                "why_apply": "",
                "talking_points": [],
                "red_flags": [],
            }
        return jobs

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Process in batches of 5 (rich output per job needs room)
    batch_size = 5
    scored_jobs = []

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]
        scored_jobs.extend(_score_batch(client, batch))

    # Sort by overall score descending
    scored_jobs.sort(key=lambda j: j.get("scores", {}).get("overall", 0), reverse=True)
    return scored_jobs


def _score_batch(client: Anthropic, batch: list[dict]) -> list[dict]:
    """Score a batch of jobs via a single Claude call."""
    job_summaries = []
    for job in batch:
        quals = "\n".join(f"  - {q}" for q in job.get("qualifications", [])[:5])
        resps = "\n".join(f"  - {r}" for r in job.get("responsibilities", [])[:4])
        quals_section = f"\nKey Qualifications:\n{quals}" if quals else ""
        resps_section = f"\nKey Responsibilities:\n{resps}" if resps else ""

        summary = (
            f"ID: {job['id']}\n"
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Salary: {job.get('salary', 'Not listed')}\n"
            f"Posted: {job.get('posted', 'Unknown')}\n"
            f"Description: {job['description'][:800]}"
            f"{quals_section}"
            f"{resps_section}\n"
        )
        job_summaries.append(summary)

    user_msg = "Score these job listings:\n\n" + "\n---\n".join(job_summaries)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            system=SYSTEM_PROMPT.format(profile=config.CANDIDATE_PROFILE),
            messages=[{"role": "user", "content": user_msg}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        scores_by_id = {s["id"]: s for s in result.get("scores", [])}

        for job in batch:
            if job["id"] in scores_by_id:
                job["scores"] = scores_by_id[job["id"]]
            else:
                job["scores"] = _empty_scores("Not scored")

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        print(f"[ranker] Scored {len(batch)} jobs — {input_tokens} in / {output_tokens} out tokens")

    except json.JSONDecodeError as e:
        print(f"[ranker] JSON parse error on batch of {len(batch)}: {e}")
        # Fallback: score each job individually
        if len(batch) > 1:
            print(f"[ranker] Retrying {len(batch)} jobs one at a time...")
            for job in batch:
                _score_single(client, job)
        else:
            for job in batch:
                job["scores"] = _empty_scores("Parse error during scoring")
    except Exception as e:
        print(f"[ranker] Claude API error: {e}")
        for job in batch:
            job["scores"] = _empty_scores("API error during scoring")

    return batch


def _score_single(client: Anthropic, job: dict) -> None:
    """Score a single job as fallback when batch parsing fails."""
    quals = "\n".join(f"  - {q}" for q in job.get("qualifications", [])[:5])
    resps = "\n".join(f"  - {r}" for r in job.get("responsibilities", [])[:4])
    quals_section = f"\nKey Qualifications:\n{quals}" if quals else ""
    resps_section = f"\nKey Responsibilities:\n{resps}" if resps else ""

    summary = (
        f"ID: {job['id']}\n"
        f"Title: {job['title']}\n"
        f"Company: {job['company']}\n"
        f"Location: {job['location']}\n"
        f"Salary: {job.get('salary', 'Not listed')}\n"
        f"Posted: {job.get('posted', 'Unknown')}\n"
        f"Description: {job['description'][:800]}"
        f"{quals_section}"
        f"{resps_section}\n"
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=SYSTEM_PROMPT.format(profile=config.CANDIDATE_PROFILE),
            messages=[{"role": "user", "content": f"Score this job listing:\n\n{summary}"}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        scores = result.get("scores", [])
        if scores:
            job["scores"] = scores[0]
        else:
            job["scores"] = _empty_scores("No scores returned")
    except Exception as e:
        print(f"[ranker]   Single-job fallback failed for {job.get('title', '?')}: {e}")
        job["scores"] = _empty_scores("Scoring failed")


def _empty_scores(reason: str) -> dict:
    return {
        "overall": 5.0,
        "one_liner": reason,
        "key_requirements": [],
        "why_apply": "",
        "talking_points": [],
        "red_flags": [],
        "deep_insight": "",
        "networking_angle": "",
        "comp_intel": "",
    }
