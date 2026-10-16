import React from 'react';
import { Info, CheckCircle2, ShieldAlert, Cpu, ArrowRight, BookOpen, Layers } from 'lucide-react';

export const SystemInfo: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-900/40">
        <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider block mb-1">
          Final-Year Major Project Implementation
        </span>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">
          AI-Based Wi-Fi Coverage Optimization and Dead-Zone Prediction System
        </h2>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          A software-only virtual platform demonstrating physics-based radio propagation simulation, spatial clustering dead-zone detection, Random Forest dead-zone prediction, and algorithmic access point placement verification.
        </p>
      </div>

      {/* Primary Novelty Box */}
      <div className="p-5 rounded-2xl bg-rose-950/20 border border-rose-900/50 space-y-2">
        <h3 className="text-sm font-bold text-rose-300 uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Core Novelty &amp; Research Focus</span>
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          The main focus of this system is <strong>AI-BASED WI-FI DEAD-ZONE DETECTION AND DEAD-ZONE PREDICTION</strong>. Rather than functioning as a generic monitoring dashboard, every subsystem is engineered around understanding why dead zones form, predicting potential dead zones in unmeasured locations, and optimizing access point coordinates to achieve verifiable dead-zone reduction.
        </p>
      </div>

      {/* Central Workflow Pipeline */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>Central System Workflow</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase">Step 1</span>
            <h4 className="font-bold text-white">DETECT</h4>
            <p className="text-slate-400 text-[11px]">
              DBSCAN spatial clustering groups poor-quality measurements into physical dead-zone polygons.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-amber-400 uppercase">Step 2</span>
            <h4 className="font-bold text-white">UNDERSTAND</h4>
            <p className="text-slate-400 text-[11px]">
              Multi-metric severity scoring diagnoses concrete wall attenuation and excessive RF distance drop-off.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-purple-400 uppercase">Step 3</span>
            <h4 className="font-bold text-white">PREDICT</h4>
            <p className="text-slate-400 text-[11px]">
              Random Forest classifier extrapolates risk across unmeasured coordinates over the entire floorplan.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-cyan-400 uppercase">Step 4</span>
            <h4 className="font-bold text-white">OPTIMIZE</h4>
            <p className="text-slate-400 text-[11px]">
              Candidate AP locations are simulated and ranked to maximize dead-zone area relief.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-emerald-400 uppercase">Step 5</span>
            <h4 className="font-bold text-white">VERIFY</h4>
            <p className="text-slate-400 text-[11px]">
              Comparative simulation evaluates Before vs After dead-zone count and area reduction.
            </p>
          </div>
        </div>
      </div>

      {/* Academic Disclaimer */}
      <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-900/40 space-y-2">
        <h3 className="text-sm font-bold text-amber-300 uppercase tracking-wider flex items-center gap-2">
          <Info className="w-4 h-4 text-amber-400" />
          <span>Academic &amp; Software-Only Disclaimer</span>
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed italic">
          "This prototype uses a software-based Wi-Fi environment simulation to demonstrate automated dead-zone detection, machine-learning-based dead-zone prediction and AP placement optimization. Real-world deployment would require actual Wi-Fi measurements and RF/environmental calibration."
        </p>
      </div>

      {/* Viva Demonstration Flow Checklist */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>Project Viva Demonstration Walkthrough</span>
        </h3>

        <div className="space-y-2 text-xs text-slate-300">
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">1.</span>
            <span>Click <strong>"Generate Demo Environment"</strong> in the top header.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">2.</span>
            <span>Observe the <strong>Dashboard</strong> answering Where, Why, Could, and How.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">3.</span>
            <span>Open <strong>Dead-Zone Analysis</strong> to inspect concrete wall attenuation root causes.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">4.</span>
            <span>Open <strong>Dead-Zone Prediction</strong> to see ML-predicted unmeasured grid risks.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">5.</span>
            <span>Open <strong>AP Optimization</strong> to review recommended placement coordinates.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-indigo-400">6.</span>
            <span>Click <strong>"Run Before vs After Verification"</strong> to prove quantitative Dead-Zone Area &amp; Count Reduction!</span>
          </div>
        </div>
      </div>
    </div>
  );
};
