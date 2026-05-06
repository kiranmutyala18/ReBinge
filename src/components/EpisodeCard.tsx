"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { ExternalLink, Calendar, Tv } from "lucide-react";
import { cn, formatEpisodeCode, formatSimilarity, getSimilarityColor, stripHtml } from "@/lib/utils";
import type { SearchResultItem } from "@/lib/api";

interface EpisodeCardProps {
  result: SearchResultItem;
  index: number;
}

export function EpisodeCard({ result, index }: EpisodeCardProps) {
  const [imgError, setImgError] = useState(false);
  const episodeCode = formatEpisodeCode(result.season, result.episode_number);
  const similarityText = formatSimilarity(result.similarity_score);
  const similarityColor = getSimilarityColor(result.similarity_score);
  const summary = result.summary ? stripHtml(result.summary) : null;

  // Color accent per show
  const showColors: Record<string, string> = {
    "Friends": "rgba(255,200,100,0.15)",
    "Seinfeld": "rgba(100,180,255,0.1)",
    "The Office": "rgba(100,200,150,0.1)",
    "Parks and Recreation": "rgba(200,150,255,0.1)",
    "Brooklyn Nine-Nine": "rgba(100,150,255,0.1)",
  };
  const cardAccent = showColors[result.show_name] ?? "rgba(230,57,70,0.08)";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "group relative rounded-2xl overflow-hidden",
        "glass cinematic-border",
        "hover:border-white/10 transition-all duration-300",
        "hover:shadow-[0_8px_40px_rgba(0,0,0,0.4)]"
      )}
      style={{ background: `linear-gradient(135deg, ${cardAccent}, rgba(14,14,26,0.95))` }}
    >
      {/* Similarity badge */}
      <div className="absolute top-3 right-3 z-10">
        <div className={cn(
          "px-2.5 py-1 rounded-lg glass text-xs font-mono font-medium",
          "border border-white/10",
          similarityColor
        )}>
          {similarityText} match
        </div>
      </div>

      {/* Episode image */}
      {result.image_url && !imgError ? (
        <div className="relative w-full h-40 overflow-hidden">
          <Image
            src={result.image_url}
            alt={result.title}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            onError={() => setImgError(true)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0e0e1a] via-transparent to-transparent" />
          {/* Episode code overlay */}
          <div className="absolute bottom-2 left-3">
            <span className="font-mono text-xs text-foreground/60 bg-black/40 px-2 py-0.5 rounded-md">
              {episodeCode}
            </span>
          </div>
        </div>
      ) : (
        <div className="relative w-full h-24 bg-surface-2 flex items-center justify-center overflow-hidden">
          <div className="text-3xl opacity-20">📺</div>
          <div className="absolute bottom-2 left-3">
            <span className="font-mono text-xs text-foreground/60 bg-black/40 px-2 py-0.5 rounded-md">
              {episodeCode}
            </span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4 space-y-2">
        {/* Show name */}
        <div className="flex items-center gap-1.5">
          <Tv size={11} className="text-muted-fg flex-shrink-0" />
          <span className="text-xs font-mono text-muted-fg uppercase tracking-wider truncate">
            {result.show_name}
          </span>
        </div>

        {/* Episode title */}
        <h3 className="text-foreground font-body font-semibold text-base leading-tight line-clamp-2 group-hover:text-white transition-colors">
          {result.title}
        </h3>

        {/* Summary */}
        {summary && (
          <p className="text-muted-fg text-sm leading-relaxed line-clamp-3 font-body font-light">
            {summary}
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-white/5">
          {result.air_date && (
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <Calendar size={11} />
              <span>{new Date(result.air_date).getFullYear()}</span>
            </div>
          )}
          {result.tvmaze_url ? (
            <a
              href={result.tvmaze_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-muted-fg hover:text-accent transition-colors ml-auto"
            >
              TVmaze
              <ExternalLink size={10} />
            </a>
          ) : (
            <div />
          )}
        </div>
      </div>

      {/* Hover shimmer */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{
          background: "linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 60%)"
        }}
      />
    </motion.div>
  );
}
