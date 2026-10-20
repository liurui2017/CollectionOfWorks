"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { api } from "@/src/api/client";

interface Query {
  page?: string;
  status?: string;
}

/** 后台作品列表：React Query 客户端拉取。 */
export default function AdminWorksPage({ searchParams }: { searchParams: Query }) {
  const page = Number(searchParams.page ?? 1);
  const status = searchParams.status;

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-works", page, status],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "12" });
      if (status) params.set("status", status);
      return api.get<any>(`/api/v1/admin/works?${params.toString()}`);
    },
  });

  return (
    <div>
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-text">作品管理</h1>
          <p className="text-sm text-text-dim mt-1">
            {data?.meta?.total ?? 0} 件作品 · 第 {page} 页
          </p>
        </div>
        <Link
          href="/admin/works/new"
          className="rounded-lg bg-accent text-bg font-medium px-4 py-2 text-sm hover:bg-accent-dim transition-colors"
        >
          ＋ 新建作品
        </Link>
      </header>

      {/* 筛选 tab */}
      <div className="flex gap-2 mb-5">
        <StatusTab label="全部" href="/admin/works" active={!status} />
        <StatusTab label="已发布" href="/admin/works?status=published" active={status === "published"} />
        <StatusTab label="草稿" href="/admin/works?status=draft" active={status === "draft"} />
      </div>

      {isLoading && <div className="py-16 text-center text-text-mute">加载中...</div>}
      {error && <div className="py-16 text-center text-danger">加载失败</div>}

      {data && (
        <div className="rounded-[var(--radius)] border border-border bg-surface overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-bg-elev text-text-dim text-left">
              <tr>
                <th className="px-4 py-3 font-medium">标题</th>
                <th className="px-4 py-3 font-medium">类型</th>
                <th className="px-4 py-3 font-medium">状态</th>
                <th className="px-4 py-3 font-medium">浏览</th>
                <th className="px-4 py-3 font-medium">发布时间</th>
                <th className="px-4 py-3 font-medium text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.items.map((w: any) => (
                <tr key={w.id} className="hover:bg-bg-elev transition-colors">
                  <td className="px-4 py-3">
                    <Link href={`/admin/works/${w.id}/edit`} className="text-text hover:text-accent">
                      {w.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-text-dim">{w.type}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        w.status === "published"
                          ? "bg-accent-soft text-accent"
                          : "bg-surface-2 text-text-mute"
                      }`}
                    >
                      {w.status === "published" ? "已发布" : "草稿"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-text-dim">{w.view_count}</td>
                  <td className="px-4 py-3 text-text-dim">
                    {w.published_at ? dayjs(w.published_at).format("YYYY-MM-DD") : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/works/${w.id}/edit`}
                      className="text-sm text-accent hover:underline"
                    >
                      编辑
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusTab({ label, href, active }: { label: string; href: string; active?: boolean }) {
  return (
    <Link
      href={href}
      className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
        active
          ? "bg-accent-soft text-accent border border-accent-line"
          : "text-text-dim hover:text-text border border-transparent hover:border-border"
      }`}
    >
      {label}
    </Link>
  );
}
