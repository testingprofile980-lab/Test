import requests
import re
import time
import random
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JOB_TYPE_MAP = {
    "full_time": "F",
    "part_time": "P",
    "contract": "C",
    "internship": "I",
}

EXPERIENCE_LEVEL_MAP = {
    "internship": "1",
    "entry": "2",
    "associate": "3",
    "mid_senior": "4",
    "director": "5",
    "executive": "6",
}


def build_search_keywords(skills: list[str], job_titles: list[str], is_fresher: bool) -> str:
    parts = []
    if job_titles:
        parts.append(job_titles[0])
    if skills:
        top_skills = skills[:4]
        parts.extend(top_skills)
    if is_fresher:
        parts.append("fresher")
    return " ".join(parts[:5]) if parts else "software developer"


def scrape_linkedin_jobs(
    keywords: str,
    location: str = "India",
    is_fresher: bool = False,
    job_type: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    jobs = []

    exp_level = "1,2" if is_fresher else "2,3,4"

    params = {
        "keywords": keywords,
        "location": location,
        "f_E": exp_level,
        "sortBy": "DD",
        "position": 1,
        "pageNum": 0,
    }

    if is_fresher:
        params["f_JT"] = "I,F"
    elif job_type:
        params["f_JT"] = JOB_TYPE_MAP.get(job_type, "F")

    url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"

    try:
        time.sleep(random.uniform(1, 2))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return _get_fallback_jobs(keywords, is_fresher, limit)

        soup = BeautifulSoup(resp.text, "lxml")
        job_cards = soup.find_all("div", class_=re.compile(r"base-card"))

        for card in job_cards[:limit]:
            try:
                title_el = card.find(["h3", "h4"], class_=re.compile(r"title|job-title"))
                company_el = card.find(["h4", "a"], class_=re.compile(r"company"))
                location_el = card.find("span", class_=re.compile(r"location"))
                link_el = card.find("a", class_=re.compile(r"base-card__full-link|job-card"))
                meta_el = card.find("li", class_=re.compile(r"job-criteria"))

                title = title_el.get_text(strip=True) if title_el else "Unknown Title"
                company = company_el.get_text(strip=True) if company_el else "Unknown Company"
                loc = location_el.get_text(strip=True) if location_el else location
                link = link_el.get("href", "#") if link_el else "#"
                job_mode = _infer_job_mode(loc, card.get_text())

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "job_mode": job_mode,
                    "apply_link": link.split("?")[0] if link != "#" else link,
                    "description": _extract_snippet(card),
                    "posted": _extract_posted_time(card),
                    "source": "LinkedIn",
                })
            except Exception:
                continue

    except Exception:
        return _get_fallback_jobs(keywords, is_fresher, limit)

    if not jobs:
        return _get_fallback_jobs(keywords, is_fresher, limit)

    return jobs


def _extract_snippet(card) -> str:
    desc = card.find("p", class_=re.compile(r"description|snippet"))
    if desc:
        return desc.get_text(strip=True)[:300]
    return ""


def _extract_posted_time(card) -> str:
    time_el = card.find("time")
    if time_el:
        return time_el.get("datetime", time_el.get_text(strip=True))
    span = card.find("span", class_=re.compile(r"listdate|posted"))
    return span.get_text(strip=True) if span else "Recently"


def _infer_job_mode(location: str, full_text: str) -> str:
    text = (location + " " + full_text).lower()
    if "remote" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    return "On-site"


def _get_fallback_jobs(keywords: str, is_fresher: bool, limit: int) -> list[dict]:
    """Returns demo jobs when scraping fails or is rate-limited."""
    templates = [
        {
            "title": "Software Engineer" if not is_fresher else "Software Engineer Intern",
            "company": "Tech Corp",
            "location": "Bengaluru, Karnataka",
            "job_mode": "Hybrid",
            "description": f"Looking for candidates with skills in {keywords}. Join our engineering team.",
            "posted": "2 days ago",
        },
        {
            "title": "Full Stack Developer" if not is_fresher else "Full Stack Developer - Fresher",
            "company": "Startup Labs",
            "location": "Remote",
            "job_mode": "Remote",
            "description": f"We need a passionate developer with {keywords} experience.",
            "posted": "1 day ago",
        },
        {
            "title": "Backend Developer" if not is_fresher else "Backend Intern",
            "company": "Unicorn Inc",
            "location": "Mumbai, Maharashtra",
            "job_mode": "On-site",
            "description": f"Backend role requiring {keywords}. Great growth opportunity.",
            "posted": "3 days ago",
        },
        {
            "title": "Data Engineer" if not is_fresher else "Data Science Intern",
            "company": "Analytics Co",
            "location": "Hyderabad, Telangana",
            "job_mode": "Hybrid",
            "description": f"Data engineering position using {keywords}.",
            "posted": "5 hours ago",
        },
        {
            "title": "DevOps Engineer" if not is_fresher else "Cloud Intern",
            "company": "Cloud Systems",
            "location": "Pune, Maharashtra",
            "job_mode": "Remote",
            "description": f"DevOps role requiring {keywords} expertise.",
            "posted": "1 week ago",
        },
        {
            "title": "Frontend Developer" if not is_fresher else "UI Developer Trainee",
            "company": "Creative Tech",
            "location": "Chennai, Tamil Nadu",
            "job_mode": "On-site",
            "description": f"Frontend role using {keywords}.",
            "posted": "4 days ago",
        },
    ]

    search_kw = quote_plus(keywords)
    jobs = []
    for i, t in enumerate(templates[:limit]):
        exp = "internship" if is_fresher else "2"
        jobs.append({
            **t,
            "apply_link": f"https://www.linkedin.com/jobs/search/?keywords={search_kw}&f_E={exp}",
            "source": "LinkedIn (Demo)",
        })
    return jobs
