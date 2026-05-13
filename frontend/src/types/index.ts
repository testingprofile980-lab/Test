export interface Profile {
  name: string;
  skills: string[];
  experience_years: number;
  total_experience?: string;
  expected_salary?: string;
  notice_period?: string;
  is_fresher: boolean;
  job_titles: string[];
  preferred_location?: string;
  job_mode_preference?: string;
  raw_text_preview?: string;
}

export interface Job {
  title: string;
  company: string;
  location: string;
  job_mode: "Remote" | "Hybrid" | "On-site";
  apply_link: string;
  description: string;
  posted: string;
  source: string;
}

export type InputMode = "landing" | "resume" | "manual" | "results";
export type JobModeFilter = "All" | "Remote" | "Hybrid" | "On-site";
