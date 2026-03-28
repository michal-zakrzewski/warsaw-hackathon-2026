import { useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { processBills } from "../api/bills";
import type { IntakeFormData, VoiceExtractedData } from "../types";
import VoiceChat from "../components/VoiceChat";

const BUSINESS_TYPES = [
  "SME (Small/Medium Enterprise)",
  "Manufacturing",
  "Farm / Agriculture",
  "Retail / Service",
  "Non-Profit",
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


export default function IntakeForm() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [billFiles, setBillFiles] = useState<File[]>([]);
  const [billsProcessing, setBillsProcessing] = useState(false);
  const [billsError, setBillsError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [voiceContext, setVoiceContext] = useState<string | null>(null);
  const [voiceFilled, setVoiceFilled] = useState(false);
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
    footprintArea: "",
  });

  const handleVoiceExtracted = useCallback((data: VoiceExtractedData) => {
    setForm((prev) => {
      const updated = { ...prev };
      if (data.businessName && !prev.businessName) updated.businessName = data.businessName;
      if (data.businessType) {
        const match = BUSINESS_TYPES.find(
          (t) => t.toLowerCase().includes(data.businessType!.toLowerCase())
        );
        if (match && prev.businessType === BUSINESS_TYPES[0]) updated.businessType = match;
      }
      if (data.address && !prev.address) updated.address = data.address;
      if (data.latitude && !prev.latitude) updated.latitude = data.latitude;
      if (data.longitude && !prev.longitude) updated.longitude = data.longitude;
      if (data.annualEnergy && !prev.annualEnergy) updated.annualEnergy = data.annualEnergy;
      if (data.estimatedBudget && prev.estimatedBudget === "$15,000 - $50,000") {
        updated.estimatedBudget = data.estimatedBudget;
      }
      if (data.sustainabilityGoal && !prev.sustainabilityGoal) {
        updated.sustainabilityGoal = data.sustainabilityGoal;
      }
      return updated;
    });

    if (data.additionalContext) {
      setVoiceContext(data.additionalContext);
    }
    setVoiceFilled(true);
  }, []);

  const set =
    (field: keyof IntakeFormData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setBillFiles(Array.from(e.target.files));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) setBillFiles(Array.from(e.dataTransfer.files));
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setImagePreview(dataUrl);
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

  const next = async () => {
    if (step < 2) {
      setStep(step + 1);
      return;
    }
    setBillsProcessing(true);
    setBillsError(null);
    try {
      let billResult = null;
      if (billFiles.length > 0) {
        const buildingId = form.businessName.replace(/\s+/g, "-").toLowerCase() || "building";
        billResult = await processBills(buildingId, billFiles);
        const kwh = billResult.derived_inputs.annual_electricity_kwh;
        if (kwh && !form.annualEnergy) {
          setForm((prev) => ({ ...prev, annualEnergy: String(Math.round(kwh)) }));
        }
      }
      sessionStorage.setItem("intake", JSON.stringify(form));
      if (billResult) sessionStorage.setItem("billIntelligence", JSON.stringify(billResult));
      if (voiceContext) sessionStorage.setItem("voiceContext", voiceContext);
      navigate("/loading");
    } catch (err) {
      setBillsError(err instanceof Error ? err.message : "Bill processing failed");
      setBillsProcessing(false);
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
                  "Upload a building photo for AI-powered analysis, and tell us the floor area for a tighter estimate."}
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
                <div className="space-y-8">
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
                          The AI will identify wall material, windows, roof type, insulation signs, cracks & degradation
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

                  {/* Footprint Area */}
                  <div className="space-y-2">
                    <label className="block text-sm font-bold text-on-surface-variant ml-1">
                      Ground Floor Area
                    </label>
                    <div className="relative">
                      <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-primary">
                        straighten
                      </span>
                      <input
                        className="w-full bg-surface-container-highest/40 border-none rounded-2xl pl-12 pr-16 py-4 focus:ring-2 focus:ring-primary transition-all text-on-surface placeholder:text-outline/50"
                        placeholder="e.g. 800"
                        type="number"
                        value={form.footprintArea}
                        onChange={set("footprintArea")}
                      />
                      <span className="absolute right-5 top-1/2 -translate-y-1/2 text-sm font-bold text-emerald-700">
                        m²
                      </span>
                    </div>
                    <p className="text-xs text-on-surface-variant/60 ml-1">
                      Optional — improves heat-loss accuracy. The AI estimates everything else from the photo.
                    </p>
                  </div>

                  {/* Utility Bills Upload */}
                  <div className="space-y-2">
                    <label className="block text-sm font-bold text-on-surface-variant ml-1">
                      Utility Bills
                    </label>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,image/png,image/jpeg,image/tiff,image/gif,image/webp"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                    <div
                      className="border-2 border-dashed border-outline-variant/30 rounded-2xl p-8 text-center cursor-pointer hover:border-primary/40 hover:bg-emerald-50/30 transition-all"
                      onClick={() => fileInputRef.current?.click()}
                      onDrop={handleDrop}
                      onDragOver={(e) => e.preventDefault()}
                    >
                      <span className="material-symbols-outlined text-4xl text-on-surface-variant/40 mb-3 block">
                        upload_file
                      </span>
                      <p className="text-on-surface-variant font-medium mb-1">
                        Drag & drop utility bills here, or click to browse
                      </p>
                      <p className="text-xs text-on-surface-variant/60">
                        PDF or images — optional but enables accurate energy cost analysis
                      </p>
                    </div>

                    {billFiles.length > 0 && (
                      <ul className="space-y-2">
                        {billFiles.map((f) => (
                          <li
                            key={f.name}
                            className="flex items-center gap-3 px-4 py-3 bg-emerald-50 rounded-xl text-sm text-emerald-800"
                          >
                            <span className="material-symbols-outlined text-base">description</span>
                            <span className="font-medium truncate">{f.name}</span>
                            <span className="ml-auto text-emerald-600 text-xs">
                              {(f.size / 1024).toFixed(0)} KB
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
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
                  {form.footprintArea && (
                    <>
                      <h4 className="text-sm font-bold text-primary uppercase tracking-wider pt-2">
                        Building Details
                      </h4>
                      <div className="flex justify-between items-start py-3 border-b border-surface-container-high last:border-none">
                        <span className="text-sm font-bold text-on-surface-variant">Ground Floor Area</span>
                        <span className="text-sm text-on-surface text-right">{form.footprintArea} m²</span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </section>

            {/* Navigation */}
            <div className="flex flex-col gap-3 pt-4">
              {billsError && (
                <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                  {billsError}
                </div>
              )}
              <div className="flex items-center justify-between gap-6">
                {step > 0 ? (
                  <button
                    onClick={prev}
                    disabled={billsProcessing}
                    className="px-8 py-4 border border-outline-variant/20 text-on-surface rounded-full font-bold text-lg hover:bg-surface-container-low transition-colors flex items-center gap-2 disabled:opacity-40"
                  >
                    <span className="material-symbols-outlined">arrow_back</span> Back
                  </button>
                ) : (
                  <div />
                )}
                <button
                  onClick={next}
                  disabled={billsProcessing}
                  className="px-10 py-5 bg-primary-gradient text-on-primary rounded-full font-bold text-lg shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3 disabled:opacity-60 disabled:scale-100"
                >
                  {billsProcessing ? (
                    <>
                      <span className="animate-spin material-symbols-outlined text-xl">progress_activity</span>
                      Processing bills...
                    </>
                  ) : (
                    <>
                      {step === 0 && "Continue to Building Details"}
                      {step === 1 && "Continue to Review"}
                      {step === 2 && "Run Analysis"}
                      <span className="material-symbols-outlined">arrow_forward</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Voice Assistant */}
          <div className="xl:col-span-5 space-y-4">
            {voiceFilled && (
              <div className="flex items-center gap-3 px-5 py-3 bg-emerald-50 border border-emerald-200 rounded-2xl">
                <span className="material-symbols-outlined text-emerald-600 fill-icon text-lg">
                  check_circle
                </span>
                <p className="text-sm font-medium text-emerald-800">
                  Voice data applied to the form. Review and adjust if needed.
                </p>
              </div>
            )}
            <VoiceChat onExtracted={handleVoiceExtracted} />
          </div>
        </div>
      </main>
    </>
  );
}
