"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SearchBar } from "@/components/SearchBar";
import { ResultsGrid } from "@/components/ResultsGrid";
import { HeroBackground } from "@/components/HeroBackground";
import { Navbar } from "@/components/Navbar";
import { ExampleQueries } from "@/components/ExampleQueries";
import { searchEpisodes, type SearchResponse, type SearchRequest } from "@/lib/api";

export default function Home() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async (req: SearchRequest) => {
    setLoading(true);
    setError(null);
    setCurrentQuery(req.query);
    setHasSearched(true);

    try {
      const data = await searchEpisodes(req);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed. Is the backend running?");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleExampleClick = (query: string) => {
    handleSearch({ query, limit: 10 });
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden">
      <HeroBackground />
      <Navbar />

      <div className="relative z-10">
        {/* Hero Section */}
        <section className="flex flex-col items-center justify-center min-h-[80vh] px-4 pt-20 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-12 max-w-4xl"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="inline-flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full glass border border-accent/20 text-sm font-mono text-accent"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-slow" />
              AI-Powered Episode Search
            </motion.div>

            {/* Title */}
            <h1 className="font-display text-[7rem] sm:text-[10rem] leading-none tracking-wide mb-4">
              <span className="text-gradient">RE</span>
              <span className="text-foreground">RUSH</span>
            </h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              className="text-muted-fg text-lg sm:text-xl font-body font-light max-w-2xl mx-auto leading-relaxed"
            >
              Can&apos;t remember the episode title? Just describe what you remember.
              <br />
              <span className="text-foreground/70">Our AI finds it across Friends, Seinfeld, The Office & more.</span>
            </motion.p>
          </motion.div>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="w-full max-w-3xl"
          >
            <SearchBar onSearch={handleSearch} loading={loading} />
          </motion.div>

          {/* Example Queries — only show when no search yet */}
          <AnimatePresence>
            {!hasSearched && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ delay: 0.7, duration: 0.5 }}
                className="mt-10 w-full max-w-3xl"
              >
                <ExampleQueries onSelect={handleExampleClick} />
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Results Section */}
        <AnimatePresence mode="wait">
          {(loading || results || error) && (
            <motion.section
              key="results"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.5 }}
              className="px-4 pb-20 max-w-7xl mx-auto"
            >
              {/* Results Header */}
              {!loading && results && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mb-8 flex items-center justify-between"
                >
                  <div>
                    <p className="text-muted-fg text-sm font-mono mb-1">RESULTS FOR</p>
                    <h2 className="text-foreground text-xl font-body font-medium">
                      &ldquo;{currentQuery}&rdquo;
                    </h2>
                  </div>
                  <div className="text-right">
                    <p className="text-muted-fg text-sm font-mono">
                      {results.count} episode{results.count !== 1 ? "s" : ""} found
                    </p>
                  </div>
                </motion.div>
              )}

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center justify-center py-20 text-center"
                >
                  <div className="w-16 h-16 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mb-4">
                    <span className="text-2xl">📡</span>
                  </div>
                  <h3 className="text-foreground text-lg font-body font-medium mb-2">Connection Error</h3>
                  <p className="text-muted-fg text-sm max-w-sm">{error}</p>
                  <p className="text-muted text-xs mt-3 font-mono">Make sure backend is running on port 8000</p>
                </motion.div>
              )}

              {/* Results Grid */}
              {!error && (
                <ResultsGrid results={results?.results ?? []} loading={loading} />
              )}
            </motion.section>
          )}
        </AnimatePresence>

        {/* Stats bar at bottom */}
        {!hasSearched && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="pb-16 px-4"
          >
            <div className="max-w-3xl mx-auto flex items-center justify-center gap-8 sm:gap-16 text-center">
              {[
                { value: "10K+", label: "Episodes Indexed" },
                { value: "8+", label: "Popular Shows" },
                { value: "384D", label: "Vector Embeddings" },
              ].map((stat) => (
                <div key={stat.label}>
                  <p className="font-display text-3xl text-gradient">{stat.value}</p>
                  <p className="text-muted-fg text-xs font-mono mt-0.5 uppercase tracking-widest">{stat.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}
