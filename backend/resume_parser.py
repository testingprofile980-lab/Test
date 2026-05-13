import re
import io
from typing import Optional
import pdfplumber
from docx import Document


TECH_SKILLS = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "swift", "kotlin",
    "react", "angular", "vue", "nextjs", "nodejs", "express", "django", "flask", "fastapi",
    "spring", "hibernate", "laravel", "rails", "asp.net",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
    "git", "linux", "bash", "nginx", "apache",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data science", "nlp", "computer vision", "opencv",
    "html", "css", "sass", "tailwind", "bootstrap", "webpack", "vite",
    "rest api", "graphql", "grpc", "microservices", "kafka", "rabbitmq",
    "figma", "photoshop", "ui/ux",
    "agile", "scrum", "jira", "confluence",
    "excel", "power bi", "tableau", "looker",
    "selenium", "cypress", "jest", "pytest", "junit",
    "blockchain", "solidity", "web3",
    "ios", "android", "flutter", "react native",
]

EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)",
    r"experience[:\s]*(\d+)\+?\s*years?",
    r"(\d+)\s*yrs?\s*(?:of\s*)?(?:experience|exp)",
]

EDUCATION_KEYWORDS = [
    "b.tech", "b.e", "bachelor", "b.sc", "b.com", "bca", "bba",
    "m.tech", "m.e", "master", "mca", "mba", "m.sc",
    "phd", "doctorate",
    "diploma", "12th", "10th",
]

FRESHER_SIGNALS = [
    "fresher", "fresh graduate", "recent graduate", "0 years", "entry level",
    "no experience", "internship", "seeking first job",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(set(found))


def extract_experience_years(text: str) -> Optional[int]:
    text_lower = text.lower()
    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    return None


def detect_fresher(text: str, years: Optional[int]) -> bool:
    if years is not None and years == 0:
        return True
    if years is None:
        text_lower = text.lower()
        for signal in FRESHER_SIGNALS:
            if signal in text_lower:
                return True
        # If no years found and recent education keywords present, assume fresher
        for kw in ["2023", "2024", "2025", "2026"]:
            if kw in text:
                return True
    return False


def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first = lines[0]
        if len(first.split()) <= 4 and not any(c.isdigit() for c in first):
            return first
    return "Candidate"


def extract_job_titles(text: str) -> list[str]:
    titles = []
    patterns = [
        r"(?:worked as|working as|position[:\s]+|title[:\s]+|role[:\s]+)\s*([A-Za-z ]+(?:Engineer|Developer|Analyst|Designer|Manager|Lead|Architect|Consultant|Intern|Scientist|Specialist))",
        r"\b((?:Senior|Junior|Lead|Principal|Staff)?\s*(?:Software|Frontend|Backend|Full.?Stack|Data|ML|AI|DevOps|Cloud|Mobile|Web)\s*(?:Engineer|Developer|Analyst|Scientist|Architect))\b",
        r"\b((?:Product|Project|Program)\s*Manager)\b",
        r"\b((?:UI|UX|UI\/UX)\s*Designer)\b",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        titles.extend([m.strip() for m in matches])
    return list(set(titles))[:5]


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith((".docx", ".doc")):
        text = extract_text_from_docx(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    skills = extract_skills(text)
    years = extract_experience_years(text)
    is_fresher = detect_fresher(text, years)
    name = extract_name(text)
    titles = extract_job_titles(text)

    return {
        "name": name,
        "skills": skills,
        "experience_years": years if years is not None else (0 if is_fresher else None),
        "is_fresher": is_fresher,
        "job_titles": titles,
        "raw_text_preview": text[:500],
    }
