"use client";

import { useState } from "react";
import { AnimatedSphere } from "@/components/landing/animated-sphere";

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    summary?: string;
    dashboard_url?: string;
    status?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/query/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f5f4f0]">

      {/* Grid lines */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-40">
        {[...Array(8)].map((_, i) => (
          <div key={`h-${i}`} className="absolute h-px bg-black/10"
            style={{ top: `${12.5 * (i + 1)}%`, left: 0, right: 0 }} />
        ))}
        {[...Array(12)].map((_, i) => (
          <div key={`v-${i}`} className="absolute w-px bg-black/10"
            style={{ left: `${8.33 * (i + 1)}%`, top: 0, bottom: 0 }} />
        ))}
      </div>

      {/* Animated sphere — large, right side, vertically centered */}
      <div className="absolute right-[-80px] top-1/2 -translate-y-1/2 w-[750px] h-[750px] lg:w-[950px] lg:h-[950px] opacity-60 pointer-events-none">
        <AnimatedSphere />
      </div>

      {/* Logo top left */}
      <div className="relative z-10 px-10 lg:px-16 pt-8">
        <span className="text-xl font-sans font-medium tracking-tight text-black">BioOracle</span>
      </div>

      {/* Left content — vertically centered */}
      <div className="absolute left-10 lg:left-20 top-1/2 -translate-y-1/2 z-10 w-full max-w-xl lg:max-w-2xl">

        {/* Tagline */}
        <p className="text-sm text-black/40 font-mono mb-4 flex items-center gap-2">
          <span className="inline-block w-8 h-px bg-black/30" />
          The platform for biomedical intelligence
        </p>

        {/* Main heading */}
        <h1 className="text-6xl lg:text-7xl font-sans font-semibold tracking-tight text-black leading-[1.05] mb-6">
          Where{" "}
          <span className="text-glow-sweep">Medical Literature</span>
          <br />
          Becomes Intelligence.
        </h1>

        {/* Subtext */}
        <p className="text-base lg:text-lg text-black/50 mb-10 max-w-lg leading-relaxed">
          Ask a biomedical question. BioOracle fetches, processes, and visualizes the research — automatically.
        </p>

        {/* Chatbox */}
        <div className="relative bg-white rounded-2xl shadow-md border border-black/10 p-5 max-w-lg">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask to create medical dashboards..."
            className="w-full resize-none bg-transparent text-black placeholder:text-black/30 focus:outline-none text-base min-h-[80px]"
            rows={3}
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="absolute bottom-5 right-5 w-10 h-10 bg-black rounded-full flex items-center justify-center hover:bg-black/80 transition-colors disabled:opacity-30"
          >
            {loading ? (
              <svg className="animate-spin text-white" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                className="text-white">
                <path d="M12 19V5" /><path d="m5 12 7-7 7 7" />
              </svg>
            )}
          </button>
        </div>

        {/* Result area */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 max-w-lg">
            {error}
          </div>
        )}
        {result && (
          <div className="mt-4 p-4 bg-white border border-black/10 rounded-xl text-sm text-black space-y-2 max-w-lg">
            {result.summary && <p>{result.summary}</p>}
            {result.dashboard_url && (
              <a href={`${API_BASE}${result.dashboard_url}`}
                target="_blank" rel="noopener noreferrer"
                className="inline-block mt-1 underline underline-offset-2 font-medium">
                View Dashboard →
              </a>
            )}
            <span className={`text-xs px-2 py-0.5 rounded-full border ${result.status === "success" ? "border-green-300 text-green-700" : "border-yellow-300 text-yellow-700"}`}>
              {result.status}
            </span>
          </div>
        )}
      </div>
    </main>
  );
}