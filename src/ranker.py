"""LLM-powered job ranking using Claude Haiku."""

import json
from anthropic import Anthropic

from . import config

SYSTEM_PROMPT = """You are a job relevance scoring assistant. You evaluate job listings against
a candidate's profile and return structured scores.

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
      "one_liner": "Brief reason this is or isn't a good fit"
    }}
  ]
}}
"""


def rank_jobs(jobs: list[dict]) -> list[dict]:
    """Score and rank jobs using Claude Haiku. Returns jobs sorted by overall score."""
    if not jobs:
        return []

    if not config.ANTHROPIC_API_KEY:
        print("[ranker] No ANTHROPIC_API_KEY set — returning unranked jobs")
        for job in jobs:
            job["scores"] = {"overall": 5.0, "one_liner": "Unranked (no API key)"}
        return jobs

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Process in batches of 15 to stay within token limits
    batch_size = 15
    scored_jobs = []

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]
        scored_jobs.extend(_score_batch(client, batch))

    # Sort by overall score descending
    scored_jobs.sort(key=lambda j: j.get("scores", {}).get("overall", 0), reverse=True)
    return scored_jobs


def _score_batch(client: Anthropic, batch: list[dict]) -> list[dict]:
    """Score a batch of jobs via a single Claude call."""
    # Build the job summaries for the prompt
    job_summaries = []
    for job in batch:
        summary = (
            f"ID: {job['id']}\n"
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Salary: {job.get('salary', 'Not listed')}\n"
            f"Description (excerpt): {job['description'][:500]}\n"
        )
        job_summaries.append(summary)

    user_msg = "Score these job listings:\n\n" + "\n---\n".join(job_summaries)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=SYSTEM_PROMPT.format(profile=config.CANDIDATE_PROFILE),
            messages=[{"role": "user", "content": user_msg}],
        )

        # Parse the JSON response
        text = response.content[0].text.strip()
        # Handle potential markdown wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        scores_by_id = {s["id"]: s for s in result.get("scores", [])}

        for job in batch:
            if job["id"] in scores_by_id:
                job["scores"] = scores_by_id[job["id"]]
            else:
                job["scores"] = {"overall": 5.0, "one_liner": "Not scored"}

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        print(f"[ranker] Scored {len(batch)} jobs — {input_tokens} in / {output_tokens} out tokens")

    except json.JSONDecodeError as e:
        print(f"[ranker] JSON parse error: {e}")
        for job in batch:
            job["scores"] = {"overall": 5.0, "one_liner": "Parse error during scoring"}
    except Exception as e:
        print(f"[ranker] Claude API error: {e}")
        for job in batch:
            job["scores"] = {"overall": 5.0, "one_liner": "API error during scoring"}

    return batch
