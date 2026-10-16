import React from 'react';
import {
  BarChart3,
  Signal,
  Clock,
  WifiOff,
  Zap,
  Layers,
} from 'lucide-react';
import { Measurement, Floor } from '../types';
import { StatCard } from '../components/StatCard';

interface NetworkAnalyticsProps {
  measurements: Measurement[];
  floor: Floor | null;
}

export const NetworkAnalytics: React.FC<NetworkAnalyticsProps> = ({ measurements, floor }) => {
  // Aggregate RSSI Bins
  const goodCount = measurements.filter((m) => m.rssi >= -65).length;
  const modCount = measurements.filter((m) => m.rssi >= -78 && m.rssi < -65).length;
  const poorCount = measurements.filter((m) => m.rssi < -78).length;
  const total = Math.max(measurements.length, 1);

  // Group by Room with strict health classification
  const roomMetrics = (floor?.rooms || []).map((r) => {
    const pts = measurements.filter((m) => m.x >= r.x1 && m.x <= r.x2 && m.y >= r.y1 && m.y <= r.y2);
    const hasData = pts.length > 0;
    const avgR = hasData ? pts.reduce((acc, p) => acc + p.rssi, 0) / pts.length : null;
    const avgL = hasData ? pts.reduce((acc, p) => acc + p.latency, 0) / pts.length : null;
    const avgLoss = hasData ? pts.reduce((acc, p) => acc + p.packet_loss, 0) / pts.length : null;
    const poorRatio = hasData ? (pts.filter((p) => p.quality_category === 'POOR').length / pts.length) * 100 : null;

    let healthStatus: 'NO_DATA' | 'INCOMPLETE_DATA' | 'CRITICAL' | 'DEGRADED' | 'MODERATE' | 'OPTIMAL' = 'NO_DATA';
    if (!hasData || avgR === null) {
      healthStatus = 'NO_DATA';
    } else if (avgR < -82.0 || (poorRatio !== null && poorRatio > 35.0)) {
      healthStatus = 'CRITICAL';
    } else if (
      avgR < -75.0 ||
      (poorRatio !== null && poorRatio > 15.0) ||
      (avgLoss !== null && avgLoss > 10.0) ||
      (avgL !== null && avgL > 120.0)
    ) {
      healthStatus = 'DEGRADED';
    } else if (
      avgR < -70.0 ||
      (poorRatio !== null && poorRatio > 5.0) ||
      (avgLoss !== null && avgLoss > 5.0) ||
      (avgL !== null && avgL > 80.0)
    ) {
      healthStatus = 'MODERATE';
    } else if (avgL === null || avgLoss === null) {
      healthStatus = 'INCOMPLETE_DATA';
    } else {
      healthStatus = 'OPTIMAL';
    }

    return {
      name: r.name,
      hasData,
      points: pts.length,
      avgRssi: avgR !== null ? Math.round(avgR * 10) / 10 : null,
      avgLatency: avgL !== null ? Math.round(avgL) : null,
      avgLoss: avgLoss !== null ? Math.round(avgLoss * 10) / 10 : null,
      poorPct: poorRatio !== null ? Math.round(poorRatio) : null,
      healthStatus,
    };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
          <BarChart3 className="w-4 h-4" />
          <span>Network Performance Analytics</span>
        </div>
        <h2 className="text-xl font-extrabold text-white tracking-tight">
          RF Signal &amp; Telemetry Distributions
        </h2>
        <p className="text-xs text-slate-400 max-w-2xl mt-1">
          Quantitative examination of physical signal strength, transmission delay, dropped packet ratios, and room-level connectivity indices.
        </p>

        {/* Telemetry Source Banner */}
        <div className="mt-3 flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300">
          <Layers className="w-3.5 h-3.5 shrink-0" />
          <span>
            Telemetry Source: Physics-based multi-wall RF propagation ray-tracing grid combined with live survey walk-test coordinates.
          </span>
        </div>
      </div>

      {/* Signal Distribution Visual Bars */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Overall Wi-Fi Quality Distribution ({measurements.length} Sample Points)
        </h3>

        {/* Stacked Percentage Bar */}
        <div className="w-full h-6 rounded-xl overflow-hidden flex bg-slate-950 p-1 border border-slate-800">
          <div
            style={{ width: `${(goodCount / total) * 100}%` }}
            className="h-full bg-emerald-500 rounded-l transition-all"
            title={`Good: ${goodCount} (${((goodCount / total) * 100).toFixed(1)}%)`}
          />
          <div
            style={{ width: `${(modCount / total) * 100}%` }}
            className="h-full bg-amber-500 transition-all"
            title={`Moderate: ${modCount} (${((modCount / total) * 100).toFixed(1)}%)`}
          />
          <div
            style={{ width: `${(poorCount / total) * 100}%` }}
            className="h-full bg-rose-500 rounded-r transition-all"
            title={`Poor: ${poorCount} (${((poorCount / total) * 100).toFixed(1)}%)`}
          />
        </div>

        {/* Category Breakdown Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/40">
            <span className="text-xs font-bold text-emerald-400 uppercase">GOOD COVERAGE</span>
            <p className="text-2xl font-black text-white mt-1">
              {((goodCount / total) * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {goodCount} points (RSSI ≥ -65 dBm, Latency &lt; 30ms)
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-900/40">
            <span className="text-xs font-bold text-amber-400 uppercase">MODERATE COVERAGE</span>
            <p className="text-2xl font-black text-white mt-1">
              {((modCount / total) * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {modCount} points (-78 to -65 dBm, standard load)
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40">
            <span className="text-xs font-bold text-rose-400 uppercase">DEAD ZONE / POOR</span>
            <p className="text-2xl font-black text-white mt-1">
              {((poorCount / total) * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {poorCount} points (RSSI &lt; -78 dBm, packet loss spikes)
            </p>
          </div>
        </div>
      </div>

      {/* Room Level Breakdown Table */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Room-Level Performance Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Room / Campus Area</th>
                <th className="py-2.5 px-3">Samples</th>
                <th className="py-2.5 px-3">Avg RSSI</th>
                <th className="py-2.5 px-3">Avg Latency</th>
                <th className="py-2.5 px-3">Packet Loss</th>
                <th className="py-2.5 px-3">Dead-Zone Ratio</th>
                <th className="py-2.5 px-3">Health Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {roomMetrics.map((rm, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="py-2 px-3 font-sans font-semibold text-slate-100">
                    {rm.name}
                  </td>
                  <td className="py-2 px-3 text-slate-400">{rm.points} pts</td>
                  <td className={`py-2 px-3 ${rm.avgRssi !== null && rm.avgRssi < -78 ? 'text-rose-400 font-bold' : 'text-slate-200'}`}>
                    {rm.hasData ? `${rm.avgRssi} dBm` : '—'}
                  </td>
                  <td className="py-2 px-3">{rm.hasData ? `${rm.avgLatency} ms` : '—'}</td>
                  <td className="py-2 px-3 text-amber-400">{rm.hasData ? `${rm.avgLoss}%` : '—'}</td>
                  <td className="py-2 px-3">
                    {rm.hasData ? (
                      <span className={`font-bold ${rm.poorPct !== null && rm.poorPct > 20 ? 'text-rose-400' : 'text-slate-300'}`}>
                        {rm.poorPct}%
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="py-2 px-3 font-sans">
                    {rm.healthStatus === 'NO_DATA' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                        NO DATA
                      </span>
                    ) : rm.healthStatus === 'INCOMPLETE_DATA' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800/80 text-amber-300 border border-amber-500/40">
                        INCOMPLETE TELEMETRY
                      </span>
                    ) : rm.healthStatus === 'CRITICAL' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        CRITICAL DEAD ZONE
                      </span>
                    ) : rm.healthStatus === 'DEGRADED' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        DEGRADED
                      </span>
                    ) : rm.healthStatus === 'MODERATE' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                        MODERATE
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        OPTIMAL
                      </span>
                    )}
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
