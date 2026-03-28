import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <main className="pt-24">
      {/* Hero */}
      <section className="relative px-8 py-20 md:py-32 max-w-7xl mx-auto overflow-hidden">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="z-10">
            <div className="inline-flex items-center gap-2 bg-secondary-container text-on-secondary-container px-4 py-1.5 rounded-full mb-6">
              <span className="material-symbols-outlined text-sm fill-icon">eco</span>
              <span className="text-xs font-bold uppercase tracking-widest">Sustainability First</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-on-surface leading-[1.1] mb-6">
              Find the best green financing path for{" "}
              <span className="text-primary">your business</span>
            </h1>
            <p className="text-xl text-on-surface-variant leading-relaxed max-w-xl mb-10">
              Upload a few details about your farm or factory, and get a recommendation with ROI,
              impact, and likely financing options.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                to="/intake"
                className="bg-primary-gradient text-on-primary px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center gap-2"
              >
                Start <span className="material-symbols-outlined">arrow_forward</span>
              </Link>
              <Link
                to="/case-study"
                className="bg-surface-container-lowest border border-outline-variant/20 text-on-surface px-8 py-4 rounded-2xl font-bold text-lg hover:bg-surface-container-low transition-colors text-center"
              >
                View sample case
              </Link>
            </div>
          </div>
          <div className="relative">
            <div className="absolute -top-20 -right-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
            <div className="absolute -bottom-20 -left-20 w-72 h-72 bg-tertiary/10 rounded-full blur-3xl" />
            <div className="relative bg-white rounded-2xl shadow-2xl p-4 md:p-8 transform rotate-2">
              <img
                alt="Sustainable factory with solar panels"
                className="rounded-xl w-full h-[400px] object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuD2pgP5qmMmQj8j_kTXLL0cAzIV9sOXrih6rRy1oZ5F8M7jakuWbyUuOa86gpHltFvf8mtap_HgCSXakhNzTmt3QO0kI0oBKVB6TrfCAndK8wJ_EwJBiGrM_ZZKL07WEB5gRXDlaJled2OxmcqtK5xObgtgGHdCJmvuRVGlQL1xcM9RpD4t7S7ZTirKJuRhzbtoIDwXx6Z0sMjxGKpw5F8u5-YaI_XsQzZg8J5CR8r15QzNSYIprORP6avWaItc40qvroqdnPibCN4"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Process Steps */}
      <section className="bg-surface-container-low py-24">
        <div className="max-w-7xl mx-auto px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-on-surface mb-4">Precision Analysis in Minutes</h2>
            <p className="text-on-surface-variant max-w-2xl mx-auto">
              Our streamlined process connects your operational data directly to institutional green
              capital standards.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 items-center">
            <div className="bg-surface-container-lowest p-8 rounded-2xl shadow-sm h-full">
              <div className="w-12 h-12 bg-secondary-container rounded-xl flex items-center justify-center mb-6 text-primary">
                <span className="material-symbols-outlined fill-icon">business_center</span>
              </div>
              <h3 className="text-xl font-bold mb-3">Business info in</h3>
              <p className="text-on-surface-variant leading-relaxed">
                Securely upload your utility bills, crop yields, or production capacity data.
              </p>
            </div>
            <div className="hidden md:flex justify-center text-outline-variant">
              <span className="material-symbols-outlined text-4xl">trending_flat</span>
            </div>
            <div className="bg-surface-container-lowest p-8 rounded-2xl shadow-sm border-2 border-primary/10 h-full">
              <div className="w-12 h-12 bg-primary-fixed rounded-xl flex items-center justify-center mb-6 text-primary">
                <span className="material-symbols-outlined fill-icon">fact_check</span>
              </div>
              <h3 className="text-xl font-bold mb-3">Recommendation out</h3>
              <p className="text-on-surface-variant leading-relaxed">
                Instant report featuring customized ROI projections and eligible loan programs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Bento Grid */}
      <section className="py-24 px-8 max-w-7xl mx-auto">
        <h2 className="text-4xl font-extrabold text-on-surface text-center mb-16">
          Investor-Grade Benefits
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-surface-container-highest/40 p-10 rounded-2xl flex flex-col md:flex-row gap-8 items-center">
            <div className="md:w-1/2">
              <h3 className="text-3xl font-bold text-on-surface mb-4">Maximize ROI</h3>
              <p className="text-on-surface-variant text-lg">
                Every recommendation is stress-tested against current market conditions to ensure
                your green transition pays for itself through energy savings and incentives.
              </p>
            </div>
            <div className="md:w-1/2 bg-white p-6 rounded-xl shadow-inner flex flex-col gap-4">
              <div className="flex justify-between items-center text-sm font-bold">
                <span>Traditional Loan</span>
                <span className="text-error">5.4% ROI</span>
              </div>
              <div className="w-full bg-surface-container h-3 rounded-full overflow-hidden">
                <div className="bg-error w-1/3 h-full" />
              </div>
              <div className="flex justify-between items-center text-sm font-bold">
                <span>GreenQualify Path</span>
                <span className="text-primary">12.8% ROI</span>
              </div>
              <div className="w-full bg-surface-container h-3 rounded-full overflow-hidden">
                <div className="bg-primary w-2/3 h-full" />
              </div>
            </div>
          </div>
          <div className="bg-tertiary text-on-tertiary p-10 rounded-2xl flex flex-col justify-end min-h-[300px]">
            <span className="material-symbols-outlined text-5xl mb-6">verified_user</span>
            <h3 className="text-2xl font-bold mb-2">Improve qualification chances</h3>
            <p className="text-tertiary-fixed/80">
              Our pre-validation process aligns your data with institutional lender requirements
              automatically.
            </p>
          </div>
          <div className="bg-primary-container text-on-primary-container p-10 rounded-2xl flex flex-col justify-end min-h-[300px]">
            <span className="material-symbols-outlined text-5xl mb-6">co2</span>
            <h3 className="text-2xl font-bold mb-2">Estimate CO2 impact</h3>
            <p className="text-on-primary-container/80">
              Detailed carbon abatement curves translated into reporting formats that investors
              trust.
            </p>
          </div>
          <div className="md:col-span-2 bg-white border border-outline-variant/10 p-10 rounded-2xl flex flex-col md:flex-row items-center gap-12">
            <div className="flex-1">
              <h3 className="text-2xl font-bold mb-4">Enterprise-Grade Security</h3>
              <p className="text-on-surface-variant">
                Your financial and operational data is encrypted using AES-256 standards. We operate
                under strict SOC2 compliance protocols to ensure your competitive data stays private.
              </p>
            </div>
            <div className="flex gap-8 opacity-40">
              <span className="material-symbols-outlined text-4xl">security</span>
              <span className="material-symbols-outlined text-4xl">encrypted</span>
              <span className="material-symbols-outlined text-4xl">cloud_done</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-8 pb-24">
        <div className="max-w-5xl mx-auto bg-primary text-on-primary rounded-3xl p-12 md:p-20 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-extrabold mb-8">Ready to transition?</h2>
            <p className="text-primary-fixed/80 text-xl mb-12 max-w-2xl mx-auto">
              Join hundreds of industrial leaders securing better rates for sustainable growth.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link
                to="/intake"
                className="bg-white text-primary px-10 py-4 rounded-full font-bold text-lg hover:bg-primary-fixed transition-colors"
              >
                Start Assessment
              </Link>
              <button className="border border-white/30 text-white px-10 py-4 rounded-full font-bold text-lg hover:bg-white/10 transition-colors">
                Talk to Advisor
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
