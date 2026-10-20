"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { getQueryClient } from "@/src/lib/query";

export default function Providers({ children }: { children: ReactNode }) {
  const qc = getQueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
