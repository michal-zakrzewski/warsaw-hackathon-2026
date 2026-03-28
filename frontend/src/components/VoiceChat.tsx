import { useState, useEffect, useRef, useCallback } from "react";
import VapiModule from "@vapi-ai/web";
import type { VoiceExtractedData } from "../types";

// Handle CJS/ESM interop — the package exports `default` as a named property
const Vapi = (typeof (VapiModule as unknown as { default: unknown }).default === "function"
  ? (VapiModule as unknown as { default: typeof VapiModule }).default
  : VapiModule) as typeof VapiModule;

interface TranscriptMessage {
  role: string;
  content: string;
  timestamp: string;
}

interface VoiceConfig {
  publicKey: string;
  interviewTitle: string;
  assistantConfig: Record<string, unknown>;
}

type CallStatus = "idle" | "loading" | "live" | "ended" | "error";

interface VoiceChatProps {
  onExtracted?: (data: VoiceExtractedData) => void;
}

export default function VoiceChat({ onExtracted }: VoiceChatProps) {
  const [status, setStatus] = useState<CallStatus>("idle");
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);

  const vapiRef = useRef<Vapi | null>(null);
  const configRef = useRef<VoiceConfig | null>(null);
  const transcriptRef = useRef<TranscriptMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  const fetchConfig = useCallback(async () => {
    const res = await fetch("/api/voice/config");
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    configRef.current = await res.json();
  }, []);

  const appendMessage = useCallback((role: string, text: string) => {
    if (!text?.trim()) return;

    setTranscript((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === role) {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...last,
          content: last.content + " " + text,
        };
        return updated;
      }
      return [
        ...prev,
        { role, content: text, timestamp: new Date().toISOString() },
      ];
    });
  }, []);

  const saveTranscript = useCallback(async () => {
    const messages = transcriptRef.current;
    if (messages.length === 0) return;
    try {
      await fetch("/api/voice/transcripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interviewTitle: configRef.current?.interviewTitle ?? "Interview",
          messages,
        }),
      });
    } catch (err) {
      console.error("Failed to save transcript:", err);
    }

    if (onExtracted && messages.length > 1) {
      setExtracting(true);
      try {
        const res = await fetch("/api/voice/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.extracted) {
            onExtracted(data.extracted);
          }
        }
      } catch (err) {
        console.error("Failed to extract from transcript:", err);
      } finally {
        setExtracting(false);
      }
    }
  }, [onExtracted]);

  const startCall = useCallback(async () => {
    setError(null);
    setStatus("loading");

    try {
      if (!configRef.current) {
        await fetchConfig();
      }
      const config = configRef.current!;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((t) => t.stop());

      const vapi = new Vapi(config.publicKey);
      vapiRef.current = vapi;

      vapi.on("call-start", () => setStatus("live"));

      vapi.on("call-end", () => {
        setStatus("ended");
        setIsSpeaking(false);
        saveTranscript();
      });

      vapi.on("speech-start", () => setIsSpeaking(true));
      vapi.on("speech-end", () => setIsSpeaking(false));

      vapi.on("message", (msg: Record<string, unknown>) => {
        if (msg.type === "transcript" && msg.transcriptType === "final") {
          appendMessage(msg.role as string, msg.transcript as string);
        }
      });

      vapi.on("error", (err: Record<string, unknown>) => {
        console.error("Vapi error:", err);
        let msg = "An unknown error occurred";
        if (typeof err?.message === "string") {
          msg = err.message;
        } else if (typeof (err?.error as Record<string, unknown>)?.message === "string") {
          msg = (err.error as Record<string, unknown>).message as string;
        } else {
          msg = JSON.stringify(err);
        }
        setError(msg);
        setStatus("error");
      });

      setTranscript([]);
      await vapi.start(config.assistantConfig);
    } catch (err) {
      console.error("Failed to start voice call:", err);
      setError(
        err instanceof Error ? err.message : "Failed to start voice session"
      );
      setStatus("error");
    }
  }, [fetchConfig, appendMessage, saveTranscript]);

  const endCall = useCallback(() => {
    vapiRef.current?.stop();
  }, []);

  const toggleMute = useCallback(() => {
    if (!vapiRef.current) return;
    const next = !isMuted;
    vapiRef.current.setMuted(next);
    setIsMuted(next);
  }, [isMuted]);

  const restart = useCallback(() => {
    setStatus("idle");
    setTranscript([]);
    setError(null);
    setIsMuted(false);
    setIsSpeaking(false);
  }, []);

  return (
    <div className="sticky top-24">
      <div className="bg-surface-container-low rounded-[2rem] overflow-hidden flex flex-col h-[680px] border border-surface-container-high relative">
        {/* Header */}
        <div className="p-6 flex items-center justify-between bg-white/40 backdrop-blur-sm border-b border-surface-container-high/50">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${
                status === "live"
                  ? "bg-emerald-500 animate-pulse"
                  : status === "loading"
                    ? "bg-amber-400 animate-pulse"
                    : status === "error"
                      ? "bg-red-500"
                      : "bg-slate-300"
              }`}
            />
            <h3 className="font-bold text-on-surface tracking-tight">
              {status === "live"
                ? "Assistant Live"
                : status === "loading"
                  ? "Connecting..."
                  : status === "ended"
                    ? "Session Ended"
                    : status === "error"
                      ? "Error"
                      : "Voice Assistant"}
            </h3>
          </div>
          {status === "live" && (
            <div className="flex items-center gap-2">
              <button
                onClick={toggleMute}
                className="w-10 h-10 rounded-full bg-white/80 flex items-center justify-center text-on-surface-variant hover:bg-white transition-colors"
                title={isMuted ? "Unmute" : "Mute"}
              >
                <span className="material-symbols-outlined text-xl">
                  {isMuted ? "mic_off" : "mic"}
                </span>
              </button>
              <button
                onClick={endCall}
                className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 hover:bg-red-200 transition-colors"
                title="End session"
              >
                <span className="material-symbols-outlined text-xl">
                  call_end
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Idle state */}
        {status === "idle" && (
          <div className="flex-grow flex flex-col items-center justify-center gap-6 p-8">
            <div className="w-24 h-24 bg-emerald-50 rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-4xl text-emerald-600 fill-icon">
                mic
              </span>
            </div>
            <div className="text-center space-y-2">
              <h4 className="text-lg font-bold text-on-surface">
                Voice Assessment
              </h4>
              <p className="text-sm text-on-surface-variant max-w-xs">
                Start a voice conversation with our AI advisor. They'll ask you
                questions to help find the best green financing options.
              </p>
            </div>
            <button
              onClick={startCall}
              className="px-8 py-4 bg-primary-gradient text-on-primary rounded-full font-bold text-base shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3"
            >
              <span className="material-symbols-outlined fill-icon">mic</span>
              Start Assessment
            </button>
          </div>
        )}

        {/* Loading state */}
        {status === "loading" && (
          <div className="flex-grow flex flex-col items-center justify-center gap-6 p-8">
            <div className="relative">
              <div className="absolute inset-0 scale-150 rounded-full border border-amber-200 animate-ping opacity-20" />
              <div className="w-20 h-20 bg-amber-50 rounded-full flex items-center justify-center">
                <span className="material-symbols-outlined text-3xl text-amber-600 animate-pulse">
                  phone_in_talk
                </span>
              </div>
            </div>
            <p className="text-sm font-bold text-amber-700 uppercase tracking-widest">
              Connecting...
            </p>
          </div>
        )}

        {/* Live / Ended state */}
        {(status === "live" || status === "ended") && (
          <>
            {/* Speaking indicator */}
            {status === "live" && isSpeaking && (
              <div className="px-6 py-4 flex items-center justify-center gap-3 bg-emerald-50/50">
                <div className="flex gap-1">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-1 bg-emerald-500 rounded-full animate-pulse"
                      style={{
                        height: `${12 + Math.random() * 16}px`,
                        animationDelay: `${i * 0.15}s`,
                      }}
                    />
                  ))}
                </div>
                <p className="text-xs font-bold text-emerald-700 uppercase tracking-widest">
                  Advisor speaking...
                </p>
              </div>
            )}

            {/* Transcript */}
            <div
              ref={scrollRef}
              className="flex-grow p-6 overflow-y-auto space-y-4 flex flex-col"
            >
              {transcript.length === 0 && status === "live" && (
                <p className="text-sm text-on-surface-variant text-center italic mt-8">
                  Waiting for conversation to begin...
                </p>
              )}
              {transcript.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 max-w-[90%] ${
                    msg.role === "user" ? "self-end flex-row-reverse" : ""
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold ${
                      msg.role === "assistant"
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      "GQ"
                    ) : (
                      <span className="material-symbols-outlined text-sm">
                        person
                      </span>
                    )}
                  </div>
                  <div
                    className={`rounded-2xl p-4 shadow-sm ${
                      msg.role === "assistant"
                        ? "bg-white rounded-tl-none border border-emerald-50/50"
                        : "bg-primary text-on-primary rounded-tr-none"
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Ended overlay */}
            {status === "ended" && transcript.length > 0 && (
              <div className="p-6 bg-white/60 border-t border-surface-container-high/50 flex flex-col items-center gap-3">
                {extracting ? (
                  <>
                    <span className="material-symbols-outlined text-3xl text-amber-500 animate-spin">
                      progress_activity
                    </span>
                    <p className="text-sm font-bold text-on-surface">
                      Extracting information from conversation...
                    </p>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-3xl text-emerald-600 fill-icon">
                      check_circle
                    </span>
                    <p className="text-sm font-bold text-on-surface">
                      Session Complete — Data Extracted
                    </p>
                    <button
                      onClick={restart}
                      className="px-6 py-3 bg-primary text-on-primary rounded-full font-bold text-sm hover:scale-105 active:scale-95 transition-all"
                    >
                      Start New Session
                    </button>
                  </>
                )}
              </div>
            )}
          </>
        )}

        {/* Error state */}
        {status === "error" && (
          <div className="flex-grow flex flex-col items-center justify-center gap-6 p-8">
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-3xl text-red-500">
                error
              </span>
            </div>
            <div className="text-center space-y-2">
              <p className="text-sm font-bold text-red-700">
                Something went wrong
              </p>
              <p className="text-xs text-red-500 max-w-xs">{error}</p>
            </div>
            <button
              onClick={restart}
              className="px-6 py-3 bg-primary text-on-primary rounded-full font-bold text-sm hover:scale-105 active:scale-95 transition-all"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center justify-center gap-4 opacity-40">
        <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Powering Sustainable Growth
        </p>
      </div>
    </div>
  );
}
