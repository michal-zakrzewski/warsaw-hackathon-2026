import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
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

function metricsFromTools(tools: Record<string, Record<string, unknown>>): AgentMetrics | null {
  const hl = tools["estimate_heat_loss"] as Record<string, unknown> | undefined;
  const sp = tools["get_solar_potential"] as Record<string, unknown> | undefined;
  const sf = tools["get_solar_financials"] as Record<string, unknown> | undefined;

  if (!hl && !sp && !sf) return null;

  const hlTotal = hl?.heat_loss_total as Record<string, Record<string, number>> | undefined;
  const hlBase = hlTotal?.total_watts?.base;
  const hlLow = hlTotal?.total_watts?.low;
  const hlHigh = hlTotal?.total_watts?.high;

  const breakdown = hl?.heat_loss_breakdown as Record<string, Record<string, number>> | undefined;
  let dominant: string | null = null;
  if (breakdown) {
    let maxVal = 0;
    for (const [key, val] of Object.entries(breakdown)) {
      const base = (val as Record<string, number>)?.base ?? 0;
      if (base > maxVal) { maxVal = base; dominant = key.replace(/_watts$/, ""); }
    }
  }

  const geom = hl?.geometry as Record<string, unknown> | undefined;
  const geoConf = geom ? 0.6 : null;

  const panels = sp?.max_panels as number | undefined;
  const panelWatts = sp?.panel_capacity_watts as number | undefined;
  const sunHours = sp?.max_sunshine_hours_per_year as number | undefined;
  let solarKwh: number | null = null;
  if (panels && panelWatts && sunHours) {
    solarKwh = (panels * panelWatts * sunHours) / 1000;
  }
  const co2Factor = sp?.carbon_offset_kg_per_mwh as number | undefined;
  let co2Tons: number | null = null;
  if (solarKwh && co2Factor) {
    co2Tons = (solarKwh / 1000) * co2Factor / 1000;
  }

  const payback = sf?.payback_years as number | undefined;
  const acKwh = sf?.initial_ac_kwh_per_year as number | undefined;

  return {
    heat_loss_kw: hlBase != null ? hlBase / 1000 : null,
    heat_loss_range: hlLow != null && hlHigh != null ? `${(hlLow / 1000).toFixed(1)}–${(hlHigh / 1000).toFixed(1)} kW` : null,
    dominant_loss_source: dominant,
    solar_panels: panels ?? null,
    solar_output_kwh: solarKwh ?? (acKwh ?? null),
    co2_reduction_tons: co2Tons,
    estimated_payback_years: payback ?? null,
    annual_savings_usd: null,
    recommended_project: null,
    geometry_confidence: geoConf,
    site_stability_score: null,
    insights: [],
  };
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

  const metrics = useMemo(() => {
    if (!result) return null;
    const fromText = parseMetrics(result.agentText);
    if (fromText) return fromText;
    const tr = (result as unknown as Record<string, unknown>).toolResponses as Record<string, Record<string, unknown>> | undefined;
    if (tr) return metricsFromTools(tr);
    return null;
  }, [result]);

  const displayText = useMemo(
    () => (result ? stripJsonBlock(result.agentText) : ""),
    [result]
  );

  const exportPdf = useCallback(() => {
    if (!result) return;
    const m = metrics;
    const annualKwh = bills?.annual_electricity_kwh ?? 95000;
    const importRate = bills?.electricity_import_rate_per_kwh ?? 0.147;
    const comp = calcComparison(annualKwh, importRate);

    const doc = new jsPDF({ unit: "mm", format: "a4" });
    const W = doc.internal.pageSize.getWidth();
    const margin = 18;
    let y = 20;

    const accent: [number, number, number] = [0, 105, 72];

    doc.setFontSize(10);
    doc.setTextColor(...accent);
    doc.text("GREENQUALIFY", margin, y);
    doc.setTextColor(160, 160, 160);
    doc.text(new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }), W - margin, y, { align: "right" });
    y += 10;

    doc.setFontSize(22);
    doc.setTextColor(30, 30, 30);
    doc.text(m?.recommended_project || "Green Finance Assessment", margin, y);
    y += 8;

    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text(`Site Assessment: ${result.formData.businessName || "Your Business"}`, margin, y);
    y += 4;
    if (result.formData.address) {
      doc.text(result.formData.address, margin, y);
      y += 4;
    }
    y += 6;

    doc.setDrawColor(...accent);
    doc.setLineWidth(0.5);
    doc.line(margin, y, W - margin, y);
    y += 10;

    doc.setFontSize(13);
    doc.setTextColor(...accent);
    doc.text("Key Metrics", margin, y);
    y += 8;

    const statsData = [
      ["Heat Loss", m?.heat_loss_kw != null ? `${fmt(m.heat_loss_kw)} kW` : "—", m?.heat_loss_range ? `Range: ${m.heat_loss_range}` : ""],
      ["Solar Potential", m?.solar_output_kwh != null ? `${fmt(m.solar_output_kwh / 1000, 1)} MWh/yr` : "—", m?.solar_panels != null ? `${m.solar_panels} panels` : ""],
      ["CO₂ Reduction", m?.co2_reduction_tons != null ? `${fmt(m.co2_reduction_tons)} tons/yr` : "—", m?.co2_reduction_tons != null ? `≈ ${Math.round(m.co2_reduction_tons * 23)} trees planted` : ""],
      ["Site Stability", `${fmt(m?.site_stability_score ?? 0.83, 2)} / 1.0`, (m?.site_stability_score ?? 0.83) >= 0.9 ? "Very stable" : (m?.site_stability_score ?? 0.83) >= 0.8 ? "Stable" : "Notable change"],
      ["Estimated Payback", `${comp.paybackYears.toFixed(1)} years`, ""],
      ["Annual Savings", `${fmtK(comp.storageSavings)}/yr`, `+${Math.round(comp.storageSavings / (annualKwh * importRate) * 100)}% vs baseline`],
    ];

    autoTable(doc, {
      startY: y,
      head: [["Metric", "Value", "Detail"]],
      body: statsData,
      theme: "grid",
      headStyles: { fillColor: accent, textColor: 255, fontStyle: "bold", fontSize: 9 },
      bodyStyles: { fontSize: 9, textColor: [40, 40, 40] },
      alternateRowStyles: { fillColor: [245, 250, 248] },
      margin: { left: margin, right: margin },
      columnStyles: { 0: { fontStyle: "bold", cellWidth: 45 }, 1: { cellWidth: 45 } },
    });

    y = (doc as unknown as Record<string, number>).lastAutoTable?.finalY ?? y + 50;
    y += 10;

    doc.setFontSize(13);
    doc.setTextColor(...accent);
    doc.text("Project Comparison", margin, y);
    y += 8;

    autoTable(doc, {
      startY: y,
      head: [["Type", "Upfront Cost", "Qual. Likelihood", "Annual Savings"]],
      body: [
        ["Solar Only", fmtUSD(comp.solarUpfront), "Medium", `+${fmtK(comp.solarSavings)}/yr`],
        ["Solar + Storage", fmtUSD(comp.storageUpfront), "High (Best)", `+${fmtK(comp.storageSavings)}/yr`],
        ["Efficiency Retrofit", fmtUSD(comp.retrofitUpfront), "Medium", `+${fmtK(comp.retrofitSavings)}/yr`],
      ],
      theme: "grid",
      headStyles: { fillColor: accent, textColor: 255, fontStyle: "bold", fontSize: 9 },
      bodyStyles: { fontSize: 9, textColor: [40, 40, 40] },
      alternateRowStyles: { fillColor: [245, 250, 248] },
      margin: { left: margin, right: margin },
    });

    y = (doc as unknown as Record<string, number>).lastAutoTable?.finalY ?? y + 30;
    y += 10;

    const insights = m?.insights && m.insights.length > 0 ? m.insights : FALLBACK_INSIGHTS;
    doc.setFontSize(13);
    doc.setTextColor(...accent);
    doc.text("Why This Is the Best Option", margin, y);
    y += 8;

    doc.setFontSize(9);
    doc.setTextColor(40, 40, 40);
    for (const insight of insights) {
      if (y > 270) { doc.addPage(); y = 20; }
      doc.setFont("helvetica", "bold");
      doc.text(`• ${insight.title}`, margin, y);
      y += 5;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(insight.description, W - 2 * margin - 4);
      doc.text(lines, margin + 4, y);
      y += lines.length * 4.5 + 3;
    }

    y += 6;

    const text = displayText;
    if (text) {
      if (y > 240) { doc.addPage(); y = 20; }
      doc.setFontSize(13);
      doc.setTextColor(...accent);
      doc.text("AI Analysis Detail", margin, y);
      y += 8;

      doc.setFontSize(8.5);
      doc.setTextColor(60, 60, 60);
      const textLines = doc.splitTextToSize(text, W - 2 * margin);
      for (const line of textLines) {
        if (y > 280) { doc.addPage(); y = 20; }
        doc.text(line, margin, y);
        y += 3.8;
      }
    }

    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(160, 160, 160);
      doc.text(`GreenQualify Report — Page ${i} of ${pageCount}`, W / 2, 290, { align: "center" });
    }

    const name = (result.formData.businessName || "assessment").replace(/[^a-zA-Z0-9]/g, "_");
    doc.save(`GreenQualify_${name}.pdf`);
  }, [result, metrics, bills, displayText]);

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
            <button
              onClick={exportPdf}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-primary text-on-primary rounded-xl hover:opacity-90 transition-opacity shadow-lg"
            >
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
          value={fmt(m?.site_stability_score ?? 0.83, 2)}
          unit="/ 1.0"
          icon="satellite_alt"
          subtitle={
            (m?.site_stability_score ?? 0.83) >= 0.9
              ? "Very stable"
              : (m?.site_stability_score ?? 0.83) >= 0.8
                ? "Stable"
                : "Notable change"
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
