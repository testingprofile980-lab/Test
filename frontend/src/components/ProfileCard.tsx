import { User, Briefcase, MapPin, Clock, DollarSign } from "lucide-react";
import type { Profile } from "../types";

interface Props {
  profile: Profile;
}

export default function ProfileCard({ profile }: Props) {
  return (
    <div className="card animate-slide-up">
      <div className="flex items-start gap-4">
        <div className="bg-linkedin-blue rounded-full p-3 flex-shrink-0">
          <User size={24} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-bold text-gray-900">{profile.name}</h3>
            {profile.is_fresher && (
              <span className="bg-green-100 text-green-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                Fresher
              </span>
            )}
            {!profile.is_fresher && profile.experience_years != null && (
              <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                {profile.experience_years}y exp
              </span>
            )}
          </div>

          {profile.job_titles.length > 0 && (
            <div className="flex items-center gap-1 mt-1">
              <Briefcase size={13} className="text-gray-400" />
              <p className="text-sm text-gray-500">{profile.job_titles.join(" · ")}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-4 mt-3">
            {profile.preferred_location && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <MapPin size={12} /> {profile.preferred_location}
              </div>
            )}
            {profile.notice_period && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Clock size={12} /> {profile.notice_period} notice
              </div>
            )}
            {profile.expected_salary && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <DollarSign size={12} /> {profile.expected_salary}
              </div>
            )}
          </div>
        </div>
      </div>

      {profile.skills.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
            Detected Skills ({profile.skills.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {profile.skills.map((s) => (
              <span key={s} className="skill-tag capitalize">{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
