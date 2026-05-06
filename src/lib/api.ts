// Types matching the FastAPI backend schemas

export interface SearchRequest {
  query: string;
  limit?: number;
  show_name?: string;
  min_similarity?: number;
}

export interface SearchResultItem {
  id: number;
  show_name: string;
  season: number;
  episode_number: number;
  title: string;
  summary: string;
  similarity_score: number;
  air_date?: string;
  image_url?: string;
  tvmaze_url?: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResultItem[];
}

export interface HealthResponse {
  status: string;
  version: string;
  embedding_model: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function searchEpisodes(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}
