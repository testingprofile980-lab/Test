import { useState, useEffect } from "react";
import { Search, Loader2, RefreshCw, Filter, RotateCcw } from "lucide-react";
import axios from "axios";
import toast from "react-hot-toast";
import type { Profile, Job, JobModeFilter } from "../types";
import ProfileCard from "./ProfileCard";
import JobCard from "./JobCard";

interface Props {
  profile: Profile;
  onReset: () => void;
}

export default function JobDashboard({ profile, onReset }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [keywords, setKeywords] = useState("");
  const [usedKeywords, setUsedKeywords] = useState("");
  const [modeFilter, setModeFilter] = useState<JobModeFilter>("All");
  const [searchLocation, setSearchLocation] = useState(profile.preferred_location || "India");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async (customKeywords?: string) => {
    setLoading(true);
    try {
      const payload = {
        ...profile,
        preferred_location: searchLocation,
      };

      let res;
      if (customKeywords) {
        res = await axios.post("/api/search-jobs", {
          keywords: customKeywords,
          location: searchLocation,
          is_fresher: profile.is_fresher,
          job_mode: profile.job_mode_preference ?? null,
          limit: 20,
        });
        setUsedKeywords(customKeywords);
      } else {
        res = await axios.post("/api/match-jobs", payload);
        setUsedKeywords(res.data.keywords_used || "");
      }

      setJobs(res.data.jobs || []);
      setSearched(true);
      toast.success(`Found ${res.data.total || 0} jobs!`);
    } catch {
      toast.error("Could not fetch jobs. Is the backend running?");
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (keywords.trim()) fetchJobs(keywords.trim());
    else fetchJobs();
  };

  const filteredJobs = modeFilter === "All" ? jobs : jobs.filter((j) => j.job_mode === modeFilter);

  const modeCounts: Record<string, number> = { All: jobs.length };
  for (const j of jobs) modeCounts[j.job_mode] = (modeCounts[j.job_mode] ?? 0) + 1;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
          {profile.is_fresher && (
            <p className="text-sm text-green-600 font-medium mt-0.5">
              Showing fresher & internship roles
            </p>
          )}
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 border border-gray-200 px-4 py-2 rounded-full"
        >
          <RotateCcw size={14} /> Start Over
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar */}
        <div className="space-y-4">
          <ProfileCard profile={profile} />

          {/* Search Controls */}
          <div className="card space-y-3">
            <h4 className="font-semibold text-gray-700 text-sm flex items-center gap-2">
              <Search size={14} /> Search Jobs
            </h4>
            <input
              className="input-field text-sm"
              placeholder="Keywords, role, skills..."
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <input
              className="input-field text-sm"
              placeholder="Location"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="btn-primary w-full text-sm flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Filter by Mode */}
          <div className="card">
            <h4 className="font-semibold text-gray-700 text-sm flex items-center gap-2 mb-3">
              <Filter size={14} /> Job Mode
            </h4>
            <div className="space-y-1.5">
              {(["All", "Remote", "Hybrid", "On-site"] as JobModeFilter[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setModeFilter(mode)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                    modeFilter === mode
                      ? "bg-linkedin-light text-linkedin-blue font-semibold"
                      : "text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <span>{mode}</span>
                  <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                    {modeCounts[mode] ?? 0}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {usedKeywords && (
            <div className="card">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">Keywords Used</p>
              <p className="text-sm text-gray-600">{usedKeywords}</p>
            </div>
          )}
        </div>

        {/* Job Listings */}
        <div className="lg:col-span-2">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 size={40} className="animate-spin text-linkedin-blue" />
              <p className="text-gray-500 font-medium">Searching LinkedIn for matching jobs...</p>
              <p className="text-sm text-gray-400">This may take a few seconds</p>
            </div>
          ) : !searched ? null : filteredJobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
              <Search size={48} className="text-gray-200" />
              <p className="text-gray-500 font-medium">No jobs found for this filter</p>
              <button onClick={() => setModeFilter("All")} className="btn-outline text-sm">
                Show All Modes
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Showing <span className="font-semibold text-gray-800">{filteredJobs.length}</span> jobs
                  {modeFilter !== "All" && ` · ${modeFilter}`}
                </p>
                <button
                  onClick={() => fetchJobs()}
                  className="flex items-center gap-1.5 text-xs text-linkedin-blue hover:text-linkedin-dark"
                >
                  <RefreshCw size={12} /> Refresh
                </button>
              </div>
              {filteredJobs.map((job, i) => (
                <JobCard key={`${job.company}-${job.title}-${i}`} job={job} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
