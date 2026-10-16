import React from 'react';
import { Floor, Measurement, DeadZone, PredictionGridPoint, APRecommendation } from '../types';
import { FloorplanMap } from '../components/FloorplanMap';
import { Layers, Info, Wifi, AlertTriangle, Sparkles, MapPin } from 'lucide-react';

interface CoverageMapProps {
  floor: Floor | null;
  measurements: Measurement[];
  deadZones: DeadZone[];
  predictedGrid: PredictionGridPoint[];
  recommendations: APRecommendation[];
  onSelectDeadZone: (dz: DeadZone) => void;
}

export const CoverageMap: React.FC<CoverageMapProps> = ({
  floor,
  measurements,
  deadZones,
  predictedGrid,
  recommendations,
  onSelectDeadZone,
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4" />
            <span>Interactive Floorplan Visualization</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">
            Spatial RF Coverage &amp; Dead-Zone Map
          </h2>
          <p className="text-xs text-slate-400 max-w-2xl mt-1">
            Inspect live measurements, structural partitions, active AP propagation halos, measured dead-zone polygon boundaries, and machine-learning risk predictions.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 bg-slate-950/70 p-3 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-slate-300">Good (&gt;-65 dBm)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="text-slate-300">Moderate (-65 to -78)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500" />
            <span className="text-slate-300">Poor / Dead Zone (&lt;-78)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-sm bg-purple-600 border border-purple-400" />
            <span className="text-purple-300">ML Predicted Risk</span>
          </div>
        </div>
      </div>

      {/* Interactive Map Component */}
      {floor ? (
        <FloorplanMap
          rooms={floor.rooms}
          walls={floor.walls}
          accessPoints={floor.access_points}
          measurements={measurements}
          deadZones={deadZones}
          predictedGrid={predictedGrid}
          recommendations={recommendations}
          onSelectDeadZone={onSelectDeadZone}
          showControls={true}
        />
      ) : (
        <div className="p-12 text-center text-slate-500 bg-slate-900 rounded-xl">
          Loading floorplan data...
        </div>
      )}

      {/* Layer Explanation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center space-x-2 text-blue-400 font-bold mb-1">
            <Wifi className="w-4 h-4" />
            <span>Existing APs</span>
          </div>
          <p className="text-slate-400">
            Current operational Wi-Fi access points with 15m nominal coverage halos and radio channel allocations.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center space-x-2 text-rose-400 font-bold mb-1">
            <AlertTriangle className="w-4 h-4" />
            <span>Current Dead Zones</span>
          </div>
          <p className="text-slate-400">
            Regions where spatial clusters of measurements fail latency, packet loss, or RSSI thresholds.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center space-x-2 text-purple-400 font-bold mb-1">
            <Sparkles className="w-4 h-4" />
            <span>ML Predicted Zones</span>
          </div>
          <p className="text-slate-400">
            Unmeasured locations where the trained Random Forest classifier predicts high probability of dead zone occurrence.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold mb-1">
            <MapPin className="w-4 h-4" />
            <span>Recommended APs</span>
          </div>
          <p className="text-slate-400">
            Algorithmically generated candidate locations simulated to maximize dead-zone area reduction.
          </p>
        </div>
      </div>
    </div>
  );
};
