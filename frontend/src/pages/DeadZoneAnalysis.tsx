import React, { useState } from 'react';
import {
  AlertTriangle,
  Layers,
  Percent,
  Clock,
  WifiOff,
  Signal,
  Gauge,
  CheckCircle,
  HelpCircle,
  TrendingDown,
  ShieldAlert,
} from 'lucide-react';
import { DeadZone, DeadZoneAnalyticsSummary, Floor } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { StatCard } from '../components/StatCard';
import { FloorplanMap } from '../components/FloorplanMap';

interface DeadZoneAnalysisProps {
  analytics: DeadZoneAnalyticsSummary | null;
  floor: Floor | null;
  selectedDeadZone: DeadZone | null;
  onSelectDeadZone: (dz: DeadZone) => void;
}

export const DeadZoneAnalysis: React.FC<DeadZoneAnalysisProps> = ({
  analytics,
  floor,
  selectedDeadZone,
  onSelectDeadZone,
}) => {
  const [activeTab, setActiveTab] = useState<'inspector' | 'map'>('inspector');

  const deadZones = analytics?.dead_zones || [];
  const currentDZ = selectedDeadZone || deadZones[0] || null;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border border-rose-900/40">
        <div>
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs uppercase tracking-wider mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Primary Novelty Core</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">
            Comprehensive Dead-Zone Detection &amp; Root-Cause Analysis
          </h2>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Spatial clustering (DBSCAN) aggregates spatially degraded telemetry points into coherent dead-zone regions. Multi-parameter scoring diagnoses concrete structural attenuation and RF distance drop-off.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-right">
            <span className="text-[10px] uppercase font-bold text-slate-500">Total Impaired Area</span>
            <p className="text-lg font-bold text-rose-400">{analytics?.total_dead_zone_area || 0} m²</p>
          </div>
          <div className="px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-right">
            <span className="text-[10px] uppercase font-bold text-slate-500">Campus Impairment</span>
            <p className="text-lg font-bold text-amber-400">{analytics?.percentage_affected || 0}%</p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="Total Dead Zones"
          value={analytics?.total_dead_zones ?? 0}
          unit="clusters"
          subtitle="Spatially grouped regions"
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Critical / High Severity"
          value={analytics?.critical_count ?? 0}
          unit="zones"
          subtitle="Severe packet & latency stalls"
          icon={ShieldAlert}
          variant="warning"
        />
        <StatCard
          title="Persistent Dead Zones"
          value={analytics?.persistent_count ?? 0}
          unit="recurring"
          subtitle="Confirmed across repeated runs"
          icon={Clock}
          variant="purple"
        />
        <StatCard
          title="Affected Building Ratio"
          value={analytics?.percentage_affected ?? 0}
          unit="%"
          subtitle="Of total floorplan square footage"
          icon={Percent}
          variant="default"
        />
      </div>

      {/* Main Analysis Section: List vs Deep-Dive Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Dead Zone Cards List (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Identified Dead Zones ({deadZones.length})
            </h3>
            <span className="text-xs text-slate-400">Click to inspect</span>
          </div>

          <div className="space-y-3">
            {deadZones.map((dz) => {
              const isSelected = currentDZ?.id === dz.id;
              return (
                <div
                  key={dz.id}
                  onClick={() => onSelectDeadZone(dz)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer shadow-md ${
                    isSelected
                      ? 'bg-rose-950/20 border-rose-500 shadow-rose-900/20'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        {dz.name}
                        {dz.is_persistent && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                            Persistent ({Math.round(dz.persistence_score * 100)}%)
                          </span>
                        )}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Center: ({dz.center_x}m, {dz.center_y}m) • Core Area: <span className="font-semibold text-slate-300">{dz.affected_area} m²</span>
                      </p>
                    </div>
                    <SeverityBadge severity={dz.severity} />
                  </div>

                  {/* Telemetry pill grid */}
                  <div className="grid grid-cols-4 gap-1.5 p-2 rounded-lg bg-slate-950/70 text-[11px] text-slate-400 mb-2">
                    <div>
                      RSSI: <span className="text-rose-400 font-bold block">{dz.avg_rssi} dBm</span>
                    </div>
                    <div>
                      Latency: <span className="text-slate-200 font-bold block">{dz.avg_latency} ms</span>
                    </div>
                    <div>
                      Loss: <span className="text-amber-400 font-bold block">{dz.avg_packet_loss}%</span>
                    </div>
                    <div>
                      Tput: <span className="text-emerald-400 font-bold block">{dz.avg_throughput} Mb</span>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 line-clamp-1">
                    <span className="font-semibold text-slate-300">Root Cause: </span>
                    {dz.contributing_factors[0]}
                  </div>
                </div>
              );
            })}

            {deadZones.length === 0 && (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-400">
                No dead zones detected for this scenario.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Deep-Dive Diagnostic Inspector & Map View (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {currentDZ ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-base font-bold text-white">{currentDZ.name}</h3>
                    <SeverityBadge severity={currentDZ.severity} />
                  </div>
                  <p className="text-xs text-slate-400">
                    Spatial Polygon Coordinates: {currentDZ.polygon_points.length} vertices enclosing {currentDZ.affected_area} m²
                  </p>
                </div>

                <div className="flex items-center space-x-1 bg-slate-800 p-1 rounded-lg text-xs">
                  <button
                    onClick={() => setActiveTab('inspector')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all ${
                      activeTab === 'inspector' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Diagnostics
                  </button>
                  <button
                    onClick={() => setActiveTab('map')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all ${
                      activeTab === 'map' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Floorplan
                  </button>
                </div>
              </div>

              {activeTab === 'inspector' ? (
                <div className="space-y-5">
                  {/* Measured Network Telemetry */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                      Measured Performance Telemetry
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Average RSSI</span>
                        <p className="text-lg font-bold text-rose-400">{currentDZ.avg_rssi} dBm</p>
                        <span className="text-[10px] text-slate-400">Target: &gt; -75 dBm</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Average Latency</span>
                        <p className="text-lg font-bold text-amber-400">{currentDZ.avg_latency} ms</p>
                        <span className="text-[10px] text-slate-400">Target: &lt; 50 ms</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Packet Drop Rate</span>
                        <p className="text-lg font-bold text-rose-400">{currentDZ.avg_packet_loss}%</p>
                        <span className="text-[10px] text-slate-400">Target: &lt; 2.0%</span>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Throughput</span>
                        <p className="text-lg font-bold text-emerald-400">{currentDZ.avg_throughput} Mbps</p>
                        <span className="text-[10px] text-slate-400">Target: &gt; 50 Mbps</span>
                      </div>
                    </div>
                  </div>

                  {/* Why are they occurring? Contributing Factors */}
                  <div>
                    <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4" />
                      <span>Why is this area a dead zone? (Contributing Factors)</span>
                    </h4>
                    <div className="space-y-2">
                      {currentDZ.contributing_factors.map((factor, idx) => (
                        <div
                          key={idx}
                          className="flex items-start space-x-2.5 p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200"
                        >
                          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                          <span>{factor}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Persistence Evaluation */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                        Persistence Across Runs
                      </span>
                      <span className="text-xs font-semibold text-purple-400">
                        Score: {Math.round(currentDZ.persistence_score * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mb-2">
                      <div
                        className="bg-purple-500 h-full rounded-full transition-all"
                        style={{ width: `${Math.round(currentDZ.persistence_score * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-400">
                      {currentDZ.is_persistent
                        ? 'Identified as a recurring dead zone across repeated simulation runs. Structural remediation strongly advised.'
                        : 'Single-run observation. Continuous measurement recommended to confirm persistence score.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div>
                  {floor && (
                    <FloorplanMap
                      rooms={floor.rooms}
                      walls={floor.walls}
                      accessPoints={floor.access_points}
                      deadZones={[currentDZ]}
                      selectedDeadZoneId={currentDZ.id}
                      showControls={false}
                    />
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-400">
              Select a dead zone to view deep-dive diagnostic details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
