import { notFound } from "next/navigation";
import Link from "next/link";
import dayjs from "dayjs";
import type { components } from "@/src/api/schema";
import { fetchWorkBySlug } from "@/src/lib/server-api";

interface Props {
  params: Promise<{ slug: string }>;
}

/** 作品详情 SSR：4 种类型（video/article/note/gallery）共用。 */
export default async function WorkDetailPage({ params }: Props) {
  const { slug } = await params;
  const work = await fetchWorkBySlug(slug);
  if (!work) notFound();

  return (
    <div className="wrap py-12 max-w-3xl">
      <Link href="/works" className="text-sm text-text-dim hover:text-accent transition-colors mb-6 inline-block">
        ← 返回作品列表
      </Link>

      <article>
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-3 text-xs text-text-mute mb-3">
            {work.category && (
              <Link href={`/works?category=${work.category.slug}`} className="hover:text-accent">
                {work.category.name}
              </Link>
            )}
            {work.published_at && <span>{dayjs(work.published_at).format("YYYY-MM-DD")}</span>}
            <span>·</span>
            <span>{work.view_count} 次浏览</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-semibold text-text leading-tight">{work.title}</h1>
          {work.summary && <p className="mt-3 text-text-dim">{work.summary}</p>}

          {work.tags && work.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {work.tags.map((t) => (
                <span
                  key={t.id}
                  className="rounded-full bg-surface border border-border text-text-dim text-xs px-2.5 py-0.5"
                >
                  #{t.name}
                </span>
              ))}
            </div>
          )}
        </header>

        {/* Video */}
        {work.video && (
          <div className="mb-8">
            <video
              src={work.video.url}
              controls
              className="w-full rounded-[var(--radius)] border border-border bg-black"
            />
          </div>
        )}

        {/* Gallery */}
        {work.images && work.images.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-8">
            {work.images.map((img) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={img.id}
                src={img.url}
                alt=""
                className="w-full aspect-square object-cover rounded-[var(--radius-sm)] border border-border"
              />
            ))}
          </div>
        )}

        {/* Content (Markdown 纯文本，v1 直接展示) */}
        {work.content && (
          <div className="prose-custom text-text-dim">
            {/* eslint-disable-next-line react/no-danger */}
            <div dangerouslySetInnerHTML={{ __html: markdownToHtml(work.content) }} />
          </div>
        )}
      </article>
    </div>
  );
}

/** v1 极简 Markdown 渲染：标题/段落/代码块/链接/列表，不依赖外部库。 */
function markdownToHtml(md: string): string {
  const lines = md.split("\n");
  const out: string[] = [];
  let codeBuf: string[] = [];
  let inCode = false;

  for (const line of lines) {
    if (line.startsWith("```")) {
      if (inCode) {
        out.push(`<pre><code>${escapeHtml(codeBuf.join("\n"))}</code></pre>`);
        codeBuf = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuf.push(line);
      continue;
    }
    if (/^#{1,3} /.test(line)) {
      const lvl = line.match(/^#+/)![0].length;
      out.push(`<h${lvl}>${inline(line.replace(/^#+\s*/, ""))}</h${lvl}>`);
    } else if (line.startsWith("> ")) {
      out.push(`<blockquote>${inline(line.slice(2))}</blockquote>`);
    } else if (/^\*\s/.test(line) || /^\d+\.\s/.test(line)) {
      out.push(`<p>${inline(line)}</p>`);
    } else if (line.trim() === "") {
      // skip blank
    } else {
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  return out.join("\n");
}

function inline(text: string): string {
  let t = escapeHtml(text);
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  return t;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
