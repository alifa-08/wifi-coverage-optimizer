import React, { useState } from 'react';
import {
  GitCompare,
  TrendingDown,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { BeforeAfterComparison, Floor } from '../types';
import { FloorplanMap } from '../components/FloorplanMap';
import { StatCard } from '../components/StatCard';

interface BeforeAfterProps {
  comparison: BeforeAfterComparison | null;
  floor: Floor | null;
}

export const BeforeAfter: React.FC<BeforeAfterProps> = ({ comparison, floor }) => {
  const [selectedView, setSelectedView] = useState<'before' | 'after' | 'split'>('split');

  if (!comparison) {
    return (
      <div className="p-12 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-3">
        <GitCompare className="w-10 h-10 text-slate-500 mx-auto" />
        <h3 className="text-base font-bold text-slate-200">No Comparison Data Available</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Please run "Generate Demo Environment" or go to the AP Optimization page and click "Run Before vs After Verification".
        </p>
      </div>
    );
  }

  // Combine floor APs with recommended APs for the "after" visualization
  const optimizedAPs = [
    ...(floor?.access_points || []),
    ...comparison.recommended_aps_added.map((rec) => ({
      id: 9000 + rec.id,
      floor_id: rec.floor_id,
      name: `Optimized AP #${rec.priority}`,
      x: rec.candidate_x,
      y: rec.candidate_y,
      tx_power_dbm: rec.tx_power_dbm,
      frequency_ghz: 2.4,
      channel: 6,
      ssid: 'Campus-Net-Optimized',
      is_active: true,
      is_recommended: true,
    })),
  ];

  return (
    <div className="space-y-6">
      {/* Verification Header */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-900/40">
        <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider mb-1">
          <GitCompare className="w-4 h-4" />
          <span>Verification &amp; Impact Analysis</span>
        </div>
        <h2 className="text-xl font-extrabold text-white tracking-tight">
          Before vs After: Quantitative Dead-Zone Reduction
        </h2>
        <p className="text-xs text-slate-400 max-w-2xl mt-1">
          Evaluating the simulated RF remediation impact. Comparing baseline dead-zone spatial footprints against the optimized AP configuration.
        </p>

        {/* Academic Limitation Banner */}
        <div className="mt-3 flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-300">
          <Info className="w-3.5 h-3.5 shrink-0" />
          <span>
            Simulated Results: Benchmark evaluated using indoor RF multi-wall path loss ray-tracing. No metric is artificially clamped or forced positive.
          </span>
        </div>
      </div>

      {/* Status Alert Banner */}
      {comparison.status === 'WORSENED' ? (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>
            <strong>Regression Detected:</strong> Under this specific AP configuration, coverage worsened or dead-zone footprint expanded. Consider re-evaluating AP candidate coordinates.
          </span>
        </div>
      ) : comparison.status === 'UNCHANGED' || comparison.status === 'ZERO_BASELINE' ? (
        <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700 text-slate-300 text-xs flex items-center space-x-2.5">
          <Info className="w-4 h-4 shrink-0 text-slate-400" />
          <span>
            <strong>Neutral Benchmark:</strong> Dead-zone footprint remained unchanged between the baseline and remediated configurations.
          </span>
        </div>
      ) : (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-2.5">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>
            <strong>Optimization Verified:</strong> Recommended AP deployment successfully mitigated dead zones and recovered weak signal coverage.
          </span>
        </div>
      )}

      {/* Dead-Zone Reduction Hero Showcase Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Dead-Zone Area Reduction Card */}
        <div className={`p-5 rounded-2xl bg-gradient-to-br ${
          comparison.before_dead_zone_area <= 0
            ? comparison.after_dead_zone_area <= 0
              ? 'from-slate-800/30 to-slate-900 border-slate-800'
              : 'from-rose-900/30 to-slate-900 border-rose-800/40'
            : comparison.dead_zone_area_reduction > 0
            ? 'from-emerald-900/30 to-slate-900 border-emerald-800/40'
            : comparison.dead_zone_area_reduction < 0
            ? 'from-rose-900/30 to-slate-900 border-rose-800/40'
            : 'from-slate-800/30 to-slate-900 border-slate-800'
        } border shadow-xl space-y-3`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-bold uppercase tracking-wider ${
              comparison.before_dead_zone_area <= 0
                ? comparison.after_dead_zone_area <= 0
                  ? 'text-slate-400'
                  : 'text-rose-400'
                : comparison.dead_zone_area_reduction > 0
                ? 'text-emerald-400'
                : comparison.dead_zone_area_reduction < 0
                ? 'text-rose-400'
                : 'text-slate-400'
            }`}>
              Dead-Zone Area Reduction
            </span>
            <div className={`flex items-center space-x-1 font-bold text-xs px-2 py-0.5 rounded-full ${
              comparison.before_dead_zone_area <= 0
                ? comparison.after_dead_zone_area <= 0
                  ? 'text-slate-400 bg-slate-700/40'
                  : 'text-rose-400 bg-rose-500/20'
                : comparison.dead_zone_area_reduction > 0
                ? 'text-emerald-400 bg-emerald-500/20'
                : comparison.dead_zone_area_reduction < 0
                ? 'text-rose-400 bg-rose-500/20'
                : 'text-slate-400 bg-slate-700/40'
            }`}>
              {comparison.before_dead_zone_area <= 0 ? (
                comparison.after_dead_zone_area <= 0 ? (
                  <>
                    <Layers className="w-3.5 h-3.5" />
                    <span>N/A (Clean Baseline — 0 m²)</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>Undefined % (Worsened from 0 m²)</span>
                  </>
                )
              ) : comparison.dead_zone_area_reduction > 0 ? (
                <>
                  <TrendingDown className="w-3.5 h-3.5" />
                  <span>-{comparison.dead_zone_area_reduction_pct}% (Improved)</span>
                </>
              ) : comparison.dead_zone_area_reduction < 0 ? (
                <>
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>+{Math.abs(comparison.dead_zone_area_reduction_pct)}% (Worsened)</span>
                </>
              ) : (
                <>
                  <Layers className="w-3.5 h-3.5" />
                  <span>0.0% (Genuine Zero Delta)</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-baseline space-x-3">
            <span className="text-3xl font-extrabold text-white">
              {comparison.dead_zone_area_reduction} m²
            </span>
            <span className="text-xs text-slate-400">
              {comparison.before_dead_zone_area <= 0
                ? comparison.after_dead_zone_area <= 0
                  ? 'Zero dead zones in baseline and remediated states (percentage undefined)'
                  : `${comparison.after_dead_zone_area} m² dead-zone area formed from previously clean baseline`
                : comparison.dead_zone_area_reduction > 0
                ? 'recovered to acceptable coverage'
                : comparison.dead_zone_area_reduction < 0
                ? 'area expanded / worsened'
                : `Baseline area of ${comparison.before_dead_zone_area} m² remained unchanged`}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-semibold">Before (Baseline)</span>
              <p className="font-bold text-rose-400 text-sm">{comparison.before_dead_zone_area} m²</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-semibold">After (Remediated)</span>
              <p className={`font-bold text-sm ${comparison.after_dead_zone_area <= comparison.before_dead_zone_area ? 'text-emerald-400' : 'text-rose-400'}`}>
                {comparison.after_dead_zone_area} m²
              </p>
            </div>
          </div>
        </div>

        {/* Dead-Zone Count Reduction Card */}
        <div className={`p-5 rounded-2xl bg-gradient-to-br ${
          comparison.before_dead_zone_count <= 0
            ? comparison.after_dead_zone_count <= 0
              ? 'from-slate-800/30 to-slate-900 border-slate-800'
              : 'from-rose-900/30 to-slate-900 border-rose-800/40'
            : comparison.dead_zone_count_reduction > 0
            ? 'from-indigo-900/30 to-slate-900 border-indigo-800/40'
            : comparison.dead_zone_count_reduction < 0
            ? 'from-rose-900/30 to-slate-900 border-rose-800/40'
            : 'from-slate-800/30 to-slate-900 border-slate-800'
        } border shadow-xl space-y-3`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-bold uppercase tracking-wider ${
              comparison.before_dead_zone_count <= 0
                ? comparison.after_dead_zone_count <= 0
                  ? 'text-slate-400'
                  : 'text-rose-400'
                : comparison.dead_zone_count_reduction > 0
                ? 'text-indigo-400'
                : comparison.dead_zone_count_reduction < 0
                ? 'text-rose-400'
                : 'text-slate-400'
            }`}>
              Dead-Zone Count Reduction
            </span>
            <div className={`flex items-center space-x-1 font-bold text-xs px-2 py-0.5 rounded-full ${
              comparison.before_dead_zone_count <= 0
                ? comparison.after_dead_zone_count <= 0
                  ? 'text-slate-400 bg-slate-700/40'
                  : 'text-rose-400 bg-rose-500/20'
                : comparison.dead_zone_count_reduction > 0
                ? 'text-indigo-400 bg-indigo-500/20'
                : comparison.dead_zone_count_reduction < 0
                ? 'text-rose-400 bg-rose-500/20'
                : 'text-slate-400 bg-slate-700/40'
            }`}>
              {comparison.before_dead_zone_count <= 0 ? (
                comparison.after_dead_zone_count <= 0 ? (
                  <>
                    <Layers className="w-3.5 h-3.5" />
                    <span>N/A (Clean Baseline — 0 Zones)</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>Undefined % (Formed from 0 Zones)</span>
                  </>
                )
              ) : comparison.dead_zone_count_reduction > 0 ? (
                <>
                  <TrendingDown className="w-3.5 h-3.5" />
                  <span>-{comparison.dead_zone_count_reduction_pct}% (Eliminated)</span>
                </>
              ) : comparison.dead_zone_count_reduction < 0 ? (
                <>
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>+{Math.abs(comparison.dead_zone_count_reduction_pct)}% (Increased)</span>
                </>
              ) : (
                <>
                  <Layers className="w-3.5 h-3.5" />
                  <span>0% (Genuine Zero Delta)</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-baseline space-x-3">
            <span className="text-3xl font-extrabold text-white">
              {comparison.before_dead_zone_count <= 0
                ? comparison.after_dead_zone_count <= 0
                  ? '0 Dead Zones'
                  : `${comparison.dead_zone_count_reduction} Zones`
                : comparison.dead_zone_count_reduction > 0
                ? `${comparison.dead_zone_count_reduction} Dead Zones`
                : comparison.dead_zone_count_reduction < 0
                ? `${Math.abs(comparison.dead_zone_count_reduction)} Zones Added`
                : '0 Dead Zones'}
            </span>
            <span className="text-xs text-slate-400">
              {comparison.before_dead_zone_count <= 0
                ? comparison.after_dead_zone_count <= 0
                  ? 'Zero dead zones in baseline and remediated states (percentage undefined)'
                  : `${comparison.after_dead_zone_count} dead zone(s) formed from previously clean baseline`
                : comparison.dead_zone_count_reduction > 0
                ? 'completely eliminated'
                : comparison.dead_zone_count_reduction < 0
                ? 'additional dead zones formed'
                : `Baseline count of ${comparison.before_dead_zone_count} zones remained unchanged`}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-semibold">Before Count</span>
              <p className="font-bold text-rose-400 text-sm">{comparison.before_dead_zone_count} zones</p>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] uppercase font-semibold">After Count</span>
              <p className={`font-bold text-sm ${comparison.after_dead_zone_count <= comparison.before_dead_zone_count ? 'text-emerald-400' : 'text-rose-400'}`}>
                {comparison.after_dead_zone_count} zones
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Network RF Quality Deltas Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="RSSI Delta"
          value={comparison.rssi_improvement > 0 ? `+${comparison.rssi_improvement}` : `${comparison.rssi_improvement}`}
          unit="dBm"
          subtitle={`Before: ${comparison.before_avg_rssi} ➔ After: ${comparison.after_avg_rssi}`}
          icon={comparison.rssi_improvement >= 0 ? TrendingUp : TrendingDown}
          variant={comparison.rssi_improvement > 0 ? 'success' : comparison.rssi_improvement < 0 ? 'danger' : 'default'}
        />
        <StatCard
          title="Latency Delta"
          value={comparison.latency_reduction > 0 ? `-${comparison.latency_reduction}` : comparison.latency_reduction < 0 ? `+${Math.abs(comparison.latency_reduction)}` : '0.0'}
          unit={comparison.latency_reduction >= 0 ? 'ms drop' : 'ms increase'}
          subtitle={`Before: ${comparison.before_avg_latency} ➔ After: ${comparison.after_avg_latency}`}
          icon={comparison.latency_reduction >= 0 ? TrendingDown : TrendingUp}
          variant={comparison.latency_reduction > 0 ? 'success' : comparison.latency_reduction < 0 ? 'danger' : 'default'}
        />
        <StatCard
          title="Packet Loss Delta"
          value={comparison.packet_loss_reduction > 0 ? `-${comparison.packet_loss_reduction}` : comparison.packet_loss_reduction < 0 ? `+${Math.abs(comparison.packet_loss_reduction)}` : '0.0'}
          unit={comparison.packet_loss_reduction >= 0 ? '% drop' : '% increase'}
          subtitle={`Before: ${comparison.before_avg_packet_loss}% ➔ After: ${comparison.after_avg_packet_loss}%`}
          icon={comparison.packet_loss_reduction >= 0 ? TrendingDown : TrendingUp}
          variant={comparison.packet_loss_reduction > 0 ? 'success' : comparison.packet_loss_reduction < 0 ? 'danger' : 'default'}
        />
        <StatCard
          title="Throughput Delta"
          value={comparison.throughput_improvement > 0 ? `+${comparison.throughput_improvement}` : `${comparison.throughput_improvement}`}
          unit="Mbps"
          subtitle={`Before: ${comparison.before_avg_throughput} ➔ After: ${comparison.after_avg_throughput}`}
          icon={comparison.throughput_improvement >= 0 ? TrendingUp : TrendingDown}
          variant={comparison.throughput_improvement > 0 ? 'success' : comparison.throughput_improvement < 0 ? 'danger' : 'default'}
        />
      </div>

      {/* Visual Floorplan Comparison */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Visual Comparative Floorplan
            </h3>
            <p className="text-xs text-slate-400">
              Observe dead-zone boundary shrinkage and coverage enhancement
            </p>
          </div>

          <div className="flex items-center space-x-1 bg-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setSelectedView('before')}
              className={`px-3 py-1 rounded-md font-semibold transition-all ${
                selectedView === 'before' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              BEFORE
            </button>
            <button
              onClick={() => setSelectedView('after')}
              className={`px-3 py-1 rounded-md font-semibold transition-all ${
                selectedView === 'after' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              AFTER
            </button>
            <button
              onClick={() => setSelectedView('split')}
              className={`px-3 py-1 rounded-md font-semibold transition-all ${
                selectedView === 'split' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              SIDE-BY-SIDE
            </button>
          </div>
        </div>

        {selectedView === 'split' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Before Map */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs px-2 font-bold text-rose-400">
                <span>BEFORE (Baseline with Dead Zones)</span>
                <span>{comparison.before_dead_zone_count} Dead Zones ({comparison.before_dead_zone_area} m²)</span>
              </div>
              {floor && (
                <FloorplanMap
                  rooms={floor.rooms}
                  walls={floor.walls}
                  accessPoints={floor.access_points}
                  deadZones={comparison.before_dead_zones}
                  showControls={false}
                />
              )}
            </div>

            {/* After Map */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs px-2 font-bold text-emerald-400">
                <span>AFTER (Optimized APs Deployed)</span>
                <span>{comparison.after_dead_zone_count} Dead Zones ({comparison.after_dead_zone_area} m²)</span>
              </div>
              {floor && (
                <FloorplanMap
                  rooms={floor.rooms}
                  walls={floor.walls}
                  accessPoints={optimizedAPs}
                  deadZones={comparison.after_dead_zones}
                  showControls={false}
                />
              )}
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-2 text-xs font-bold px-2">
              {selectedView === 'before' ? (
                <span className="text-rose-400">Viewing BEFORE State ({comparison.before_dead_zone_count} Dead Zones)</span>
              ) : (
                <span className="text-emerald-400">Viewing AFTER State ({comparison.after_dead_zone_count} Dead Zones)</span>
              )}
            </div>
            {floor && (
              <FloorplanMap
                rooms={floor.rooms}
                walls={floor.walls}
                accessPoints={selectedView === 'before' ? floor.access_points : optimizedAPs}
                deadZones={selectedView === 'before' ? comparison.before_dead_zones : comparison.after_dead_zones}
                showControls={false}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};
