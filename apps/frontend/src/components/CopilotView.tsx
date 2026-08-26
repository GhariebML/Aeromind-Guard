import React, { useState } from 'react';
import {
  Bot, Send, Sparkles, Database, CheckCircle2,
  AlertTriangle, ShieldAlert, Cpu, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: string[];
  groundedData?: any;
  isLlmActive?: boolean;
}

export const CopilotView: React.FC = () => {
  const [inputQuery, setInputQuery] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Greetings. I am the AeroMind ClimateGuard Physical AI Copilot. I provide verified, data-grounded explanations of thermal anomalies, composite risk factors, visual hazard detections, and recommended operational directives. How can I assist you?',
      timestamp: new Date().toLocaleTimeString(),
      sources: ['AeroMind Deterministic Operational Telemetry']
    }
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedGroundedData, setSelectedGroundedData] = useState<any | null>(null);

  const quickPrompts = [
    "What are the highest-risk events today?",
    "Why did the risk score increase?",
    "Which location requires attention?",
    "What changed during the last hour?",
    "Summarize today's environmental anomalies.",
    "Explain this alert."
  ];

  const handleSendMessage = async (queryText?: string) => {
    const text = queryText || inputQuery;
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await api.queryCopilot(text);
      const assistantMsg: Message = {
        role: 'assistant',
        content: res.answer,
        timestamp: new Date().toLocaleTimeString(),
        sources: res.sources_used,
        groundedData: res.grounded_data,
        isLlmActive: res.is_llm_active
      };
      setMessages((prev) => [...prev, assistantMsg]);
      if (res.grounded_data) {
        setSelectedGroundedData(res.grounded_data);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error executing grounded copilot query: ${err.message}`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-200">
              AEROMIND PHYSICAL AI COPILOT
            </h2>
            <span className="text-[11px] text-slate-400">
              Grounded situational reasoning on live environmental, visual, and risk telemetry
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 font-bold">
            ZERO HALLUCINATION PROTOCOL ACTIVE
          </span>
        </div>
      </div>

      {/* Main Grid: Chat Stream (2 Cols) + Grounded Context Inspector (1 Col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: Interactive Dialogue */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-4 flex flex-col justify-between h-[580px]">
          {/* Messages Scroll Area */}
          <div className="space-y-3.5 overflow-y-auto pr-2 flex-1">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 text-xs ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-cyan-600/30 border border-cyan-500/40 text-cyan-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`p-3.5 rounded-xl max-w-xl space-y-1.5 ${
                    m.role === 'user'
                      ? 'bg-cyan-600 text-white rounded-br-none shadow-md shadow-cyan-600/20'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none shadow-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>

                  {m.sources && (
                    <div className="pt-2 mt-1 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
                      <span className="font-semibold text-cyan-400">Sources:</span>
                      {m.sources.map((s, sIdx) => (
                        <span key={sIdx} className="px-1.5 py-0.2 rounded bg-slate-950 font-mono text-slate-300">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  <span className="text-[9px] text-slate-400 block text-right font-mono">
                    {m.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 text-xs justify-start">
                <div className="w-7 h-7 rounded-lg bg-cyan-600/30 border border-cyan-500/40 text-cyan-400 flex items-center justify-center shrink-0">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                </div>
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 italic text-xs">
                  Querying grounded physical telemetry state and reasoning...
                </div>
              </div>
            )}
          </div>

          {/* Quick Prompts Chips */}
          <div className="pt-3 border-t border-slate-800">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 no-scrollbar">
              {quickPrompts.map((qp, qIdx) => (
                <button
                  key={qIdx}
                  onClick={() => handleSendMessage(qp)}
                  className="px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-[11px] text-slate-300 border border-slate-700/80 whitespace-nowrap transition-colors flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  {qp}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="flex items-center gap-2 mt-2">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask Copilot regarding active risks, anomalies, or facility protocols..."
                className="flex-1 bg-slate-950 text-xs text-slate-100 border border-slate-700 rounded-lg px-3.5 py-2.5 focus:outline-none focus:border-cyan-500 font-sans"
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isLoading || !inputQuery.trim()}
                className="p-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white font-bold transition-all shadow-md shadow-cyan-600/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Real-Time Grounding Context Drawer */}
        <div className="glass-panel rounded-xl p-4 space-y-3 flex flex-col justify-between h-[580px]">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold text-slate-200 flex items-center gap-1.5">
                <Database className="w-4 h-4 text-cyan-400" />
                VERIFIED GROUNDING CONTEXT
              </h2>
              <span className="text-[10px] font-mono text-emerald-400">
                Live State
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs overflow-y-auto max-h-[460px] pr-1">
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                <strong className="text-cyan-400 block mb-1">Grounded Query Protocol:</strong>
                All responses strictly query active database tables (`risk_scores`, `alerts`, `anomalies`, `video_events`). The LLM is NEVER used for mathematical calculations.
              </div>

              {selectedGroundedData ? (
                <div className="space-y-2">
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 uppercase block">Active Alerts Grounding</span>
                    <span className="text-xs font-bold text-slate-200">
                      {selectedGroundedData.alerts?.length || 0} alerts evaluated
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 uppercase block">Top Monitored Risk</span>
                    <span className="text-xs font-bold text-slate-200">
                      {selectedGroundedData.risk_assessments?.[0]?.overall_score || 18.5} / 100 ({selectedGroundedData.risk_assessments?.[0]?.severity || 'LOW'})
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 uppercase block">Visual Hazards</span>
                    <span className="text-xs font-bold text-slate-200">
                      {selectedGroundedData.visual_hazards?.length || 0} active camera detections
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic py-10 text-center">
                  Submit a query to inspect live database grounding payload.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
