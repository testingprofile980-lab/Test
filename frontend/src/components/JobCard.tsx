import { Building2, MapPin, ExternalLink, Clock, Wifi, Building, Globe } from "lucide-react";
import type { Job } from "../types";

interface Props {
  job: Job;
  index: number;
}

const MODE_CONFIG = {
  Remote: { color: "bg-green-100 text-green-700", icon: Globe },
  Hybrid: { color: "bg-yellow-100 text-yellow-700", icon: Wifi },
  "On-site": { color: "bg-blue-100 text-blue-700", icon: Building },
};

export default function JobCard({ job, index }: Props) {
  const modeConf = MODE_CONFIG[job.job_mode] ?? MODE_CONFIG["On-site"];
  const ModeIcon = modeConf.icon;

  return (
    <div
      className="card hover:shadow-md hover:border-linkedin-blue transition-all duration-200 animate-slide-up group"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Company Logo Placeholder */}
          <div className="bg-gray-100 group-hover:bg-linkedin-light rounded-lg p-2.5 flex-shrink-0 transition-colors">
            <Building2 size={22} className="text-gray-400 group-hover:text-linkedin-blue transition-colors" />
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-base leading-tight truncate">
              {job.title}
            </h3>
            <p className="text-sm text-gray-600 font-medium mt-0.5">{job.company}</p>

            <div className="flex flex-wrap items-center gap-3 mt-2">
              <div className="flex items-center gap-1 text-xs text-gray-400">
                <MapPin size={11} /> {job.location}
              </div>
              <div className="flex items-center gap-1 text-xs text-gray-400">
                <Clock size={11} /> {job.posted}
              </div>
              <span className={`job-mode-badge flex items-center gap-1 ${modeConf.color}`}>
                <ModeIcon size={11} /> {job.job_mode}
              </span>
            </div>
          </div>
        </div>

        <a
          href={job.apply_link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 bg-linkedin-blue text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-linkedin-dark transition-colors flex-shrink-0"
        >
          Apply <ExternalLink size={12} />
        </a>
      </div>

      {job.description && (
        <p className="mt-3 text-sm text-gray-500 line-clamp-2 border-t border-gray-50 pt-3">
          {job.description}
        </p>
      )}

      <div className="mt-2 flex items-center justify-between">
        <span className="text-[11px] text-gray-300">{job.source}</span>
      </div>
    </div>
  );
}
