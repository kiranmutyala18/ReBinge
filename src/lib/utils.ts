import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatEpisodeCode(season: number, episode: number): string {
  return `S${String(season).padStart(2, "0")}E${String(episode).padStart(2, "0")}`;
}

export function formatSimilarity(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function getSimilarityColor(score: number): string {
  if (score >= 0.8) return "text-green-400";
  if (score >= 0.6) return "text-gold";
  if (score >= 0.4) return "text-accent-2";
  return "text-muted-fg";
}

export function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, "");
}

export const POPULAR_SHOWS = [
  "Friends",
  "Seinfeld",
  "The Office",
  "Parks and Recreation",
  "Brooklyn Nine-Nine",
  "How I Met Your Mother",
  "The Big Bang Theory",
  "It's Always Sunny in Philadelphia",
];

export const EXAMPLE_QUERIES = [
  "the one where they get trapped in an elevator",
  "romantic subplot at a high school reunion",
  "cooking competition with a surprise twist",
  "a character pretends to be someone else at a party",
  "road trip goes horribly wrong",
  "someone accidentally sends the wrong message",
  "flashback episode revealing a big secret",
  "holiday episode with unexpected guests",
];
