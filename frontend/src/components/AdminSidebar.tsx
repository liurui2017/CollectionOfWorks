import Link from "next/link";
import { cn } from "@/src/lib/utils";

const items = [
  { href: "/admin/works", label: "作品管理" },
  { href: "/admin/categories", label: "分类" },
  { href: "/admin/tags", label: "标签" },
  { href: "/admin/site/profile", label: "站点设置" },
];

export function AdminSidebar() {
  return (
    <aside className="fixed top-0 left-0 h-screen w-64 border-r border-border bg-bg-elev py-6 px-4 z-30">
      <Link href="/admin/works" className="flex items-center gap-2 font-semibold text-text mb-8 px-2">
        <span className="inline-block h-[9px] w-[9px] rounded-full bg-accent shadow-[0_0_12px_var(--accent)]" />
        管理后台
      </Link>
      <nav className="flex flex-col gap-1">
        {items.map((i) => (
          <Link
            key={i.href}
            href={i.href}
            className={cn(
              "rounded-lg px-3 py-2 text-sm text-text-dim transition-colors",
              "hover:bg-surface hover:text-text",
            )}
          >
            {i.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
