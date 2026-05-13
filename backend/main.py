from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from resume_parser import parse_resume
from job_scraper import scrape_linkedin_jobs, build_search_keywords

app = FastAPI(title="LinkedIn Job Matcher API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ManualProfileInput(BaseModel):
    name: str
    skills: list[str]
    experience_years: int
    total_experience: str
    expected_salary: str
    notice_period: str
    preferred_location: Optional[str] = "India"
    job_mode_preference: Optional[str] = None


class JobSearchRequest(BaseModel):
    keywords: str
    location: str = "India"
    is_fresher: bool = False
    job_mode: Optional[str] = None
    limit: int = 20


@app.get("/")
def root():
    return {"status": "ok", "message": "LinkedIn Job Matcher API"}


@app.post("/api/parse-resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, DOCX, or TXT.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    result = parse_resume(content, file.filename)
    return {"success": True, "profile": result}


@app.post("/api/manual-profile")
def manual_profile(data: ManualProfileInput):
    is_fresher = data.experience_years == 0
    job_titles = _infer_titles_from_skills(data.skills)
    return {
        "success": True,
        "profile": {
            "name": data.name,
            "skills": data.skills,
            "experience_years": data.experience_years,
            "total_experience": data.total_experience,
            "expected_salary": data.expected_salary,
            "notice_period": data.notice_period,
            "is_fresher": is_fresher,
            "job_titles": job_titles,
            "preferred_location": data.preferred_location,
            "job_mode_preference": data.job_mode_preference,
        },
    }


@app.post("/api/search-jobs")
def search_jobs(req: JobSearchRequest):
    jobs = scrape_linkedin_jobs(
        keywords=req.keywords,
        location=req.location,
        is_fresher=req.is_fresher,
        job_type=req.job_mode,
        limit=req.limit,
    )
    return {"success": True, "jobs": jobs, "total": len(jobs)}


@app.post("/api/match-jobs")
def match_jobs_from_profile(profile: dict):
    skills = profile.get("skills", [])
    job_titles = profile.get("job_titles", [])
    is_fresher = profile.get("is_fresher", False)
    location = profile.get("preferred_location", "India")
    job_mode = profile.get("job_mode_preference")

    keywords = build_search_keywords(skills, job_titles, is_fresher)
    jobs = scrape_linkedin_jobs(
        keywords=keywords,
        location=location,
        is_fresher=is_fresher,
        job_type=job_mode,
        limit=20,
    )
    return {"success": True, "jobs": jobs, "keywords_used": keywords, "total": len(jobs)}


def _infer_titles_from_skills(skills: list[str]) -> list[str]:
    skill_set = set(s.lower() for s in skills)
    titles = []
    if skill_set & {"react", "angular", "vue", "html", "css", "javascript", "typescript"}:
        titles.append("Frontend Developer")
    if skill_set & {"python", "django", "flask", "fastapi", "nodejs", "java", "spring"}:
        titles.append("Backend Developer")
    if skill_set & {"react", "nodejs", "python", "javascript"}:
        titles.append("Full Stack Developer")
    if skill_set & {"machine learning", "deep learning", "tensorflow", "pytorch", "data science"}:
        titles.append("Data Scientist")
    if skill_set & {"sql", "pandas", "numpy", "tableau", "power bi"}:
        titles.append("Data Analyst")
    if skill_set & {"aws", "docker", "kubernetes", "terraform", "jenkins"}:
        titles.append("DevOps Engineer")
    if not titles:
        titles.append("Software Developer")
    return titles[:3]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
