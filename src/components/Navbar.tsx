"use client";

import { motion } from "framer-motion";
import { Tv2, Github, Zap } from "lucide-react";

export function Navbar() {
  return (
    <motion.nav
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="fixed top-0 left-0 right-0 z-50 px-6 py-4"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center">
            <Tv2 size={16} className="text-accent" />
          </div>
          <span className="font-display text-xl tracking-widest text-foreground">
            RE<span className="text-accent">RUSH</span>
          </span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs font-mono text-muted-fg">
            <Zap size={10} className="text-gold" />
            Semantic AI
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="w-8 h-8 rounded-lg glass flex items-center justify-center text-muted-fg hover:text-foreground transition-colors"
          >
            <Github size={15} />
          </a>
        </div>
      </div>
    </motion.nav>
  );
}
