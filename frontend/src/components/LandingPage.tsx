import { Upload, PenLine, CheckCircle } from "lucide-react";
import type { InputMode } from "../types";

interface Props {
  onSelect: (mode: InputMode) => void;
}

export default function LandingPage({ onSelect }: Props) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12 animate-fade-in">
      <div className="text-center mb-12 max-w-2xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Find Your <span className="text-linkedin-blue">Perfect Job</span> on LinkedIn
        </h1>
        <p className="text-lg text-gray-500">
          Upload your resume or fill in your details. We'll match you with active LinkedIn jobs
          tailored to your skills and experience level.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
        <button
          onClick={() => onSelect("resume")}
          className="group card hover:shadow-lg hover:border-linkedin-blue transition-all duration-300 text-left cursor-pointer border-2"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-linkedin-light group-hover:bg-linkedin-blue p-3 rounded-xl transition-colors">
              <Upload size={28} className="text-linkedin-blue group-hover:text-white transition-colors" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Upload Resume</h2>
              <p className="text-sm text-gray-400">PDF, DOCX, or TXT</p>
            </div>
          </div>
          <p className="text-gray-600 text-sm mb-4">
            We'll automatically extract your skills, experience, and job history to find the best matching roles.
          </p>
          <ul className="space-y-2">
            {["Auto-detect skills & experience", "Fresher/experienced detection", "Smart keyword extraction"].map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm text-gray-500">
                <CheckCircle size={15} className="text-green-500 flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
          <div className="mt-5">
            <span className="btn-primary text-sm inline-block">Upload Resume →</span>
          </div>
        </button>

        <button
          onClick={() => onSelect("manual")}
          className="group card hover:shadow-lg hover:border-linkedin-blue transition-all duration-300 text-left cursor-pointer border-2"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-purple-50 group-hover:bg-purple-600 p-3 rounded-xl transition-colors">
              <PenLine size={28} className="text-purple-600 group-hover:text-white transition-colors" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Fill Manually</h2>
              <p className="text-sm text-gray-400">No resume needed</p>
            </div>
          </div>
          <p className="text-gray-600 text-sm mb-4">
            Enter your skills, years of experience, expected salary, and notice period to get matched instantly.
          </p>
          <ul className="space-y-2">
            {["Add skills & experience manually", "Set salary expectations", "Specify notice period"].map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm text-gray-500">
                <CheckCircle size={15} className="text-green-500 flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
          <div className="mt-5">
            <span className="btn-outline text-sm inline-block">Fill Details →</span>
          </div>
        </button>
      </div>

      <p className="mt-10 text-xs text-gray-400 text-center max-w-lg">
        Job listings are sourced from LinkedIn's public job board. We do not store your resume or personal data.
      </p>
    </div>
  );
}
