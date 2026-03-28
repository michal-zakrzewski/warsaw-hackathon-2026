import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { AnalysisResult } from "../types";

export default function Results() {
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("result");
    if (!raw) {
      navigate("/intake");
      return;
    }
    setResult(JSON.parse(raw));
  }, [navigate]);

  if (!result) return null;

  return (
    <main className="pt-24 pb-20 px-4 md:px-12 max-w-7xl mx-auto">
      {/* Dashboard Header */}
      <div className="mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-semibold mb-4">
              <span className="material-symbols-outlined text-sm fill-icon">verified</span>
              High Qualification Likelihood
            </span>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-on-surface mb-2">
              Solar + Storage
            </h1>
            <p className="text-lg text-on-surface-variant font-medium">
              Recommended Financing:{" "}
              <span className="text-tertiary">
                {result.formData.businessName || "GreenBridge Capital"}
              </span>
            </p>
          </div>
          <div className="flex gap-3">
            <button className="flex items-center gap-2 px-5 py-2.5 bg-surface-container-lowest text-on-surface border border-outline-variant/20 rounded-xl hover:bg-surface-container-low transition-colors shadow-sm">
              <span className="material-symbols-outlined">share</span>
              <span className="text-sm font-semibold">Share</span>
            </button>
            <button className="flex items-center gap-2 px-5 py-2.5 bg-gradient-primary text-on-primary rounded-xl hover:opacity-90 transition-opacity shadow-lg">
              <span className="material-symbols-outlined">download</span>
              <span className="text-sm font-semibold">Export PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Key Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-surface-container-lowest p-8 rounded-xl shadow-sm border border-outline-variant/10">
          <div className="flex items-center justify-between mb-4">
            <p className="text-on-surface-variant text-sm font-bold uppercase tracking-widest">
              Estimated Payback
            </p>
            <span className="material-symbols-outlined text-primary">calendar_today</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-extrabold tracking-tighter">4.2</span>
            <span className="text-on-surface-variant font-semibold">years</span>
          </div>
          <div className="mt-4 h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
            <div className="h-full bg-primary w-[85%] rounded-full" />
          </div>
        </div>

        <div className="bg-surface-container-lowest p-8 rounded-xl shadow-sm border border-outline-variant/10">
          <div className="flex items-center justify-between mb-4">
            <p className="text-on-surface-variant text-sm font-bold uppercase tracking-widest">
              Annual Savings
            </p>
            <span className="material-symbols-outlined text-primary">payments</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-extrabold tracking-tighter">$12,450</span>
            <span className="text-on-surface-variant font-semibold">/yr</span>
          </div>
          <p className="text-primary text-sm font-bold mt-4">+18% vs baseline</p>
        </div>

        <div className="bg-surface-container-lowest p-8 rounded-xl shadow-sm border border-outline-variant/10">
          <div className="flex items-center justify-between mb-4">
            <p className="text-on-surface-variant text-sm font-bold uppercase tracking-widest">
              CO2 Reduction
            </p>
            <span className="material-symbols-outlined text-primary">eco</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-extrabold tracking-tighter">18.5</span>
            <span className="text-on-surface-variant font-semibold">tons</span>
          </div>
          <p className="text-on-surface-variant text-xs mt-4">Equivalent to 425 trees planted</p>
        </div>
      </div>

      {/* Bento Grid: Insights + Next Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 mb-12">
        {/* Best Option Insights */}
        <div className="lg:col-span-3 bg-surface-container-low p-8 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight mb-8">
              Why this is the best option
            </h2>
            <div className="space-y-6">
              <div className="flex gap-5 group">
                <div className="w-12 h-12 shrink-0 rounded-full bg-primary/10 flex items-center justify-center text-primary transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined">bolt</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">Peak-Shaving Efficiency</h3>
                  <p className="text-on-surface-variant leading-relaxed">
                    The storage integration allows you to avoid peak utility rates, cutting
                    operational costs by 35% during high-demand hours.
                  </p>
                </div>
              </div>
              <div className="flex gap-5 group">
                <div className="w-12 h-12 shrink-0 rounded-full bg-primary/10 flex items-center justify-center text-primary transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined">shield_moon</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">Energy Resilience</h3>
                  <p className="text-on-surface-variant leading-relaxed">
                    Maintain critical operations during grid failures. Your facility stays online
                    without expensive diesel generator fuel costs.
                  </p>
                </div>
              </div>
              <div className="flex gap-5 group">
                <div className="w-12 h-12 shrink-0 rounded-full bg-primary/10 flex items-center justify-center text-primary transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined">trending_up</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">Maximized ITC Benefits</h3>
                  <p className="text-on-surface-variant leading-relaxed">
                    Current legislation favors this combined stack, unlocking a 30% Investment Tax
                    Credit for the entire project cost.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Next Steps Checklist */}
        <div className="lg:col-span-2 bg-tertiary text-on-tertiary p-8 rounded-xl relative overflow-hidden">
          <div className="relative z-10">
            <h2 className="text-2xl font-bold tracking-tight mb-2">What you need next</h2>
            <p className="text-tertiary-fixed/70 text-sm mb-8">
              Required for final approval
            </p>
            <ul className="space-y-4">
              {[
                "Signed Tax ID Verification",
                "Property Deed / Title",
                "Last 6 Months Utility Bills",
                "Facility Layout Blueprints",
              ].map((item) => (
                <li
                  key={item}
                  className="flex items-center gap-4 p-4 bg-white/10 rounded-xl backdrop-blur-sm border border-white/10"
                >
                  <span className="material-symbols-outlined text-tertiary-fixed">
                    check_box_outline_blank
                  </span>
                  <span className="font-medium">{item}</span>
                </li>
              ))}
            </ul>
            <button className="mt-8 w-full py-4 bg-surface-container-lowest text-tertiary rounded-xl font-bold hover:bg-tertiary-fixed transition-colors">
              Upload Documents
            </button>
          </div>
          <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-white/5 rounded-full blur-3xl" />
        </div>
      </div>

      {/* AI Analysis Detail */}
      {result.agentText && (
        <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10 p-8 md:p-12 mb-12">
          <h2 className="text-xl font-bold tracking-tight mb-6">AI Analysis Detail</h2>
          <div className="max-w-none text-on-surface">
            {result.agentText.split("\n").map((line, i) => {
              if (!line.trim()) return <br key={i} />;
              if (line.startsWith("# "))
                return (
                  <h2 key={i} className="text-2xl font-bold mt-6 mb-3">
                    {line.slice(2)}
                  </h2>
                );
              if (line.startsWith("## "))
                return (
                  <h3 key={i} className="text-xl font-bold mt-4 mb-2">
                    {line.slice(3)}
                  </h3>
                );
              if (line.startsWith("### "))
                return (
                  <h4 key={i} className="text-lg font-bold mt-3 mb-1">
                    {line.slice(4)}
                  </h4>
                );
              if (line.startsWith("- "))
                return (
                  <li key={i} className="ml-4 text-on-surface-variant mb-1">
                    {line.slice(2)}
                  </li>
                );
              if (line.startsWith("**") && line.endsWith("**"))
                return (
                  <p key={i} className="font-bold mb-2">
                    {line.slice(2, -2)}
                  </p>
                );
              return (
                <p key={i} className="text-on-surface-variant leading-relaxed mb-2">
                  {line}
                </p>
              );
            })}
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10 overflow-hidden mb-12">
        <div className="px-8 py-6 border-b border-surface-container-high">
          <h2 className="text-xl font-bold tracking-tight">Project Comparison</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant">
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">Type</th>
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">
                  Upfront Cost
                </th>
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">
                  Qual. Likelihood
                </th>
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">
                  Net Outcome
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high">
              <tr className="hover:bg-primary/5 transition-colors">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    <span className="font-bold">Solar Only</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-medium text-on-surface-variant">$245,000</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-surface-container text-on-surface-variant rounded-full text-xs font-bold">
                    Medium
                  </span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+$8.2k/yr</td>
              </tr>
              <tr className="bg-primary/5">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                    <span className="font-bold">Solar + Storage</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-medium text-on-surface-variant">$380,000</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-primary text-on-primary rounded-full text-xs font-bold">
                    High (Best)
                  </span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+$12.4k/yr</td>
              </tr>
              <tr className="hover:bg-primary/5 transition-colors">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-tertiary" />
                    <span className="font-bold">Efficiency Retrofit</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-medium text-on-surface-variant">$115,000</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-surface-container text-on-surface-variant rounded-full text-xs font-bold">
                    Medium
                  </span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+$4.1k/yr</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row justify-center gap-4">
        <Link
          to="/intake"
          className="flex items-center justify-center gap-2 px-8 py-4 bg-surface-container-lowest text-on-surface border border-outline-variant/20 rounded-xl hover:bg-surface-container-low transition-colors shadow-sm font-semibold"
        >
          <span className="material-symbols-outlined">refresh</span>
          New Analysis
        </Link>
        <Link
          to="/case-study"
          className="flex items-center justify-center gap-2 px-8 py-4 bg-gradient-primary text-on-primary rounded-xl hover:opacity-90 transition-opacity shadow-lg font-semibold"
        >
          View Success Story
          <span className="material-symbols-outlined">arrow_forward</span>
        </Link>
      </div>
    </main>
  );
}
