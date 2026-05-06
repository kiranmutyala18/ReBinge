"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { EXAMPLE_QUERIES } from "@/lib/utils";

interface ExampleQueriesProps {
  onSelect: (query: string) => void;
}

export function ExampleQueries({ onSelect }: ExampleQueriesProps) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4 justify-center">
        <Sparkles size={12} className="text-gold" />
        <span className="text-xs font-mono text-muted-fg uppercase tracking-widest">
          Try these
        </span>
      </div>
      <div className="flex flex-wrap gap-2 justify-center">
        {EXAMPLE_QUERIES.map((query, i) => (
          <motion.button
            key={query}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i, duration: 0.4 }}
            onClick={() => onSelect(query)}
            className="px-4 py-2 rounded-full glass cinematic-border text-sm text-muted-fg hover:text-foreground hover:border-accent/30 transition-all duration-200 font-body"
          >
            &ldquo;{query}&rdquo;
          </motion.button>
        ))}
      </div>
    </div>
  );
}
