import { AdminGuard } from "@/src/components/AdminGuard";
import { AdminSidebar } from "@/src/components/AdminSidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <div className="flex min-h-screen bg-bg">
        <AdminSidebar />
        <div className="flex-1 ml-64">
          <main className="p-8">{children}</main>
        </div>
      </div>
    </AdminGuard>
  );
}
