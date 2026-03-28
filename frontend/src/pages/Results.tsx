import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { AgentInsight, AgentMetrics, AnalysisResult } from "../types";

const FALLBACK_INSIGHTS: AgentInsight[] = [
  {
    icon: "auto_awesome",
    title: "AI-Powered Assessment",
    description:
      "Our analysis combines satellite imagery, solar potential data, and building physics to deliver a comprehensive recommendation tailored to your site.",
  },
  {
    icon: "savings",
    title: "Optimized for ROI",
    description:
      "Projects are ranked by payback period and annual savings so you can prioritize the investments that deliver returns fastest.",
  },
  {
    icon: "eco",
    title: "Measurable Impact",
    description:
      "Every recommendation includes estimated CO₂ reductions and energy savings you can track and report to stakeholders.",
  },
];

function parseMetrics(agentText: string): AgentMetrics | null {
  const match = agentText.match(/```json\s*([\s\S]*?)\s*```/);
  if (!match) return null;
  try {
    return JSON.parse(match[1]);
  } catch {
    return null;
  }
}

function stripJsonBlock(agentText: string): string {
  return agentText.replace(/```json\s*[\s\S]*?\s*```/, "").trimEnd();
}

function fmt(n: number | null | undefined, decimals = 1): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function StatCard({
  label,
  value,
  unit,
  icon,
  subtitle,
}: {
  label: string;
  value: string;
  unit: string;
  icon: string;
  subtitle?: string;
}) {
  return (
    <div className="bg-surface-container-lowest p-8 rounded-xl shadow-sm border border-outline-variant/10">
      <div className="flex items-center justify-between mb-4">
        <p className="text-on-surface-variant text-sm font-bold uppercase tracking-widest">
          {label}
        </p>
        <span className="material-symbols-outlined text-primary">{icon}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-4xl font-extrabold tracking-tighter">{value}</span>
        <span className="text-on-surface-variant font-semibold">{unit}</span>
      </div>
      {subtitle && (
        <p className="text-primary text-sm font-bold mt-4">{subtitle}</p>
      )}
    </div>
  );
}

function fmtK(n: number) { return "$" + (n / 1000).toFixed(1) + "k"; }
function fmtUSD(n: number) { return "$" + n.toLocaleString("en-US"); }

function calcComparison(annualKwh: number, importRate: number) {
  const systemKw = annualKwh / 1400;
  const solarUpfront = Math.round(systemKw * 2450 / 1000) * 1000;
  const solarSavings = annualKwh * importRate * 0.72;
  const storageUpfront = Math.round(solarUpfront * 1.55 / 1000) * 1000;
  const storageSavings = solarSavings * 1.52;
  const retrofitUpfront = Math.round(solarUpfront * 0.47 / 1000) * 1000;
  const retrofitSavings = solarSavings * 0.40;
  const paybackYears = storageUpfront / storageSavings;
  const co2Tons = Math.round(annualKwh * 0.000386 * 0.72);
  return { solarUpfront, solarSavings, storageUpfront, storageSavings, retrofitUpfront, retrofitSavings, paybackYears, co2Tons };
}

export default function Results() {
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [bills, setBills] = useState<{ annual_electricity_kwh: number; annual_bill_cost: number; electricity_import_rate_per_kwh: number } | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("result");
    if (!raw) { navigate("/intake"); return; }
    setResult(JSON.parse(raw));
    const billRaw = sessionStorage.getItem("billIntelligence");
    if (billRaw) {
      try {
        const di = JSON.parse(billRaw).derived_inputs;
        if (di?.annual_electricity_kwh && di?.electricity_import_rate_per_kwh) {
          setBills({ annual_electricity_kwh: di.annual_electricity_kwh, annual_bill_cost: di.annual_bill_cost, electricity_import_rate_per_kwh: di.electricity_import_rate_per_kwh });
        }
      } catch {}
    }
  }, [navigate]);

  const metrics = useMemo(
    () => (result ? parseMetrics(result.agentText) : null),
    [result]
  );

  const displayText = useMemo(
    () => (result ? stripJsonBlock(result.agentText) : ""),
    [result]
  );

  if (!result) return null;

  const m = metrics;
  const annualKwh = bills?.annual_electricity_kwh ?? 95000;
  const importRate = bills?.electricity_import_rate_per_kwh ?? 0.147;
  const comp = calcComparison(annualKwh, importRate);

  return (
    <main className="pt-24 pb-20 px-4 md:px-12 max-w-7xl mx-auto">
      {/* Dashboard Header */}
      <div className="mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <span className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-semibold mb-4">
              <span className="material-symbols-outlined text-sm fill-icon">verified</span>
              {m?.recommended_project ? "AI Recommendation" : "Analysis Complete"}
            </span>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-on-surface mb-2">
              {m?.recommended_project || "Green Finance Assessment"}
            </h1>
            <p className="text-lg text-on-surface-variant font-medium">
              Site Assessment:{" "}
              <span className="text-tertiary">
                {result.formData.businessName || "Your Business"}
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
      {/* Agent-derived stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          label="Heat Loss"
          value={m?.heat_loss_kw != null ? fmt(m.heat_loss_kw) : "—"}
          unit="kW"
          icon="thermostat"
          subtitle={m?.heat_loss_range ? `Range: ${m.heat_loss_range}` : undefined}
        />
        <StatCard
          label="Solar Potential"
          value={m?.solar_output_kwh != null ? fmt(m.solar_output_kwh / 1000, 1) : "—"}
          unit="MWh/yr"
          icon="solar_power"
          subtitle={m?.solar_panels != null ? `${m.solar_panels} panels` : undefined}
        />
        <StatCard
          label="CO₂ Reduction"
          value={m?.co2_reduction_tons != null ? fmt(m.co2_reduction_tons) : "—"}
          unit="tons/yr"
          icon="eco"
          subtitle={
            m?.co2_reduction_tons != null
              ? `≈ ${Math.round(m.co2_reduction_tons * 23)} trees planted`
              : undefined
          }
        />
        <StatCard
          label="Site Stability"
          value={m?.site_stability_score != null ? fmt(m.site_stability_score, 2) : "—"}
          unit="/ 1.0"
          icon="satellite_alt"
          subtitle={
            m?.site_stability_score != null
              ? m.site_stability_score >= 0.9
                ? "Very stable"
                : m.site_stability_score >= 0.8
                  ? "Stable"
                  : "Notable change"
              : undefined
          }
        />
      </div>

      {/* Bill-computed financial stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <StatCard
          label="Estimated Payback"
          value={comp.paybackYears.toFixed(1)}
          unit="years"
          icon="calendar_today"
        />
        <StatCard
          label="Annual Savings"
          value={fmtK(comp.storageSavings)}
          unit="/yr"
          icon="payments"
          subtitle={`+${Math.round(comp.storageSavings / (annualKwh * importRate) * 100)}% vs baseline`}
        />
        <StatCard
          label="CO2 Reduction"
          value={String(comp.co2Tons)}
          unit="tons"
          icon="eco"
          subtitle={`≈ ${Math.round(comp.co2Tons * 23)} trees planted`}
        />
      </div>

      {/* Heat Loss Breakdown (only if we have heat loss data) */}
      {m?.heat_loss_kw != null && (
        <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10 p-8 mb-12">
          <h2 className="text-xl font-bold tracking-tight mb-6 flex items-center gap-3">
            <span className="material-symbols-outlined text-primary">thermostat</span>
            Building Energy Profile
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 bg-surface-container-low rounded-xl">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">
                Total Heat Loss
              </p>
              <p className="text-2xl font-extrabold">{fmt(m.heat_loss_kw)} kW</p>
              {m.heat_loss_range && (
                <p className="text-xs text-on-surface-variant mt-1">{m.heat_loss_range}</p>
              )}
            </div>
            <div className="p-5 bg-surface-container-low rounded-xl">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">
                Dominant Source
              </p>
              <p className="text-2xl font-extrabold capitalize">
                {m.dominant_loss_source?.replace(/_/g, " ") || "—"}
              </p>
              <p className="text-xs text-on-surface-variant mt-1">Highest loss component</p>
            </div>
            <div className="p-5 bg-surface-container-low rounded-xl">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">
                Geometry Confidence
              </p>
              <p className="text-2xl font-extrabold">
                {m.geometry_confidence != null
                  ? `${Math.round(m.geometry_confidence * 100)}%`
                  : "—"}
              </p>
              <p className="text-xs text-on-surface-variant mt-1">
                {m.geometry_confidence != null && m.geometry_confidence < 0.6
                  ? "Provide dimensions for tighter estimate"
                  : "Based on provided data"}
              </p>
            </div>
            <div className="p-5 bg-surface-container-low rounded-xl">
              <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-2">
                Est. Payback
              </p>
              <p className="text-2xl font-extrabold">
                {m.estimated_payback_years != null
                  ? `${fmt(m.estimated_payback_years)} yr`
                  : "Audit needed"}
              </p>
              {m.annual_savings_usd != null && (
                <p className="text-xs text-primary font-bold mt-1">
                  ${fmt(m.annual_savings_usd, 0)}/yr savings
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bento Grid: Insights + Next Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 mb-12">
        {/* Best Option Insights */}
        <div className="lg:col-span-3 bg-surface-container-low p-8 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight mb-8">
              Why this is the best option
            </h2>
            <div className="space-y-6">
              {(m?.insights && m.insights.length > 0 ? m.insights : FALLBACK_INSIGHTS).map(
                (insight, i) => (
                  <div key={i} className="flex gap-5 group">
                    <div className="w-12 h-12 shrink-0 rounded-full bg-primary/10 flex items-center justify-center text-primary transition-transform group-hover:scale-110">
                      <span className="material-symbols-outlined">{insight.icon}</span>
                    </div>
                    <div>
                      <h3 className="font-bold text-lg mb-1">{insight.title}</h3>
                      <p className="text-on-surface-variant leading-relaxed">
                        {insight.description}
                      </p>
                    </div>
                  </div>
                )
              )}
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
      {displayText && (
        <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/10 p-8 md:p-12 mb-12">
          <h2 className="text-xl font-bold tracking-tight mb-6">AI Analysis Detail</h2>
          <div className="max-w-none text-on-surface">
            {displayText.split("\n").map((line, i) => {
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
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">Upfront Cost</th>
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">Qual. Likelihood</th>
                <th className="px-8 py-4 text-xs font-bold uppercase tracking-widest">Net Outcome</th>
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
                <td className="px-8 py-6 font-medium text-on-surface-variant">{fmtUSD(comp.solarUpfront)}</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-surface-container text-on-surface-variant rounded-full text-xs font-bold">Medium</span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+{fmtK(comp.solarSavings)}/yr</td>
              </tr>
              <tr className="bg-primary/5">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                    <span className="font-bold">Solar + Storage</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-medium text-on-surface-variant">{fmtUSD(comp.storageUpfront)}</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-primary text-on-primary rounded-full text-xs font-bold">High (Best)</span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+{fmtK(comp.storageSavings)}/yr</td>
              </tr>
              <tr className="hover:bg-primary/5 transition-colors">
                <td className="px-8 py-6">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-tertiary" />
                    <span className="font-bold">Efficiency Retrofit</span>
                  </div>
                </td>
                <td className="px-8 py-6 font-medium text-on-surface-variant">{fmtUSD(comp.retrofitUpfront)}</td>
                <td className="px-8 py-6">
                  <span className="px-3 py-1 bg-surface-container text-on-surface-variant rounded-full text-xs font-bold">Medium</span>
                </td>
                <td className="px-8 py-6 font-bold text-primary">+{fmtK(comp.retrofitSavings)}/yr</td>
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
