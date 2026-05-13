import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Loader2, ArrowLeft, AlertCircle } from "lucide-react";
import axios from "axios";
import toast from "react-hot-toast";
import type { Profile } from "../types";

interface Props {
  onParsed: (profile: Profile) => void;
  onBack: () => void;
}

export default function ResumeUpload({ onParsed, onBack }: Props) {
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      setError("");
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/msword": [".doc"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
    onDropRejected: () => setError("Invalid file. Please upload a PDF, DOCX, or TXT under 5MB."),
  });

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("/api/parse-resume", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Resume parsed successfully!");
      onParsed(res.data.profile);
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : "Failed to parse resume. Please check the backend is running.";
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

      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Upload Your Resume</h2>
        <p className="text-gray-500 text-sm mb-6">
          We'll extract your skills, experience level, and job history automatically.
        </p>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200
            ${isDragActive ? "border-linkedin-blue bg-linkedin-light drop-zone-active" : "border-gray-300 hover:border-linkedin-blue hover:bg-gray-50"}`}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="flex flex-col items-center gap-3">
              <FileText size={48} className="text-linkedin-blue" />
              <p className="font-semibold text-gray-800">{file.name}</p>
              <p className="text-sm text-gray-400">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload size={48} className={isDragActive ? "text-linkedin-blue" : "text-gray-300"} />
              <p className="text-gray-700 font-medium">
                {isDragActive ? "Drop it here!" : "Drag & drop your resume here"}
              </p>
              <p className="text-sm text-gray-400">or click to browse</p>
              <p className="text-xs text-gray-300 mt-2">PDF, DOCX, TXT · Max 5MB</p>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2 text-red-600 text-sm bg-red-50 rounded-lg p-3">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="btn-primary w-full mt-6 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" /> Analyzing Resume...
            </>
          ) : (
            "Analyze & Find Jobs"
          )}
        </button>
      </div>
    </div>
  );
}
