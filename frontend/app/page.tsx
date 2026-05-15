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
    <main className="relative min-h-screen overflow-hidden">
      {/* Grid lines */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
        {[...Array(8)].map((_, i) => (
          <div key={`h-${i}`} className="absolute h-px bg-foreground/10"
            style={{ top: `${12.5 * (i + 1)}%`, left: 0, right: 0 }} />
        ))}
        {[...Array(12)].map((_, i) => (
          <div key={`v-${i}`} className="absolute w-px bg-foreground/10"
            style={{ left: `${8.33 * (i + 1)}%`, top: 0, bottom: 0 }} />
        ))}
      </div>

      {/* Animated sphere */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[600px] h-[600px] lg:w-[800px] lg:h-[800px] opacity-40 pointer-events-none">
        <AnimatedSphere />
      </div>

      {/* Logo */}
      <div className="relative z-10 px-8 lg:px-16 pt-8">
        <span className="text-2xl font-display tracking-tight">BioOracle</span>
      </div>

      {/* Left content */}
      <div className="absolute left-16 lg:left-32 top-1/2 -translate-y-1/2 z-10 w-full max-w-lg lg:max-w-xl">
        <h1 className="text-4xl lg:text-5xl font-semibold tracking-tight text-foreground mb-10">
          Where <span className="text-glow-sweep">Medical Literature</span> Becomes Intelligence.
        </h1>

        {/* Chatbox */}
        <div className="relative bg-white rounded-2xl shadow-lg border border-foreground/10 p-5">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask to create medical dashboards..."
            className="w-full resize-none bg-transparent text-foreground placeholder:text-foreground/40 focus:outline-none text-lg min-h-[70px]"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="absolute bottom-5 right-5 w-11 h-11 bg-foreground rounded-full flex items-center justify-center hover:bg-foreground/90 transition-colors disabled:opacity-40"
          >
            {loading ? (
              <svg className="animate-spin text-background" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="text-background">
                <path d="M12 19V5" /><path d="m5 12 7-7 7 7" />
              </svg>
            )}
          </button>
        </div>

        {/* Result area */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
            {error}
          </div>
        )}
        {result && (
          <div className="mt-4 p-4 bg-white/80 border border-foreground/10 rounded-xl text-sm text-foreground space-y-2 backdrop-blur">
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