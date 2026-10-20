import Link from "next/link";
import dayjs from "dayjs";
import type { components } from "@/src/api/schema";
import { fetchSiteProfile, fetchWorks } from "@/src/lib/server-api";

/** 首页 SSR：Hero（site_profile）+ 精选作品 + 最新作品。 */
export default async function HomePage() {
  const [profile, worksRes] = await Promise.all([
    fetchSiteProfile(),
    fetchWorks("featured=true&page_size=6"),
  ]);
  const featured = worksRes?.items ?? [];

  return (
    <div className="wrap py-16 sm:py-24">
      {/* Hero */}
      <section className="mb-20">
        <div className="flex items-start gap-6">
          {profile?.avatar && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={profile.avatar.url}
              alt={profile.nickname}
              className="h-20 w-20 rounded-full object-cover ring-2 ring-accent/40"
            />
          )}
          <div>
            <h1 className="text-3xl sm:text-4xl font-semibold text-text mb-2">
              {profile?.nickname || profile?.site_name || "你好，我是创作者"}
            </h1>
            {profile?.headline && (
              <p className="text-lg text-text-dim max-w-2xl">{profile.headline}</p>
            )}
          </div>
        </div>
        {profile?.bio && (
          <div className="mt-6 text-text-dim max-w-2xl whitespace-pre-wrap leading-relaxed">
            {profile.bio}
          </div>
        )}
      </section>

      {/* 精选作品 */}
      <section>
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-xl font-semibold text-text">精选作品</h2>
          <Link href="/works" className="text-sm text-text-dim hover:text-accent transition-colors">
            全部作品 →
          </Link>
        </div>

        {featured.length === 0 ? (
          <div className="py-16 text-center text-text-mute">
            还没有发布作品。先去<span className="text-accent">管理后台</span>创建一个吧。
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {featured.map((w) => (
              <WorkCard key={w.id} work={w} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function WorkCard({ work }: { work: components["schemas"]["WorkListItem"] }) {
  return (
    <Link
      href={`/works/${work.slug}`}
      className="group block rounded-[var(--radius)] border border-border bg-surface overflow-hidden hover:border-accent-line transition-colors"
    >
      {work.cover ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={work.cover.url}
          alt={work.title}
          className="aspect-[16/10] w-full object-cover"
        />
      ) : (
        <div className="aspect-[16/10] w-full bg-bg-elev flex items-center justify-center text-text-mute text-xs uppercase tracking-wider">
          {work.type}
        </div>
      )}
      <div className="p-4">
        <h3 className="font-medium text-text group-hover:text-accent transition-colors">
          {work.title}
        </h3>
        {work.summary && (
          <p className="mt-1 text-sm text-text-dim line-clamp-2">{work.summary}</p>
        )}
        <div className="mt-3 flex items-center gap-3 text-xs text-text-mute">
          {work.published_at && (
            <span>{dayjs(work.published_at).format("YYYY-MM-DD")}</span>
          )}
          <span className="ml-auto">{work.view_count} 次浏览</span>
        </div>
      </div>
    </Link>
  );
}
