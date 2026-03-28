export default function Footer() {
  return (
    <footer className="w-full py-12 border-t border-slate-200 bg-slate-50">
      <div className="flex flex-col md:flex-row justify-between items-center px-8 max-w-7xl mx-auto gap-6">
        <div className="text-xs text-slate-500 uppercase tracking-widest">
          © 2025 GreenQualify Finance. Secure & Encrypted.
        </div>
        <div className="flex gap-8">
          <a className="text-xs text-slate-500 uppercase tracking-widest hover:text-emerald-600 transition-colors" href="#">
            Privacy
          </a>
          <a className="text-xs text-slate-500 uppercase tracking-widest hover:text-emerald-600 transition-colors" href="#">
            Security
          </a>
          <a className="text-xs text-slate-500 uppercase tracking-widest hover:text-emerald-600 transition-colors" href="#">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
