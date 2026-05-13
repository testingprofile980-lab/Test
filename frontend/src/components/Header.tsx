import { Briefcase } from "lucide-react";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="bg-linkedin-blue rounded-lg p-1.5">
            <Briefcase size={20} className="text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">
            Job<span className="text-linkedin-blue">Match</span>
          </span>
        </div>
        <span className="text-xs bg-linkedin-light text-linkedin-blue px-2 py-0.5 rounded-full font-medium ml-1">
          LinkedIn Powered
        </span>
      </div>
    </header>
  );
}
