/** Server Component 用：直接 fetch 后端，类型安全。 */
import type { components } from "@/src/api/schema";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const FALLBACK = { cache: "no-store" as const };

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchSiteProfile(): Promise<components["schemas"]["SiteProfileOut"] | null> {
  return get("/api/v1/site/profile");
}

export async function fetchWorks(params?: string): Promise<components["schemas"]["Paginated_WorkListItem_"] | null> {
  return get(`/api/v1/works${params ? `?${params}` : ""}`);
}

export async function fetchWorkBySlug(slug: string): Promise<components["schemas"]["WorkDetail"] | null> {
  return get(`/api/v1/works/${slug}`);
}

export async function fetchCategories(): Promise<components["schemas"]["CategoryOut"][] | null> {
  return get("/api/v1/categories");
}

export async function fetchTags(limit?: number): Promise<components["schemas"]["TagOut"][] | null> {
  return get(limit ? `/api/v1/tags?limit=${limit}` : "/api/v1/tags");
}
