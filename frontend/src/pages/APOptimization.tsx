import React from 'react';
import { Cpu, MapPin, CheckCircle, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { APRecommendation, DeadZone, Floor } from '../types';
import { FloorplanMap } from '../components/FloorplanMap';
import { StatCard } from '../components/StatCard';
import { PageId } from '../components/Sidebar';

interface APOptimizationProps {
  recommendations: APRecommendation[];
  deadZones: DeadZone[];
  floor: Floor | null;
  onRunBeforeAfter: () => void;
  isRunningBeforeAfter: boolean;
  onNavigate: (page: PageId) => void;
}

export const APOptimization: React.FC<APOptimizationProps> = ({
  recommendations,
  deadZones,
  floor,
  onRunBeforeAfter,
  isRunningBeforeAfter,
  onNavigate,
}) => {
  const totalAreaRecoverable = recommendations.reduce(
    (sum, r) => sum + r.expected_dead_zone_reduction_area,
    0
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-900 border border-cyan-900/40">
        <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs uppercase tracking-wider mb-1">
          <Cpu className="w-4 h-4" />
          <span>Algorithmic AP Placement Optimization</span>
        </div>
        <h2 className="text-xl font-extrabold text-white tracking-tight">
          Dead-Zone Relief Placement Engine
        </h2>
        <p className="text-xs text-slate-400 max-w-2xl mt-1">
          Computes optimal access point coordinates targeted directly at eliminating high-severity dead-zone cores. Placement simulations calculate expected dead-zone area reduction ($m^2$) and coverage gain before hardware installation.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="Generated AP Candidates"
          value={recommendations.length}
          unit="positions"
          subtitle="Evaluated for dead-zone relief"
          icon={Cpu}
          variant="cyan"
        />
        <StatCard
          title="Estimated Area Relief"
          value={totalAreaRecoverable.toFixed(1)}
          unit="m²"
          subtitle="Recoverable impaired area"
          icon={MapPin}
          variant="success"
        />
        <StatCard
          title="Targeted Dead Zones"
          value={deadZones.length}
          unit="zones"
          subtitle="Currently diagnosed"
          icon={ShieldCheck}
          variant="default"
        />
        <StatCard
          title="Simulation Verification"
          value="Ready"
          subtitle="Before vs After ready to test"
          icon={Zap}
          variant="purple"
        />
      </div>

      {/* Recommendations List and Floorplan Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recommendations Cards (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Recommended AP Deployments ({recommendations.length})
            </h3>
          </div>

          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition-all shadow-md space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold flex items-center justify-center text-xs border border-cyan-500/40">
                      #{rec.priority}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-100">
                        Candidate AP #{rec.priority}
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        Target Coordinates: ({rec.candidate_x}m, {rec.candidate_y}m)
                      </p>
                    </div>
                  </div>

                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                    Priority {rec.priority}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-950/70 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 font-semibold uppercase">Expected Area Gain</span>
                    <p className="text-sm font-bold text-cyan-300">{rec.expected_dead_zone_reduction_area} m²</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-semibold uppercase">Dead Zones Relieved</span>
                    <p className="text-sm font-bold text-emerald-400">~{rec.expected_dead_zone_count_reduction} zones</p>
                  </div>
                </div>

                <p className="text-xs text-slate-300 italic border-l-2 border-cyan-500/50 pl-2 py-0.5">
                  "{rec.reason}"
                </p>
              </div>
            ))}

            {recommendations.length === 0 && (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-400">
                No active recommendations. Click "Generate Demo Environment" or run a simulation.
              </div>
            )}
          </div>

          {/* Action Trigger */}
          {recommendations.length > 0 && (
            <button
              onClick={onRunBeforeAfter}
              disabled={isRunningBeforeAfter}
              className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-900/40 transition-all cursor-pointer disabled:opacity-60"
            >
              <CheckCircle className="w-4 h-4" />
              <span>{isRunningBeforeAfter ? 'Simulating Deployment Impact...' : 'Run Before vs After Verification'}</span>
            </button>
          )}
        </div>

        {/* Floorplan with Candidate Highlights (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Candidate Placement Visualization
            </h3>
            <span className="text-xs text-cyan-400 font-semibold">Cyan circles represent recommended APs</span>
          </div>

          {floor && (
            <FloorplanMap
              rooms={floor.rooms}
              walls={floor.walls}
              accessPoints={floor.access_points}
              deadZones={deadZones}
              recommendations={recommendations}
              showControls={true}
            />
          )}
        </div>
      </div>
    </div>
  );
};
