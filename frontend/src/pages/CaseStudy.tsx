import { Link } from "react-router-dom";

export default function CaseStudy() {
  return (
    <main className="pt-24 pb-20 px-4 md:px-12 max-w-7xl mx-auto">
      {/* Hero Header */}
      <header className="mb-16 md:mb-24 flex flex-col items-center text-center">
        <span className="inline-block px-4 py-1.5 rounded-full bg-secondary-container text-on-secondary-container text-xs font-bold uppercase tracking-widest mb-6">
          Success Story
        </span>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-on-background mb-6 max-w-4xl">
          Turning "Not Ready" into <span className="text-primary">Capital Ready.</span>
        </h1>
        <p className="text-xl text-on-surface-variant max-w-2xl leading-relaxed">
          How Miller's Tool & Die Shop leveraged GreenQualify to unlock $450k in green manufacturing
          grants they didn't know they qualified for.
        </p>
      </header>

      {/* Before / After Grid */}
      <section className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-24">
        <div className="md:col-span-5 bg-surface-container-low rounded-xl p-8 flex flex-col">
          <div className="flex items-center gap-3 mb-8">
            <span className="material-symbols-outlined text-error">error</span>
            <h3 className="text-xl font-bold text-on-surface">The Before</h3>
          </div>
          <div className="space-y-6 flex-grow">
            <div className="p-6 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10">
              <p className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-2">Internal Status</p>
              <p className="text-lg font-medium text-error">Unclear Financing Options</p>
              <p className="text-sm text-on-surface-variant mt-2">
                Owner spent 12+ hours researching generic SBA loans with no clear path to equipment upgrades.
              </p>
            </div>
            <div className="p-6 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10 opacity-70">
              <p className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-2">Application Readiness</p>
              <p className="text-lg font-medium text-secondary">0% Prepared</p>
              <p className="text-sm text-on-surface-variant mt-2">
                Missing critical impact data required for modern environmental manufacturing incentives.
              </p>
            </div>
          </div>
        </div>

        <div className="hidden md:flex md:col-span-2 items-center justify-center">
          <div className="w-12 h-12 bg-primary-container text-on-primary-container rounded-full flex items-center justify-center shadow-lg">
            <span className="material-symbols-outlined">arrow_forward</span>
          </div>
        </div>

        <div className="md:col-span-5 bg-surface-container-highest/30 rounded-xl p-8 flex flex-col border-2 border-primary/20">
          <div className="flex items-center gap-3 mb-8">
            <span className="material-symbols-outlined text-primary fill-icon">check_circle</span>
            <h3 className="text-xl font-bold text-on-surface">The After</h3>
          </div>
          <div className="space-y-6 flex-grow">
            <div className="p-6 bg-white rounded-xl shadow-md border-l-4 border-primary">
              <p className="text-sm font-bold text-primary uppercase tracking-wider mb-2">Concierge Outcome</p>
              <p className="text-lg font-bold text-on-surface">Precision Recommendation</p>
              <p className="text-sm text-on-surface-variant mt-2">
                Identified specific USDA REAP Grant & Green Tech Credit eligibility within 15 minutes.
              </p>
            </div>
            <div className="p-6 bg-white rounded-xl shadow-md border-l-4 border-primary">
              <p className="text-sm font-bold text-primary uppercase tracking-wider mb-2">Application Readiness</p>
              <p className="text-lg font-bold text-on-surface">100% Prepared</p>
              <p className="text-sm text-on-surface-variant mt-2">
                Generated a comprehensive 'Impact Case' report including projected CO2 reduction and ROI metrics.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Quote */}
      <section className="mb-24 bg-surface-container-lowest rounded-[2rem] p-12 md:p-20 shadow-xl shadow-slate-200/50 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="relative z-10 flex flex-col md:flex-row gap-12 items-center">
          <div className="w-32 h-32 md:w-48 md:h-48 shrink-0">
            <img
              alt="George Miller portrait"
              className="w-full h-full object-cover rounded-full border-4 border-white shadow-lg"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDHiWdy6xRXL3r6pcBQjcToD8AegJpZzrTnNyG9SUPkCKKnKfPFUajpdSA7Wcsl8Y4dPzAHkhng7JymMFI-O9euXeJ7lCJsjizRsEBX6hsX95D2y6eQGfwP3s3lUuFbIvhCsRVv0ZS4ye-ysCcwKdbxrhf4-kLqzT1RhdAgmhsTX_XLBLKL37eTpj-so9rxk9K8WfEPiUL8PJPE8mOaJNMEjzs-SrInqcmAhDPOHgJBYIhS9fjvGrrCE9Wj-oO6hWtcHA-tMa1ptR8"
            />
          </div>
          <div>
            <span className="material-symbols-outlined text-primary text-6xl mb-4 fill-icon">format_quote</span>
            <blockquote className="text-2xl md:text-3xl font-medium text-on-background leading-relaxed mb-6 italic">
              "I thought sustainability was for Silicon Valley companies, not for a tool shop in Ohio.
              GreenQualify showed us that our efficiency upgrades were actually green assets. We didn't
              just get the loan; we got a roadmap for the next decade."
            </blockquote>
            <p className="text-lg font-bold text-on-surface">— George Miller</p>
            <p className="text-sm text-on-surface-variant uppercase tracking-widest">
              Founder, Miller's Tool & Die Shop
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
        <div className="text-center p-8">
          <p className="text-6xl font-extrabold text-primary tracking-tighter mb-2">$450k</p>
          <p className="text-sm font-bold text-on-surface-variant uppercase">Grant Funding Secured</p>
        </div>
        <div className="text-center p-8 border-x-0 md:border-x border-outline-variant/30">
          <p className="text-6xl font-extrabold text-primary tracking-tighter mb-2">15m</p>
          <p className="text-sm font-bold text-on-surface-variant uppercase">Time to Qualification</p>
        </div>
        <div className="text-center p-8">
          <p className="text-6xl font-extrabold text-primary tracking-tighter mb-2">100%</p>
          <p className="text-sm font-bold text-on-surface-variant uppercase">Application Approval</p>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-emerald-gradient rounded-[2.5rem] p-12 md:p-24 text-center text-white relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative z-10">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tight mb-8">
            Ready for your success story?
          </h2>
          <p className="text-xl text-primary-fixed mb-12 max-w-2xl mx-auto opacity-90">
            Join 1,200+ small businesses using GreenQualify to find hidden financial opportunities.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Link
              to="/intake"
              className="w-full sm:w-auto px-10 py-5 bg-white text-primary rounded-full font-extrabold text-lg shadow-2xl shadow-emerald-950/20 active:scale-95 transition-all"
            >
              Start Your Assessment
            </Link>
            <button className="w-full sm:w-auto px-10 py-5 bg-primary/20 backdrop-blur-md border border-white/20 text-white rounded-full font-bold text-lg hover:bg-white/10 transition-all">
              Download Report
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
