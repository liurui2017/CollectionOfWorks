import Link from "next/link";
import { NavBar } from "@/src/components/NavBar";
import { Footer } from "@/src/components/Footer";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <NavBar />
      <main className="flex-1">{children}</main>
      <Footer />
    </>
  );
}
