import { useState } from "react";
import { ArrowLeft, Plus, X, Loader2, AlertCircle } from "lucide-react";
import axios from "axios";
import toast from "react-hot-toast";
import type { Profile } from "../types";

interface Props {
  onSubmit: (profile: Profile) => void;
  onBack: () => void;
}

const POPULAR_SKILLS = [
  "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++",
  "SQL", "AWS", "Docker", "Machine Learning", "Data Analysis", "Spring Boot",
  "Flutter", "Angular", "Vue.js", "Django", "FastAPI", "Kubernetes", "Git",
];

const NOTICE_OPTIONS = ["Immediate", "15 days", "30 days", "45 days", "60 days", "90 days"];
const JOB_MODE_OPTIONS = ["Any", "Remote", "Hybrid", "On-site"];

export default function ManualInput({ onSubmit, onBack }: Props) {
  const [name, setName] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [expYears, setExpYears] = useState(0);
  const [totalExp, setTotalExp] = useState("");
  const [salary, setSalary] = useState("");
  const [noticePeriod, setNoticePeriod] = useState("30 days");
  const [location, setLocation] = useState("India");
  const [jobMode, setJobMode] = useState("Any");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const addSkill = (skill: string) => {
    const trimmed = skill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
    }
    setSkillInput("");
  };

  const removeSkill = (s: string) => setSkills(skills.filter((x) => x !== s));

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(skillInput);
    }
  };

  const handleSubmit = async () => {
    if (!name.trim()) return setError("Please enter your name.");
    if (skills.length === 0) return setError("Add at least one skill.");
    setError("");
    setLoading(true);

    try {
      const payload = {
        name: name.trim(),
        skills,
        experience_years: expYears,
        total_experience: totalExp || `${expYears} years`,
        expected_salary: salary,
        notice_period: noticePeriod,
        preferred_location: location,
        job_mode_preference: jobMode === "Any" ? null : jobMode.toLowerCase().replace("-", "_"),
      };
      const res = await axios.post("/api/manual-profile", payload);
      toast.success("Profile created!");
      onSubmit(res.data.profile);
    } catch {
      const msg = "Failed to connect. Ensure backend is running on port 8000.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 animate-fade-in">
      <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-gray-800 mb-6 text-sm">
        <ArrowLeft size={16} /> Back
      </button>

      <div className="card space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Your Profile</h2>
          <p className="text-gray-500 text-sm mt-1">Tell us about yourself to find matching jobs.</p>
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
          <input
            className="input-field"
            placeholder="e.g. Rahul Sharma"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        {/* Experience */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Years of Experience *</label>
            <select
              className="input-field"
              value={expYears}
              onChange={(e) => setExpYears(Number(e.target.value))}
            >
              <option value={0}>0 (Fresher)</option>
              {Array.from({ length: 25 }, (_, i) => i + 1).map((y) => (
                <option key={y} value={y}>{y} {y === 1 ? "year" : "years"}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Total Experience (text)</label>
            <input
              className="input-field"
              placeholder="e.g. 2 years 3 months"
              value={totalExp}
              onChange={(e) => setTotalExp(e.target.value)}
            />
          </div>
        </div>

        {expYears === 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700 flex items-center gap-2">
            <span className="text-blue-500 font-bold">i</span>
            As a fresher, we'll search for internship and entry-level positions specifically.
          </div>
        )}

        {/* Skills */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Skills *</label>
          <div className="flex gap-2 mb-2">
            <input
              className="input-field flex-1"
              placeholder="Type a skill and press Enter"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              type="button"
              onClick={() => addSkill(skillInput)}
              className="btn-primary px-3 py-2 flex items-center"
            >
              <Plus size={18} />
            </button>
          </div>

          {/* Popular skills */}
          <div className="flex flex-wrap gap-2 mb-3">
            {POPULAR_SKILLS.filter((s) => !skills.includes(s)).slice(0, 10).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => addSkill(s)}
                className="text-xs border border-gray-200 text-gray-600 px-2.5 py-1 rounded-full hover:border-linkedin-blue hover:text-linkedin-blue transition-colors"
              >
                + {s}
              </button>
            ))}
          </div>

          {/* Added skills */}
          {skills.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {skills.map((s) => (
                <span key={s} className="skill-tag gap-1.5">
                  {s}
                  <button type="button" onClick={() => removeSkill(s)} className="hover:text-red-500">
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Salary & Notice */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Expected Salary (LPA)</label>
            <input
              className="input-field"
              placeholder="e.g. 8-12 LPA"
              value={salary}
              onChange={(e) => setSalary(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notice Period</label>
            <select className="input-field" value={noticePeriod} onChange={(e) => setNoticePeriod(e.target.value)}>
              {NOTICE_OPTIONS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
        </div>

        {/* Location & Mode */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Location</label>
            <input
              className="input-field"
              placeholder="e.g. Bengaluru, India"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Mode Preference</label>
            <select className="input-field" value={jobMode} onChange={(e) => setJobMode(e.target.value)}>
              {JOB_MODE_OPTIONS.map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 text-red-600 text-sm bg-red-50 rounded-lg p-3">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" /> Finding Jobs...
            </>
          ) : (
            "Find Matching Jobs →"
          )}
        </button>
      </div>
    </div>
  );
}
