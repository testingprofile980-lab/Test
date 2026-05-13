import { useState } from "react";
import Header from "./components/Header";
import LandingPage from "./components/LandingPage";
import ResumeUpload from "./components/ResumeUpload";
import ManualInput from "./components/ManualInput";
import JobDashboard from "./components/JobDashboard";
import type { InputMode, Profile } from "./types";

export default function App() {
  const [mode, setMode] = useState<InputMode>("landing");
  const [profile, setProfile] = useState<Profile | null>(null);

  const handleProfileReady = (p: Profile) => {
    setProfile(p);
    setMode("results");
  };

  const handleReset = () => {
    setProfile(null);
    setMode("landing");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1">
        {mode === "landing" && <LandingPage onSelect={setMode} />}
        {mode === "resume" && (
          <ResumeUpload onParsed={handleProfileReady} onBack={() => setMode("landing")} />
        )}
        {mode === "manual" && (
          <ManualInput onSubmit={handleProfileReady} onBack={() => setMode("landing")} />
        )}
        {mode === "results" && profile && (
          <JobDashboard profile={profile} onReset={handleReset} />
        )}
      </main>

      <footer className="border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400">
        JobMatch — LinkedIn Job Matcher · Built for job seekers
      </footer>
    </div>
  );
}
