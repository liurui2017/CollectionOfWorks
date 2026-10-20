"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/src/api/client";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace(`/admin/login?redirect=${encodeURIComponent(window.location.pathname)}`);
    }
  }, [router]);

  // 客户端渲染期间先展示空壳（layout 背景仍可见）
  return <>{children}</>;
}
