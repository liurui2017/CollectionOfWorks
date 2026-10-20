export function Footer() {
  return (
    <footer className="border-t border-border mt-20 py-10 text-sm text-text-mute">
      <div className="wrap flex flex-col sm:flex-row items-center justify-between gap-3">
        <p>© {new Date().getFullYear()} Collection · All rights reserved.</p>
        <div className="flex items-center gap-4">
          <span className="hover:text-text-dim cursor-pointer">GitHub</span>
          <span className="hover:text-text-dim cursor-pointer">Bilibili</span>
          <span className="hover:text-text-dim cursor-pointer">X</span>
        </div>
      </div>
    </footer>
  );
}
