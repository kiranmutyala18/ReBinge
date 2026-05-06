"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, SlidersHorizontal, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { POPULAR_SHOWS } from "@/lib/utils";
import type { SearchRequest } from "@/lib/api";

interface SearchBarProps {
  onSearch: (req: SearchRequest) => void;
  loading: boolean;
}

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedShow, setSelectedShow] = useState<string>("");
  const [limit, setLimit] = useState(10);
  const [minSimilarity, setMinSimilarity] = useState(0.3);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (!query.trim() || loading) return;
    onSearch({
      query: query.trim(),
      limit,
      show_name: selectedShow || undefined,
      min_similarity: minSimilarity,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full">
      {/* Main search box */}
      <div
        className={cn(
          "relative rounded-2xl transition-all duration-300",
          "glass cinematic-border",
          "focus-within:border-accent/40 focus-within:shadow-[0_0_40px_rgba(230,57,70,0.15)]"
        )}
      >
        {/* Search icon */}
        <div className="absolute left-5 top-5 text-muted-fg">
          {loading ? (
            <Loader2 size={20} className="animate-spin text-accent" />
          ) : (
            <Search size={20} />
          )}
        </div>

        {/* Textarea */}
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the episode… "the one where they all get snowed in and secrets come out""
          rows={2}
          className={cn(
            "w-full bg-transparent text-foreground placeholder:text-muted",
            "pl-14 pr-28 py-5 resize-none",
            "font-body text-base leading-relaxed",
            "focus:outline-none"
          )}
        />

        {/* Right actions */}
        <div className="absolute right-4 top-4 flex items-center gap-2">
          {query && (
            <button
              onClick={() => setQuery("")}
              className="w-7 h-7 rounded-lg flex items-center justify-center text-muted-fg hover:text-foreground transition-colors"
            >
              <X size={14} />
            </button>
          )}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center transition-all",
              showFilters
                ? "bg-accent/20 text-accent border border-accent/30"
                : "glass text-muted-fg hover:text-foreground"
            )}
          >
            <SlidersHorizontal size={14} />
          </button>
          <button
            onClick={handleSubmit}
            disabled={!query.trim() || loading}
            className={cn(
              "px-5 py-2 rounded-xl font-body font-medium text-sm transition-all duration-200",
              "bg-accent hover:bg-accent-2 text-white",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              "shadow-[0_0_20px_rgba(230,57,70,0.3)] hover:shadow-[0_0_30px_rgba(230,57,70,0.5)]"
            )}
          >
            Find it
          </button>
        </div>
      </div>

      {/* Filters panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-3 p-5 rounded-2xl glass cinematic-border space-y-5">
              {/* Show filter */}
              <div>
                <label className="text-xs font-mono text-muted-fg uppercase tracking-widest mb-3 block">
                  Filter by Show
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setSelectedShow("")}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-body transition-all",
                      !selectedShow
                        ? "bg-accent/20 text-accent border border-accent/30"
                        : "glass text-muted-fg hover:text-foreground cinematic-border"
                    )}
                  >
                    All Shows
                  </button>
                  {POPULAR_SHOWS.map((show) => (
                    <button
                      key={show}
                      onClick={() => setSelectedShow(show === selectedShow ? "" : show)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-sm font-body transition-all",
                        selectedShow === show
                          ? "bg-accent/20 text-accent border border-accent/30"
                          : "glass text-muted-fg hover:text-foreground cinematic-border"
                      )}
                    >
                      {show}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-5">
                {/* Result limit */}
                <div>
                  <label className="text-xs font-mono text-muted-fg uppercase tracking-widest mb-2 block">
                    Results: <span className="text-foreground">{limit}</span>
                  </label>
                  <input
                    type="range"
                    min={3}
                    max={20}
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="w-full accent-accent"
                  />
                </div>

                {/* Min similarity */}
                <div>
                  <label className="text-xs font-mono text-muted-fg uppercase tracking-widest mb-2 block">
                    Min Match: <span className="text-foreground">{Math.round(minSimilarity * 100)}%</span>
                  </label>
                  <input
                    type="range"
                    min={10}
                    max={80}
                    value={minSimilarity * 100}
                    onChange={(e) => setMinSimilarity(Number(e.target.value) / 100)}
                    className="w-full accent-accent"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
