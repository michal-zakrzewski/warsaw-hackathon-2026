import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createSession, runAgent, extractAgentText } from "../api/agent";
import type { IntakeFormData } from "../types";

const STATUS_STEPS = [
  "Understanding your business...",
  "Reviewing uploaded information...",
  "Estimating project options...",
  "Matching financing opportunities...",
  "Preparing recommendation...",
];

export default function AnalysisLoading() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(10);

  useEffect(() => {
    const raw = sessionStorage.getItem("intake");
    if (!raw) {
      navigate("/intake");
      return;
    }

    const form: IntakeFormData = JSON.parse(raw);

    const userId = `user_${Date.now()}`;
    const sessionId = `session_${Date.now()}`;

    const prompt = [
      `Analyze this business for green financing eligibility:`,
      `Business: ${form.businessName} (${form.businessType})`,
      `Location: ${form.address}`,
      form.latitude && form.longitude ? `Coordinates: ${form.latitude}, ${form.longitude}` : "",
      form.annualEnergy ? `Annual energy usage: ${form.annualEnergy} kWh` : "",
      `Budget: ${form.estimatedBudget}`,
      form.sustainabilityGoal ? `Goal: ${form.sustainabilityGoal}` : "",
      ``,
      `Provide: recommended financing path, estimated payback period, annual savings, CO2 reduction, and comparison of at least 3 project types.`,
    ]
      .filter(Boolean)
      .join("\n");

    const stepInterval = setInterval(() => {
      setActiveStep((s) => Math.min(s + 1, STATUS_STEPS.length - 1));
      setProgress((p) => Math.min(p + 18, 90));
    }, 3000);

    (async () => {
      try {
        await createSession(userId, sessionId);
        const events = await runAgent(userId, sessionId, prompt);
        const text = extractAgentText(events);
        sessionStorage.setItem("result", JSON.stringify({ agentText: text, formData: form }));
        setProgress(100);
        clearInterval(stepInterval);
        setTimeout(() => navigate("/results"), 600);
      } catch (err) {
        console.error("Agent error:", err);
        sessionStorage.setItem(
          "result",
          JSON.stringify({
            agentText: "Analysis could not be completed. The agent service may be unavailable. Please ensure `adk api_server green_agent` is running on port 8000.",
            formData: form,
          })
        );
        clearInterval(stepInterval);
        navigate("/results");
      }
    })();

    return () => clearInterval(stepInterval);
  }, [navigate]);

  return (
    <>
      <header className="fixed top-0 w-full z-50 bg-white/40 backdrop-blur-md">
        <div className="flex justify-between items-center px-8 py-6 max-w-7xl mx-auto">
          <div className="text-2xl font-extrabold tracking-tighter text-emerald-900">Concierge</div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant/60">Secure Session</span>
            <span className="material-symbols-outlined text-emerald-700 text-sm fill-icon">lock</span>
          </div>
        </div>
      </header>

      <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden px-6">
        <div className="absolute inset-0 z-0">
          <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-emerald-50/50 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-secondary-container/30 rounded-full blur-[100px]" />
        </div>

        <div className="z-10 w-full max-w-xl flex flex-col items-center text-center">
          <div className="mb-12 relative">
            <div className="w-32 h-32 rounded-full bg-surface-container-lowest flex items-center justify-center shadow-sm animate-subtle border border-emerald-50">
              <span className="material-symbols-outlined text-primary text-5xl">auto_awesome</span>
            </div>
            <div className="absolute inset-0 -m-4 border border-emerald-100/50 rounded-full" />
            <div className="absolute inset-0 -m-8 border border-emerald-50/30 rounded-full" />
          </div>

          <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight mb-4">
            Personalizing your experience
          </h1>

          <div className="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden mb-8 max-w-sm">
            <div
              className="bg-gradient-to-r from-primary to-primary-container h-full rounded-full shadow-[0_0_12px_rgba(0,105,72,0.3)] transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="bg-surface-container-low rounded-xl px-8 py-4 border border-surface-variant/20 inline-flex items-center gap-4">
            <div className="flex space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-pulse" style={{ animationDelay: "75ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-primary/30 animate-pulse" style={{ animationDelay: "150ms" }} />
            </div>
            <p className="text-on-surface-variant font-medium text-lg">
              {STATUS_STEPS[activeStep]}
            </p>
          </div>

          <div className="mt-12 w-full grid grid-cols-1 gap-3">
            {STATUS_STEPS.map((label, i) => (
              <div key={i} className={`flex items-center justify-center gap-3 text-sm ${i > activeStep ? "opacity-30" : "opacity-60"}`}>
                <span className={`material-symbols-outlined text-base ${i <= activeStep ? "text-primary fill-icon" : "text-on-surface-variant/40"}`}>
                  {i <= activeStep ? "check_circle" : "radio_button_unchecked"}
                </span>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
