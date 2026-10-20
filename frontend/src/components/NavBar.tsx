import Link from "next/link";
import { cn } from "@/src/lib/utils";

const links = [
  { href: "/", label: "首页" },
  { href: "/works", label: "作品" },
  // About 通过 site_profile 在首页或独立 /about 页展示，v1 先不单独路由
];

export function NavBar() {
  return (
    <nav className="sticky top-0 z-40 border-b border-border bg-bg/80 backdrop-blur-md">
      <div className="wrap flex items-center justify-between gap-5 py-3.5">
        <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-wide text-text">
          <span className="inline-block h-[9px] w-[9px] rounded-full bg-accent shadow-[0_0_12px_var(--accent)]" />
          <span>Collection</span>
        </Link>

        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "rounded-full px-3.5 py-1.5 text-sm text-text-dim transition-colors",
                "hover:bg-surface hover:text-text",
              )}
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/admin/login"
            className={cn(
              "ml-2 rounded-full border border-border-strong px-3.5 py-1.5 text-sm text-text-dim transition-colors",
              "hover:border-accent-line hover:text-text",
            )}
          >
            管理
          </Link>
        </div>
      </div>
    </nav>
  );
}
