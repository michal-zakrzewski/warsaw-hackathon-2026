import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md shadow-sm">
      <div className="flex justify-between items-center px-8 py-4 max-w-7xl mx-auto">
        <Link to="/" className="text-2xl font-bold tracking-tighter text-emerald-900">
          Concierge
        </Link>
        <div className="hidden md:flex items-center gap-8">
          <Link
            to="/"
            className="text-sm font-semibold tracking-tight text-emerald-700 border-b-2 border-emerald-600"
          >
            How it Works
          </Link>
          <Link
            to="/case-study"
            className="text-sm font-medium tracking-tight text-slate-600 hover:text-emerald-600 transition-colors"
          >
            Case Study
          </Link>
        </div>
        <div className="flex items-center gap-6">
          <button className="text-sm font-medium tracking-tight text-slate-600 hover:text-emerald-600 transition-colors">
            Sign In
          </button>
          <Link
            to="/intake"
            className="bg-primary-gradient text-white px-6 py-2.5 rounded-full text-sm font-semibold tracking-tight active:scale-95 duration-150 shadow-md"
          >
            Start
          </Link>
        </div>
      </div>
      <div className="bg-slate-200/20 h-px w-full" />
    </nav>
  );
}
