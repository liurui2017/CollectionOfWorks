import { QueryClient } from "@tanstack/react-query";

// 单例 queryClient（App Router 每个请求创建一次，避免 SSR 状态交叉）
let client: QueryClient | null = null;

export function getQueryClient(): QueryClient {
  if (typeof window === "undefined") {
    return new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30_000,   // 30 秒内视为新鲜
          refetchOnWindowFocus: false,
          retry: 1,
        },
      },
    });
  }
  if (!client) {
    client = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30_000,
          refetchOnWindowFocus: false,
          retry: 1,
        },
      },
    });
  }
  return client;
}
