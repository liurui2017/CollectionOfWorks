import Link from "next/link";
import dayjs from "dayjs";
import type { components } from "@/src/api/schema";
import { fetchCategories, fetchTags, fetchWorks } from "@/src/lib/server-api";

interface SearchParams {
  type?: string;
  category?: string;
  tag?: string;
  q?: string;
  sort?: string;
  page?: string;
}

/** 作品列表 SSR：支持 type / category / tag / q / sort / page 查询。 */
export default async function WorksPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const sp = await searchParams;
  const params = new URLSearchParams();
  Object.entries(sp).forEach(([k, v]) => {
    if (v) params.set(k, v);
  });
  const paramsStr = params.toString();

  const [worksRes, categories, tags] = await Promise.all([
    fetchWorks(paramsStr),
    fetchCategories(),
    fetchTags(),
  ]);
  const items = worksRes?.items ?? [];
  const meta = worksRes?.meta ?? { page: 1, page_size: 12, total: 0, total_pages: 0 };

  return (
    <div className="wrap py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-text">全部作品</h1>
        <p className="text-text-dim mt-1">
          {meta.total} 件作品 · 第 {meta.page}/{meta.total_pages || 1} 页
        </p>
      </div>

      {/* 分类 / 标签 过滤 */}
      <div className="mb-8 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-text-mute mr-1">分类：</span>
        <FilterPill label="全部" href="/works" active={!sp.category} />
        {(categories ?? []).map((c) => (
          <FilterPill
            key={c.id}
            label={c.name}
            href={`/works?category=${c.slug}`}
            active={sp.category === c.slug}
          />
        ))}
      </div>
      <div className="mb-8 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-text-mute mr-1">标签：</span>
        {(tags ?? []).slice(0, 10).map((t) => (
          <FilterPill
            key={t.id}
            label={`#${t.name}`}
            href={`/works?tag=${t.slug}`}
            active={sp.tag === t.slug}
          />
        ))}
      </div>

      {items.length === 0 ? (
        <div className="py-20 text-center text-text-mute">没有匹配的作品</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((w) => (
            <Link
              key={w.id}
              href={`/works/${w.slug}`}
              className="group rounded-[var(--radius)] border border-border bg-surface overflow-hidden hover:border-accent-line transition-colors"
            >
              {w.cover ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={w.cover.url} alt={w.title} className="aspect-[16/10] w-full object-cover" />
              ) : (
                <div className="aspect-[16/10] w-full bg-bg-elev flex items-center justify-center text-text-mute text-xs uppercase tracking-wider">
                  {w.type}
                </div>
              )}
              <div className="p-4">
                <h3 className="font-medium text-text group-hover:text-accent transition-colors">{w.title}</h3>
                {w.summary && <p className="mt-1 text-sm text-text-dim line-clamp-2">{w.summary}</p>}
                <div className="mt-3 flex items-center gap-3 text-xs text-text-mute">
                  {w.published_at && <span>{dayjs(w.published_at).format("YYYY-MM-DD")}</span>}
                  <span className="ml-auto">{w.view_count} 次浏览</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* 分页 */}
      {meta.total_pages > 1 && (
        <div className="mt-10 flex justify-center items-center gap-2">
          {Array.from({ length: meta.total_pages }, (_, i) => i + 1).map((p) => {
            const q = new URLSearchParams(sp as Record<string, string>);
            q.set("page", String(p));
            return (
              <Link
                key={p}
                href={`/works?${q.toString()}`}
                className={`rounded-full px-3 py-1 text-sm transition-colors ${
                  p === meta.page
                    ? "bg-accent text-bg"
                    : "bg-surface text-text-dim hover:text-text border border-border"
                }`}
              >
                {p}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function FilterPill({ label, href, active }: { label: string; href: string; active?: boolean }) {
  return (
    <Link
      href={href}
      className={`rounded-full px-3 py-1 text-sm transition-colors ${
        active
          ? "bg-accent-soft text-accent border border-accent-line"
          : "text-text-dim hover:text-text hover:bg-surface border border-transparent"
      }`}
    >
      {label}
    </Link>
  );
}
