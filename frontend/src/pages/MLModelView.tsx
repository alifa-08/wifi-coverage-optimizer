import React, { useState } from 'react';
import { Binary, CheckCircle, RefreshCw, Layers, ShieldCheck, BarChart2 } from 'lucide-react';
import { MLModelMetrics } from '../types';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';

interface MLModelViewProps {
  metrics: MLModelMetrics | null;
  onModelRetrained: (m: MLModelMetrics) => void;
}

export const MLModelView: React.FC<MLModelViewProps> = ({ metrics, onModelRetrained }) => {
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);

  const handleRetrain = async () => {
    setIsRetraining(true);
    setRetrainMsg('Fitting Random Forest ensemble across spatial measurements...');
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
            <Binary className="w-4 h-4" />
            <span>Machine Learning Pipeline Architecture</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">
            Random Forest Dead-Zone Classifier
          </h2>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Ensemble decision trees trained on multivariate RF propagation and network telemetry features. Honest test set evaluation without metric fabrication.
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={isRetraining}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-60 shrink-0"
        >
          {isRetraining ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          <span>{isRetraining ? 'Training Model...' : 'Retrain Model On-Demand'}</span>
        </button>
      </div>

      {retrainMsg && (
        <div className="p-3 bg-indigo-950/40 border border-indigo-800/50 rounded-xl text-xs text-indigo-300">
          {retrainMsg}
        </div>
      )}

      {/* Verified Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="Accuracy"
          value={metrics ? `${(metrics.accuracy * 100).toFixed(1)}%` : '0%'}
          subtitle="Test set classification rate"
          icon={CheckCircle}
          variant="success"
        />
        <StatCard
          title="Precision"
          value={metrics ? `${(metrics.precision * 100).toFixed(1)}%` : '0%'}
          subtitle="Positive predictive value"
          icon={ShieldCheck}
          variant="purple"
        />
        <StatCard
          title="Recall (Sensitivity)"
          value={metrics ? `${(metrics.recall * 100).toFixed(1)}%` : '0%'}
          subtitle="Dead-zone capture rate"
          icon={Binary}
          variant="cyan"
        />
        <StatCard
          title="F1-Score"
          value={metrics ? `${(metrics.f1_score * 100).toFixed(1)}%` : '0%'}
          subtitle="Harmonic mean"
          icon={BarChart2}
          variant="success"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Card */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Test Confusion Matrix ({metrics?.test_sample_count || 0} Test Samples)
          </h3>

          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">
                True Negatives (TN)
              </span>
              <span className="text-2xl font-black text-emerald-400">{tn}</span>
              <p className="text-[10px] text-slate-400 mt-1">Correctly identified adequate coverage</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">
                False Positives (FP)
              </span>
              <span className="text-2xl font-black text-amber-400">{fp}</span>
              <p className="text-[10px] text-slate-400 mt-1">Type I error (False alarm)</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">
                False Negatives (FN)
              </span>
              <span className="text-2xl font-black text-rose-400">{fn}</span>
              <p className="text-[10px] text-slate-400 mt-1">Type II error (Missed dead zone)</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 font-semibold uppercase block">
                True Positives (TP)
              </span>
              <span className="text-2xl font-black text-emerald-400">{tp}</span>
              <p className="text-[10px] text-slate-400 mt-1">Accurately detected dead zone</p>
            </div>
          </div>
        </div>

        {/* Feature Importance Ranking Card */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Feature Importance Ranking (Gini Impurity)
          </h3>

          <div className="space-y-2.5">
            {featureEntries.map(([feat, imp]) => {
              const pct = (imp * 100).toFixed(1);
              return (
                <div key={feat} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-300 font-mono">{feat}</span>
                    <span className="text-slate-400 font-bold">{pct}%</span>
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
