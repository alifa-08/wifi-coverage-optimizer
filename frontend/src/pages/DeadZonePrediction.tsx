import React, { useState } from 'react';
import { Sparkles, Sliders, ShieldAlert, Cpu, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { PredictionGridPoint, DeadZone, Floor } from '../types';
import { FloorplanMap } from '../components/FloorplanMap';
import { StatCard } from '../components/StatCard';

interface DeadZonePredictionProps {
  predictedGrid: PredictionGridPoint[];
  currentDeadZones: DeadZone[];
  floor: Floor | null;
  onSelectDeadZone: (dz: DeadZone) => void;
}

export const DeadZonePrediction: React.FC<DeadZonePredictionProps> = ({
  predictedGrid,
  currentDeadZones,
  floor,
  onSelectDeadZone,
}) => {
  const [probThreshold, setProbThreshold] = useState<number>(0.5);

  const filteredPredictions = predictedGrid.filter(
    (p) => p.dead_zone_probability >= probThreshold
  );

  const avgProb =
    predictedGrid.length > 0
      ? (
          predictedGrid.reduce((sum, p) => sum + p.dead_zone_probability, 0) /
          predictedGrid.length
        ) * 100
      : 0;

  return (
    <div className="space-y-6">
      {/* Novelty Header */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-900/40">
        <div className="flex items-center space-x-2 text-purple-400 font-bold text-xs uppercase tracking-wider mb-1">
          <Sparkles className="w-4 h-4" />
          <span>Core Novelty Component</span>
        </div>
        <h2 className="text-xl font-extrabold text-white tracking-tight">
          AI-Based Wi-Fi Dead-Zone Prediction Engine
        </h2>
        <p className="text-xs text-slate-400 max-w-2xl mt-1">
          Machine Learning models predict potential weak and dead zones across unmeasured building locations using multivariate RF propagation features (distance, concrete wall factor, AP density, estimated RSSI, and latency).
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="Evaluated Grid Locations"
          value={predictedGrid.length}
          unit="points"
          subtitle="Full floorplan spatial grid"
          icon={Cpu}
          variant="default"
        />
        <StatCard
          title="Predicted Dead-Zone Points"
          value={filteredPredictions.length}
          unit="points"
          subtitle={`Risk threshold ≥ ${(probThreshold * 100).toFixed(0)}%`}
          icon={Sparkles}
          variant="purple"
        />
        <StatCard
          title="Measured Dead-Zone Areas"
          value={currentDeadZones.length}
          unit="zones"
          subtitle="Directly measured baseline"
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Floorplan Risk Index"
          value={avgProb.toFixed(1)}
          unit="%"
          subtitle="Overall floor vulnerability"
          icon={ShieldAlert}
          variant="warning"
        />
      </div>

      {/* Distinction Banner: Measured vs Predicted */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/40 space-y-2">
          <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            <span>Current / Directly Measured Dead Zones</span>
          </div>
          <p className="text-xs text-slate-300">
            Detected from direct telemetry measurements (RSSI &lt; -78 dBm, high latency, dropped packets) within surveyed locations. These represent established physical dead zones.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-900/40 space-y-2">
          <div className="flex items-center space-x-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>AI-Predicted Potential Dead Zones</span>
          </div>
          <p className="text-xs text-slate-300">
            Inferred by the trained Random Forest model for unmeasured coordinates by analyzing spatial distance, wall penetration count, and AP density. Identifies hidden vulnerability spots before user complaints arise.
          </p>
        </div>
      </div>

      {/* Probability Slider & Map */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-bold text-slate-200">
              Confidence / Probability Threshold: {(probThreshold * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center space-x-3 w-full sm:w-72">
            <span className="text-xs text-slate-500 font-semibold">30%</span>
            <input
              type="range"
              min="0.30"
              max="0.90"
              step="0.05"
              value={probThreshold}
              onChange={(e) => setProbThreshold(parseFloat(e.target.value))}
              aria-label="Confidence Probability Threshold"
              className="w-full accent-purple-500 cursor-pointer"
            />
            <span className="text-xs text-slate-500 font-semibold">90%</span>
          </div>
        </div>

        {/* Floorplan with Predicted Layer */}
        {floor && (
          <FloorplanMap
            rooms={floor.rooms}
            walls={floor.walls}
            accessPoints={floor.access_points}
            deadZones={currentDeadZones}
            predictedGrid={filteredPredictions}
            onSelectDeadZone={onSelectDeadZone}
            showControls={true}
          />
        )}
      </div>

      {/* High-Risk Predicted Locations Table */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Top ML-Predicted High-Risk Coordinates
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Coordinates (X, Y)</th>
                <th className="py-2.5 px-3">Dead-Zone Probability</th>
                <th className="py-2.5 px-3">Estimated RSSI</th>
                <th className="py-2.5 px-3">Est. Latency</th>
                <th className="py-2.5 px-3">Est. Loss</th>
                <th className="py-2.5 px-3">Distance to AP</th>
                <th className="py-2.5 px-3">Wall Factor</th>
                <th className="py-2.5 px-3">Risk Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredPredictions.slice(0, 8).map((p, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="py-2 px-3 font-semibold text-slate-100">
                    ({p.x.toFixed(1)}m, {p.y.toFixed(1)}m)
                  </td>
                  <td className="py-2 px-3 text-purple-400 font-bold">
                    {(p.dead_zone_probability * 100).toFixed(1)}%
                  </td>
                  <td className="py-2 px-3 text-rose-400">
                    {p.estimated_rssi.toFixed(1)} dBm
                  </td>
                  <td className="py-2 px-3">
                    {p.estimated_latency.toFixed(0)} ms
                  </td>
                  <td className="py-2 px-3 text-amber-400">
                    {p.estimated_packet_loss.toFixed(1)}%
                  </td>
                  <td className="py-2 px-3">
                    {p.distance_to_ap.toFixed(1)} m
                  </td>
                  <td className="py-2 px-3">
                    {p.wall_factor.toFixed(1)} dB
                  </td>
                  <td className="py-2 px-3 font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      POTENTIAL_DEAD_ZONE
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
