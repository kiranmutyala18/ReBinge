"use client";

import { motion } from "framer-motion";
import { EpisodeCard } from "@/components/EpisodeCard";
import { EpisodeCardSkeleton } from "@/components/EpisodeCardSkeleton";
import type { SearchResultItem } from "@/lib/api";

interface ResultsGridProps {
  results: SearchResultItem[];
  loading: boolean;
}

export function ResultsGrid({ results, loading }: ResultsGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <EpisodeCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-20 text-center"
      >
        <div className="w-16 h-16 rounded-full bg-surface-2 border border-border flex items-center justify-center mb-4 text-2xl">
          🎬
        </div>
        <h3 className="text-foreground font-body font-medium mb-2">No episodes found</h3>
        <p className="text-muted-fg text-sm">Try a different description or lower the similarity threshold</p>
      </motion.div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {results.map((result, i) => (
        <EpisodeCard key={result.id} result={result} index={i} />
      ))}
    </div>
  );
}
