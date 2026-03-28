import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { IntakeFormData } from "../types";

const BUSINESS_TYPES = [
  "SME (Small/Medium Enterprise)",
  "Manufacturing",
  "Farm / Agriculture",
  "Retail / Service",
  "Non-Profit",
];

const BUILDING_TYPES = [
  "house",
  "apartment_block",
  "office",
  "warehouse",
  "industrial",
  "unknown",
];

const ROOF_TYPES = ["flat", "gable", "hip", "shed", "mansard", "sawtooth", "unknown"];

const WALL_MATERIALS = [
  "brick",
  "concrete",
  "aac",
  "timber_frame",
  "steel_frame",
  "sandwich_panel",
  "glass_curtain",
  "mixed",
  "unknown",
];

const WINDOW_TYPES = [
  "single_glazed",
  "double_glazed",
  "triple_glazed",
  "mixed",
  "unknown",
];

const STEPS = ["Business Info", "Building Details", "Review"];

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex gap-2 w-full pt-4">
      {STEPS.map((_, i) => (
        <div
          key={i}
          className={`h-1.5 flex-1 rounded-full ${
            i <= current ? "bg-primary" : "bg-surface-container-highest"
          }`}
        />
      ))}
    </div>
  );
}

function Sidebar({ current }: { current: number }) {
  const items = [
    { icon: "business_center", label: "Business Info" },
    { icon: "apartment", label: "Building Details" },
    { icon: "fact_check", label: "Review" },
  ];
  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] w-64 border-r border-emerald-100/50 bg-slate-50 p-4 hidden lg:flex flex-col gap-2">
      <div className="px-4 py-6 mb-4">
        <h2 className="text-lg font-extrabold text-emerald-800">Intake Wizard</h2>
        <p className="text-xs text-slate-500">Step-by-step guidance</p>
      </div>
      <nav className="flex flex-col gap-2 flex-grow">
        {items.map((item, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium cursor-pointer transition-all ${
              i === current
                ? "text-emerald-700 bg-emerald-100/50 font-bold"
                : "text-slate-500 hover:bg-emerald-50"
            }`}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
      <div className="mt-auto p-4 bg-surface-container-low rounded-2xl border border-outline-variant/10">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-symbols-outlined text-emerald-600 text-sm fill-icon">
            verified_user
          </span>
          <span className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">
            Secured Portal
          </span>
        </div>
        <p className="text-[10px] text-on-surface-variant leading-relaxed">
          Your data is encrypted with 256-bit SSL technology. GreenQualify never shares private
          financial data.
        </p>
      </div>
    </aside>
  );
}

function AssistantPanel() {
  return (
    <div className="xl:col-span-5 sticky top-24">
      <div className="bg-surface-container-low rounded-[2rem] overflow-hidden flex flex-col h-[680px] border border-surface-container-high relative">
        {/* Header */}
        <div className="p-6 flex items-center justify-between bg-white/40 backdrop-blur-sm border-b border-surface-container-high/50">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse" />
            <h3 className="font-bold text-on-surface tracking-tight">Assistant Live</h3>
          </div>
          <button className="w-10 h-10 rounded-full bg-white/80 flex items-center justify-center text-on-surface-variant hover:bg-white transition-colors">
            <span className="material-symbols-outlined text-xl">settings</span>
          </button>
        </div>

        {/* Voice Visualizer */}
        <div className="px-6 py-10 flex flex-col items-center justify-center gap-4 bg-emerald-50/30">
          <div className="relative">
            <div className="absolute inset-0 scale-150 rounded-full border border-emerald-200 animate-ping opacity-20" />
            <div className="absolute inset-0 scale-125 rounded-full border border-emerald-300 animate-ping opacity-30" />
            <div className="w-20 h-20 bg-primary-gradient rounded-full flex items-center justify-center text-white shadow-xl z-10 relative">
              <span className="material-symbols-outlined text-3xl fill-icon">mic</span>
            </div>
          </div>
          <p className="text-sm font-bold text-emerald-800 uppercase tracking-widest">
            Listening...
          </p>
        </div>

        {/* Chat Transcript */}
        <div className="flex-grow p-6 overflow-y-auto space-y-6 flex flex-col">
          {/* AI Bubble */}
          <div className="flex gap-3 max-w-[90%]">
            <div className="w-8 h-8 rounded-full bg-emerald-600 flex-shrink-0 flex items-center justify-center text-white text-[10px] font-bold">
              GQ
            </div>
            <div className="bg-white rounded-2xl rounded-tl-none p-4 shadow-sm border border-emerald-50/50">
              <p className="text-sm text-on-surface leading-relaxed italic">
                "I see you are a small factory. Would you like to prioritize grants for
                energy-efficiency upgrades like LED lighting or HVAC retrofits?"
              </p>
            </div>
          </div>

          {/* User Bubble */}
          <div className="flex gap-3 max-w-[90%] self-end flex-row-reverse">
            <div className="w-8 h-8 rounded-full bg-slate-200 flex-shrink-0 flex items-center justify-center text-slate-600">
              <span className="material-symbols-outlined text-sm">person</span>
            </div>
            <div className="bg-primary text-on-primary rounded-2xl rounded-tr-none p-4 shadow-sm">
              <p className="text-sm font-medium">"Yes, both please."</p>
            </div>
          </div>

          <div className="flex-grow" />

          {/* Suggestion Chips */}
          <div className="flex flex-wrap gap-2">
            <div className="px-4 py-2 bg-white/60 hover:bg-white border border-surface-container-high rounded-full text-xs font-semibold text-on-surface-variant cursor-pointer transition-all">
              Tell me about LED grants
            </div>
            <div className="px-4 py-2 bg-white/60 hover:bg-white border border-surface-container-high rounded-full text-xs font-semibold text-on-surface-variant cursor-pointer transition-all">
              How much can I save?
            </div>
          </div>
        </div>

        {/* Bottom Input */}
        <div className="p-6 bg-white/40 border-t border-surface-container-high/50 flex gap-4">
          <div className="flex-grow bg-white rounded-2xl px-4 py-3 border border-surface-container-high flex items-center">
            <input
              className="w-full border-none focus:ring-0 text-sm bg-transparent"
              placeholder="Type or ask follow-up..."
              type="text"
            />
          </div>
          <button className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center text-on-primary hover:bg-primary-container transition-all">
            <span className="material-symbols-outlined">send</span>
          </button>
        </div>
      </div>

      {/* Decorative */}
      <div className="mt-6 flex items-center justify-center gap-4 opacity-40">
        <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Powering Sustainable Growth
        </p>
      </div>
    </div>
  );
}

export default function IntakeForm() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [form, setForm] = useState<IntakeFormData>({
    businessName: "",
    businessType: BUSINESS_TYPES[0],
    address: "",
    latitude: "",
    longitude: "",
    annualEnergy: "",
    estimatedBudget: "$15,000 - $50,000",
    sustainabilityGoal: "",
    buildingType: "unknown",
    roofType: "unknown",
    wallMaterial: "unknown",
    windowType: "unknown",
    footprintArea: "",
    floorsCount: "",
    floorHeight: "",
  });

  const set =
    (field: keyof IntakeFormData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setImagePreview(dataUrl);
      // Store base64 separately — keep IntakeFormData small
      const base64 = dataUrl.split(",")[1];
      const mimeType = file.type || "image/jpeg";
      sessionStorage.setItem(
        "buildingImage",
        JSON.stringify({ base64, mimeType })
      );
    };
    reader.readAsDataURL(file);
  };

  const removeImage = () => {
    setImagePreview(null);
    sessionStorage.removeItem("buildingImage");
  };

  const next = () => {
    if (step < 2) setStep(step + 1);
    else {
      sessionStorage.setItem("intake", JSON.stringify(form));
      navigate("/loading");
    }
  };

  const prev = () => step > 0 && setStep(step - 1);

  return (
    <>
      {/* Intake-specific header */}
      <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md shadow-sm border-b border-emerald-100/20 px-6 py-4 flex justify-between items-center h-16">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold text-emerald-900">GreenQualify</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-6 mr-6">
            <span className="text-emerald-700 font-semibold text-sm">Intake Wizard</span>
            <span className="text-slate-500 text-sm">Dashboard</span>
            <span className="text-slate-500 text-sm">Programs</span>
          </div>
          <button className="p-2 rounded-full hover:bg-emerald-50 transition-colors">
            <span className="material-symbols-outlined text-on-surface-variant">account_circle</span>
          </button>
        </div>
      </header>

      <Sidebar current={step} />

      <main className="pt-24 pb-12 lg:pl-72 lg:pr-12 px-6 min-h-screen">
        <div className="max-w-6xl mx-auto grid grid-cols-1 xl:grid-cols-12 gap-10 items-start">
          {/* Left Column: Intake Form */}
          <div className="xl:col-span-7 space-y-8">
            <header className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full text-xs font-bold uppercase tracking-widest">
                Step {step + 1} of 3
              </div>
              <h1 className="text-4xl font-extrabold text-on-surface tracking-tight">
                {STEPS[step]}
              </h1>
              <p className="text-on-surface-variant text-lg max-w-xl">
                {step === 0 &&
                  "Let's start with the basics. This information helps us identify the most relevant green subsidies for your sector."}
                {step === 1 &&
                  "Tell us about the building — the more you share, the more accurate our heat-loss and energy analysis will be."}
                {step === 2 && "Review your information before we run the analysis."}
              </p>
              <StepIndicator current={step} />
            </header>

            <section className="bg-surface-container-lowest rounded-3xl p-8 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.04)] border border-surface-container-low">
              {step === 0 && (
                <form className="space-y-8" onSubmit={(e) => e.preventDefault()}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Business Name
                      </label>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="e.g. EcoFab Manufacturing"
                        value={form.businessName}
                        onChange={set("businessName")}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Business Type
                      </label>
                      <div className="relative">
                        <select
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary appearance-none transition-all text-on-surface"
                          value={form.businessType}
                          onChange={set("businessType")}
                        >
                          {BUSINESS_TYPES.map((t) => (
                            <option key={t}>{t}</option>
                          ))}
                        </select>
                        <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                          expand_more
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-bold text-on-surface-variant ml-1">
                      Address / Location
                    </label>
                    <div className="relative group">
                      <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-primary group-focus-within:text-primary-container transition-colors">
                        location_on
                      </span>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl pl-12 pr-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="Search for your business address"
                        value={form.address}
                        onChange={set("address")}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Latitude
                      </label>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="e.g. 52.2297"
                        value={form.latitude}
                        onChange={set("latitude")}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Longitude
                      </label>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="e.g. 21.0122"
                        value={form.longitude}
                        onChange={set("longitude")}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Annual Energy Usage
                      </label>
                      <div className="relative">
                        <input
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                          placeholder="0.00"
                          type="number"
                          value={form.annualEnergy}
                          onChange={set("annualEnergy")}
                        />
                        <span className="absolute right-5 top-1/2 -translate-y-1/2 text-sm font-bold text-emerald-700">
                          kWh
                        </span>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center ml-1">
                        <label className="block text-sm font-bold text-on-surface-variant">
                          Estimated Budget
                        </label>
                        <span className="text-sm font-extrabold text-primary">
                          {form.estimatedBudget}
                        </span>
                      </div>
                      <input
                        className="w-full h-2 bg-surface-container-high rounded-lg appearance-none cursor-pointer accent-primary"
                        type="range"
                        min="5000"
                        max="500000"
                        step="5000"
                        defaultValue="15000"
                        onChange={(e) => {
                          const v = Number(e.target.value);
                          const lo = `$${(v).toLocaleString()}`;
                          const hi = `$${(v * 2).toLocaleString()}`;
                          setForm((prev) => ({ ...prev, estimatedBudget: `${lo} - ${hi}` }));
                        }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-bold text-on-surface-variant ml-1">
                      Primary Sustainability Goal
                    </label>
                    <textarea
                      className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50 resize-none"
                      placeholder="Tell us what you want to achieve (e.g., reducing carbon footprint, cutting energy costs...)"
                      rows={3}
                      value={form.sustainabilityGoal}
                      onChange={set("sustainabilityGoal")}
                    />
                  </div>
                </form>
              )}

              {step === 1 && (
                <form className="space-y-8" onSubmit={(e) => e.preventDefault()}>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="material-symbols-outlined text-primary text-xl">info</span>
                    <p className="text-sm text-on-surface-variant">
                      Upload a building photo for AI-powered visual analysis, or fill in the details manually — or both for the best results.
                    </p>
                  </div>

                  {/* Building Photo Upload */}
                  <div className="space-y-2">
                    <label className="block text-sm font-bold text-on-surface-variant ml-1">
                      Building Photograph
                    </label>
                    {!imagePreview ? (
                      <label className="border-2 border-dashed border-primary/30 rounded-2xl p-8 text-center cursor-pointer hover:border-primary/60 hover:bg-emerald-50/30 transition-all block group">
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="hidden"
                          onChange={handleImageUpload}
                        />
                        <span className="material-symbols-outlined text-4xl text-primary/40 group-hover:text-primary/70 mb-3 block transition-colors">
                          add_a_photo
                        </span>
                        <p className="text-on-surface-variant font-medium mb-1">
                          Upload a photo of the building facade
                        </p>
                        <p className="text-xs text-on-surface-variant/60">
                          The AI will analyze wall material, windows, roof, insulation signs, cracks & degradation
                        </p>
                      </label>
                    ) : (
                      <div className="relative rounded-2xl overflow-hidden border border-surface-container-high">
                        <img
                          src={imagePreview}
                          alt="Building preview"
                          className="w-full max-h-64 object-cover"
                        />
                        <div className="absolute top-3 right-3 flex gap-2">
                          <button
                            type="button"
                            onClick={removeImage}
                            className="w-10 h-10 rounded-full bg-red-500/90 backdrop-blur-sm flex items-center justify-center text-white hover:bg-red-600 transition-colors shadow-lg"
                          >
                            <span className="material-symbols-outlined text-lg">close</span>
                          </button>
                        </div>
                        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent px-4 py-3">
                          <div className="flex items-center gap-2 text-white/90">
                            <span className="material-symbols-outlined text-sm fill-icon">
                              check_circle
                            </span>
                            <span className="text-xs font-bold">
                              Photo ready — AI will analyze during assessment
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="relative flex items-center gap-4">
                    <div className="flex-grow border-t border-surface-container-high" />
                    <span className="text-xs font-bold text-on-surface-variant/50 uppercase tracking-widest">
                      or specify manually
                    </span>
                    <div className="flex-grow border-t border-surface-container-high" />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Building Type
                      </label>
                      <div className="relative">
                        <select
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary appearance-none transition-all text-on-surface capitalize"
                          value={form.buildingType}
                          onChange={set("buildingType")}
                        >
                          {BUILDING_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                        <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                          expand_more
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Roof Type
                      </label>
                      <div className="relative">
                        <select
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary appearance-none transition-all text-on-surface capitalize"
                          value={form.roofType}
                          onChange={set("roofType")}
                        >
                          {ROOF_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                        <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                          expand_more
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Wall Material
                      </label>
                      <div className="relative">
                        <select
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary appearance-none transition-all text-on-surface capitalize"
                          value={form.wallMaterial}
                          onChange={set("wallMaterial")}
                        >
                          {WALL_MATERIALS.map((t) => (
                            <option key={t} value={t}>
                              {t.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                        <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                          expand_more
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Window Type
                      </label>
                      <div className="relative">
                        <select
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary appearance-none transition-all text-on-surface capitalize"
                          value={form.windowType}
                          onChange={set("windowType")}
                        >
                          {WINDOW_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                        <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-outline">
                          expand_more
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Footprint Area
                      </label>
                      <div className="relative">
                        <input
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                          placeholder="e.g. 3000"
                          type="number"
                          value={form.footprintArea}
                          onChange={set("footprintArea")}
                        />
                        <span className="absolute right-5 top-1/2 -translate-y-1/2 text-sm font-bold text-emerald-700">
                          m²
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Number of Floors
                      </label>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="e.g. 1"
                        type="number"
                        min="1"
                        max="50"
                        value={form.floorsCount}
                        onChange={set("floorsCount")}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="block text-sm font-bold text-on-surface-variant ml-1">
                        Floor Height
                      </label>
                      <div className="relative">
                        <input
                          className="w-full bg-surface-container-highest/40 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                          placeholder="e.g. 7.0"
                          type="number"
                          step="0.1"
                          value={form.floorHeight}
                          onChange={set("floorHeight")}
                        />
                        <span className="absolute right-5 top-1/2 -translate-y-1/2 text-sm font-bold text-emerald-700">
                          m
                        </span>
                      </div>
                    </div>
                  </div>
                </form>
              )}

              {step === 2 && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold mb-4">Review your information</h3>
                  {(
                    [
                      ["Business Name", form.businessName],
                      ["Business Type", form.businessType],
                      ["Address", form.address],
                      [
                        "Coordinates",
                        form.latitude && form.longitude
                          ? `${form.latitude}, ${form.longitude}`
                          : "Not provided",
                      ],
                      [
                        "Annual Energy Usage",
                        form.annualEnergy ? `${form.annualEnergy} kWh` : "Not provided",
                      ],
                      ["Estimated Budget", form.estimatedBudget],
                      ["Sustainability Goal", form.sustainabilityGoal || "Not provided"],
                    ] as [string, string][]
                  ).map(([label, value]) => (
                    <div
                      key={label}
                      className="flex justify-between items-start py-3 border-b border-surface-container-high last:border-none"
                    >
                      <span className="text-sm font-bold text-on-surface-variant">{label}</span>
                      <span className="text-sm text-on-surface text-right max-w-xs">
                        {value || "—"}
                      </span>
                    </div>
                  ))}

                  {/* Building Photo */}
                  {imagePreview && (
                    <div className="pt-2">
                      <h4 className="text-sm font-bold text-primary uppercase tracking-wider mb-3">
                        Building Photo
                      </h4>
                      <img
                        src={imagePreview}
                        alt="Building"
                        className="w-full max-h-48 object-cover rounded-xl border border-surface-container-high"
                      />
                      <p className="text-xs text-on-surface-variant mt-2">
                        AI will visually analyze this photo for wall material, cracks, insulation signs, and more.
                      </p>
                    </div>
                  )}

                  {/* Building Details subsection */}
                  {(form.buildingType !== "unknown" ||
                    form.roofType !== "unknown" ||
                    form.wallMaterial !== "unknown" ||
                    form.windowType !== "unknown" ||
                    form.footprintArea ||
                    form.floorsCount ||
                    form.floorHeight) && (
                    <>
                      <h4 className="text-sm font-bold text-primary uppercase tracking-wider pt-2">
                        Building Details
                      </h4>
                      {(
                        [
                          ["Building Type", form.buildingType !== "unknown" ? form.buildingType.replace(/_/g, " ") : null],
                          ["Roof Type", form.roofType !== "unknown" ? form.roofType.replace(/_/g, " ") : null],
                          ["Wall Material", form.wallMaterial !== "unknown" ? form.wallMaterial.replace(/_/g, " ") : null],
                          ["Window Type", form.windowType !== "unknown" ? form.windowType.replace(/_/g, " ") : null],
                          ["Footprint Area", form.footprintArea ? `${form.footprintArea} m²` : null],
                          ["Floors", form.floorsCount || null],
                          ["Floor Height", form.floorHeight ? `${form.floorHeight} m` : null],
                        ] as [string, string | null][]
                      )
                        .filter(([, v]) => v)
                        .map(([label, value]) => (
                          <div
                            key={label}
                            className="flex justify-between items-start py-3 border-b border-surface-container-high last:border-none"
                          >
                            <span className="text-sm font-bold text-on-surface-variant">{label}</span>
                            <span className="text-sm text-on-surface text-right max-w-xs capitalize">
                              {value}
                            </span>
                          </div>
                        ))}
                    </>
                  )}
                </div>
              )}
            </section>

            {/* Navigation */}
            <div className="flex items-center justify-between gap-6 pt-4">
              {step > 0 ? (
                <button
                  onClick={prev}
                  className="px-8 py-4 border border-outline-variant/20 text-on-surface rounded-full font-bold text-lg hover:bg-surface-container-low transition-colors flex items-center gap-2"
                >
                  <span className="material-symbols-outlined">arrow_back</span> Back
                </button>
              ) : (
                <div />
              )}
              <button
                onClick={next}
                className="px-10 py-5 bg-primary-gradient text-on-primary rounded-full font-bold text-lg shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3"
              >
                {step === 0 && "Continue to Building Details"}
                {step === 1 && "Continue to Review"}
                {step === 2 && "Run Analysis"}
                <span className="material-symbols-outlined">arrow_forward</span>
              </button>
            </div>
          </div>

          {/* Right Column: Assistant Live Panel */}
          <AssistantPanel />
        </div>
      </main>
    </>
  );
}
