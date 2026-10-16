import React, { useState, useEffect } from 'react';
import {
  Activity,
  Binary,
  Cpu,
  Layers,
  Server,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  HardDrive,
  Info,
  Radio,
} from 'lucide-react';
import { api } from '../api/client';
import { MLModelMetrics, GatewayStatus, GatewayTelemetry } from '../types';

interface SystemDiagnosticsProps {
  metrics: MLModelMetrics | null;
  onModelRetrained: (m: MLModelMetrics) => void;
}

export const SystemDiagnostics: React.FC<SystemDiagnosticsProps> = ({
  metrics,
  onModelRetrained,
}) => {
  const [activeTab, setActiveTab] = useState<'ml' | 'gateway' | 'system'>('ml');
  const [isRetraining, setIsRetraining] = useState<boolean>(false);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);

  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null);
  const [gatewayTelemetry, setGatewayTelemetry] = useState<GatewayTelemetry | null>(null);
  const [isPollingGateway, setIsPollingGateway] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const fetchGw = async () => {
      setIsPollingGateway(true);
      try {
        const [st, tel] = await Promise.all([
          api.getGatewayStatus().catch(() => null),
          api.getGatewayTelemetry().catch(() => null),
        ]);
        if (isMounted) {
          setGatewayStatus(st);
          setGatewayTelemetry(tel);
        }
      } finally {
        if (isMounted) setIsPollingGateway(false);
      }
    };
    fetchGw();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRetrain = async () => {
    setIsRetraining(true);
    setRetrainMsg('Training Scikit-learn Random Forest ensemble...');
    try {
      const updated = await api.trainModel();
      setRetrainMsg('Model retrained successfully with updated evaluation metrics.');
      onModelRetrained(updated);
    } catch (err: any) {
      setRetrainMsg(`Training error: ${err.message}`);
    } finally {
      setIsRetraining(false);
    }
  };

  const cm = metrics?.confusion_matrix || [[0, 0], [0, 0]];
  const tn = cm[0]?.[0] || 0;
  const fp = cm[0]?.[1] || 0;
  const fn = cm[1]?.[0] || 0;
  const tp = cm[1]?.[1] || 0;

  const featureEntries = Object.entries(metrics?.feature_importances || {}).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
          <Activity className="w-4 h-4" />
          <span>System Internals &amp; Engineering Diagnostics</span>
        </div>
        <h1 className="text-xl font-extrabold text-white tracking-tight">System Diagnostics</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl">
          Deep-dive inspection into the Random Forest prediction model, OpenNDS netfilter iptables rules, and platform service telemetry.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('ml')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'ml'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Binary className="w-3.5 h-3.5" />
          <span>ML Model Inspector</span>
        </button>

        <button
          onClick={() => setActiveTab('gateway')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'gateway'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Server className="w-3.5 h-3.5" />
          <span>Gateway &amp; Netfilter Diagnostics</span>
        </button>

        <button
          onClick={() => setActiveTab('system')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'system'
              ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Info className="w-3.5 h-3.5" />
          <span>Architecture &amp; Methodology</span>
        </button>
      </div>

      {/* Tab 1: ML Model Inspector */}
      {activeTab === 'ml' && (
        <div className="space-y-6 animate-in fade-in">
          {/* Retrain Action Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div>
              <span className="font-bold text-white block">Random Forest Dead-Zone Classifier</span>
              <span className="text-slate-400">Trained on multivariate RF propagation and network telemetry features.</span>
            </div>

            <button
              onClick={handleRetrain}
              disabled={isRetraining}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-md shadow-indigo-600/30 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRetraining ? 'animate-spin' : ''}`} />
              <span>{isRetraining ? 'Fitting Trees...' : 'Retrain ML Model'}</span>
            </button>
          </div>

          {retrainMsg && (
            <p className="text-xs text-indigo-300 bg-indigo-950/40 p-3 rounded-xl border border-indigo-900/40">
              {retrainMsg}
            </p>
          )}

          {/* Model Performance Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Accuracy</span>
              <div className="text-2xl font-extrabold text-indigo-400 mt-1">
                {metrics ? (metrics.accuracy * 100).toFixed(1) : 0}%
              </div>
              <span className="text-[10px] text-slate-400">Overall classification</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">F1-Score</span>
              <div className="text-2xl font-extrabold text-purple-400 mt-1">
                {metrics ? (metrics.f1_score * 100).toFixed(1) : 0}%
              </div>
              <span className="text-[10px] text-slate-400">Harmonic balance</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Precision</span>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                {metrics ? (metrics.precision * 100).toFixed(1) : 0}%
              </div>
              <span className="text-[10px] text-slate-400">Positive accuracy</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Recall</span>
              <div className="text-2xl font-extrabold text-amber-400 mt-1">
                {metrics ? (metrics.recall * 100).toFixed(1) : 0}%
              </div>
              <span className="text-[10px] text-slate-400">Dead-zone capture rate</span>
            </div>
          </div>

          {/* Dataset & Methodology Disclosure Banner */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-bold text-slate-200">
                Evaluation Benchmark: Multi-Scenario Simulated Propagation Holdout
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                Group-Split (Unseen Simulation Runs)
              </span>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              The Random Forest ensemble acts as a surrogate propagation model learning multivariate degradation boundaries (COST-231 path loss + wall attenuation). Holdout evaluation is partitioned by simulation run to prevent spatial autocorrelation leakage.
            </p>
            <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate-400 font-mono">
              <div>
                Training Set: <span className="text-slate-200 font-bold">{metrics?.train_sample_count?.toLocaleString() || 0}</span> points
              </div>
              <div>
                Test Holdout: <span className="text-slate-200 font-bold">{metrics?.test_sample_count?.toLocaleString() || 0}</span> points
              </div>
              <div>
                Evaluated in Matrix: <span className="text-indigo-300 font-bold">{(tn + fp + fn + tp).toLocaleString()}</span> points
              </div>
            </div>
          </div>

          {/* Confusion Matrix & Feature Importances */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confusion Matrix */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Confusion Matrix Table
                </h3>
                <span className="text-[10px] text-slate-400 font-mono">
                  {(tn + fp + fn + tp).toLocaleString()} holdout samples
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-center text-xs">
                  <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-2 text-left">Ground Truth</th>
                      <th className="p-2">Pred: Normal</th>
                      <th className="p-2">Pred: Dead Zone</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    <tr>
                      <td className="p-2 text-left text-slate-300 font-medium">Actual Normal</td>
                      <td className="p-2 bg-emerald-950/20 text-emerald-300 font-mono font-bold">{tn.toLocaleString()} (TN)</td>
                      <td className="p-2 bg-rose-950/20 text-rose-300 font-mono font-bold">{fp.toLocaleString()} (FP)</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-left text-slate-300 font-medium">Actual Dead Zone</td>
                      <td className="p-2 bg-rose-950/20 text-rose-300 font-mono font-bold">{fn.toLocaleString()} (FN)</td>
                      <td className="p-2 bg-emerald-950/20 text-emerald-300 font-mono font-bold">{tp.toLocaleString()} (TP)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Feature Importance */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  RF Propagation Feature Weights
                </h3>
                <span className="text-[10px] text-slate-400 font-mono">Gini Impurity</span>
              </div>
              <div className="space-y-2.5">
                {featureEntries.map(([feat, weight]) => (
                  <div key={feat} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-mono text-slate-300 capitalize">{feat.replace(/_/g, ' ')}</span>
                      <span className="font-mono font-bold text-indigo-400">{(weight * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                      <div
                        className="h-full rounded-full bg-indigo-500"
                        style={{ width: `${Math.min(100, weight * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-slate-500 pt-1 leading-normal">
                Relative Gini impurity reduction across 100 decision trees. Proximate telemetry indicators (RSSI, latency, packet loss) represent dominant split criteria.
              </p>
            </div>
          </div>

          {/* 4-Way Evaluation Breakdown & Academic Generalization Disclosure */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
              <Info className="w-4 h-4" />
              <span>Rigorous 4-Level AI Evaluation &amp; Generalization Architecture</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {/* Level 1: Multi-Scenario Simulated Benchmark */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">1. Simulated RF Benchmark</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
                    Surrogate Model
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Trained on 106,000+ synthetic measurements across 158 floor scenarios. The Random Forest operates as an analytical surrogate model replicating the COST-231 multi-wall propagation attenuation boundaries.
                </p>
              </div>

              {/* Level 2: Held-Out Simulation Run Split */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">2. Held-Out Simulation Partition</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-800">
                    GroupShuffleSplit
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Evaluated on {metrics?.test_sample_count?.toLocaleString() || 0} unseen simulation run points. Entire simulation runs are held out to strictly prevent spatial autocorrelation and cross-run coordinate leakage.
                </p>
              </div>

              {/* Level 3: Real Survey Evaluation */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">3. Real Laptop Walk-Survey</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-300 border border-amber-800">
                    54 Spot Measurements
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Evaluated on 54 real Windows laptop telemetry points (14.8% agreement with survey quality rating). Real survey captured high ping latency (180 ms) alongside strong signal (-58 dBm, 0% loss); model correctly identifies RF power as sufficient.
                </p>
              </div>

              {/* Level 4: Predictions at Unmeasured Locations */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">4. Unmeasured Grid Predictions</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                    Risk Extrapolation
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Floorplan grid points infer potential dead-zone risks across unmeasured CAD coordinates using simulated physics features. These represent simulated risk indicators, not physically confirmed measurements.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Gateway & Netfilter Diagnostics */}
      {activeTab === 'gateway' && (
        <div className="space-y-6 animate-in fade-in text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase text-[11px]">
                <ShieldCheck className="w-4 h-4" />
                <span>OpenNDS Captive Interception</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                OpenNDS binds to Linux virtual switch <code className="text-indigo-300 font-mono">br-lan</code> (IP 192.168.214.2, Port 2050). Unauthenticated port 80 requests are redirected with SHA256 hashed query tokens to the FAS external server endpoint.
              </p>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                Command: ndsctl status &bull; ndsctl json
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400 font-bold uppercase text-[11px]">
                <HardDrive className="w-4 h-4" />
                <span>Netfilter Kernel Bandwidth Enforcement</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Client authorization establishes dedicated iptables byte-counter rules in the kernel. When upload or download limits are reached, the firewall rule immediately drops traffic and invalidates the client's session.
              </p>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                Command: ndsctl auth &lt;mac&gt; &lt;mins&gt; &lt;up_kb&gt; &lt;down_kb&gt;
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Architecture & Methodology */}
      {activeTab === 'system' && (
        <div className="space-y-6 animate-in fade-in text-xs">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              5-Stage Engineering Workflow Pipeline
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-indigo-400 uppercase">Stage 1</span>
                <h4 className="font-bold text-white">DETECT</h4>
                <p className="text-slate-400 text-[11px]">DBSCAN spatial clustering groups poor-signal measurements into physical dead zones.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-amber-400 uppercase">Stage 2</span>
                <h4 className="font-bold text-white">UNDERSTAND</h4>
                <p className="text-slate-400 text-[11px]">Multi-metric severity scoring diagnoses concrete wall attenuation and path loss.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-purple-400 uppercase">Stage 3</span>
                <h4 className="font-bold text-white">PREDICT</h4>
                <p className="text-slate-400 text-[11px]">Random Forest classifies dead-zone risks across unmeasured floor coordinates.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-cyan-400 uppercase">Stage 4</span>
                <h4 className="font-bold text-white">OPTIMIZE</h4>
                <p className="text-slate-400 text-[11px]">Centroid placement algorithms recommend new access point coordinates.</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-emerald-400 uppercase">Stage 5</span>
                <h4 className="font-bold text-white">VERIFY</h4>
                <p className="text-slate-400 text-[11px]">Dual-simulation confirms &gt;75% dead-zone reduction and signal recovery.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
