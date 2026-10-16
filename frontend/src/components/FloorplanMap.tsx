import React, { useState } from 'react';
import { Room, Wall, AccessPoint, Measurement, DeadZone, PredictionGridPoint, APRecommendation } from '../types';
import { Wifi, AlertTriangle, Sparkles, MapPin, Layers } from 'lucide-react';

interface FloorplanMapProps {
  rooms: Room[];
  walls: Wall[];
  accessPoints: AccessPoint[];
  measurements?: Measurement[];
  deadZones?: DeadZone[];
  predictedGrid?: PredictionGridPoint[];
  recommendations?: APRecommendation[];
  selectedDeadZoneId?: number | null;
  onSelectDeadZone?: (dz: DeadZone) => void;
  width?: number;
  height?: number;
  showControls?: boolean;
}

export const FloorplanMap: React.FC<FloorplanMapProps> = ({
  rooms = [],
  walls = [],
  accessPoints = [],
  measurements = [],
  deadZones = [],
  predictedGrid = [],
  recommendations = [],
  selectedDeadZoneId,
  onSelectDeadZone,
  width = 80,
  height = 50,
  showControls = true,
}) => {
  // Layer visibility toggles
  const [showRooms, setShowRooms] = useState(true);
  const [showWalls, setShowWalls] = useState(true);
  const [showAPs, setShowAPs] = useState(true);
  const [showMeasurements, setShowMeasurements] = useState(false);
  const [showDeadZones, setShowDeadZones] = useState(true);
  const [showPredicted, setShowPredicted] = useState(true);
  const [showRecs, setShowRecs] = useState(true);

  // Hover inspector
  const [hoveredItem, setHoveredItem] = useState<{
    type: 'ap' | 'deadzone' | 'measurement' | 'prediction' | 'recommendation';
    data: any;
  } | null>(null);

  return (
    <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Controls toolbar */}
      {showControls && (
        <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-slate-800/80 border-b border-slate-700/60 text-xs">
          <div className="flex items-center space-x-2 text-slate-300 font-medium">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Map Layers:</span>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setShowDeadZones(!showDeadZones)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                showDeadZones ? 'bg-rose-600 text-white shadow-sm shadow-rose-900/50' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Current Dead Zones ({deadZones.length})
            </button>

            <button
              onClick={() => setShowPredicted(!showPredicted)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                showPredicted ? 'bg-purple-600 text-white shadow-sm shadow-purple-900/50' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              ML Predictions ({predictedGrid.filter((p) => p.predicted_risk === 'POTENTIAL_DEAD_ZONE').length})
            </button>

            <button
              onClick={() => setShowMeasurements(!showMeasurements)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                showMeasurements ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-900/50' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Measurements ({measurements.length})
            </button>

            <button
              onClick={() => setShowAPs(!showAPs)}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                showAPs ? 'bg-blue-600 text-white shadow-sm shadow-blue-900/50' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Access Points ({accessPoints.length})
            </button>

            {recommendations.length > 0 && (
              <button
                onClick={() => setShowRecs(!showRecs)}
                className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                  showRecs ? 'bg-cyan-600 text-white shadow-sm shadow-cyan-900/50' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Recommended APs ({recommendations.length})
              </button>
            )}
          </div>
        </div>
      )}

      {/* SVG Canvas */}
      <div className="relative w-full aspect-[80/50] bg-slate-950 p-2 overflow-hidden flex items-center justify-center">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full select-none"
          style={{ maxHeight: '680px' }}
        >
          <defs>
            {/* Dead zone hatched pattern */}
            <pattern id="deadZoneHatch" width="4" height="4" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="4" stroke="#f43f5e" strokeWidth="1.2" opacity="0.6" />
            </pattern>
            {/* Predicted dead zone hatch */}
            <pattern id="predHatch" width="4" height="4" patternTransform="rotate(135 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="4" stroke="#a855f7" strokeWidth="1" opacity="0.5" />
            </pattern>
          </defs>

          {/* 1. ROOMS LAYER */}
          {showRooms &&
            rooms.map((room) => {
              const rw = room.x2 - room.x1;
              const rh = room.y2 - room.y1;
              return (
                <g key={`room-${room.id}`}>
                  <rect
                    x={room.x1}
                    y={room.y1}
                    width={rw}
                    height={rh}
                    fill={room.room_type === 'corridor' ? '#1e293b' : '#0f172a'}
                    stroke="#334155"
                    strokeWidth="0.4"
                    opacity="0.9"
                  />
                  {/* Room Label */}
                  <text
                    x={room.x1 + rw / 2}
                    y={room.y1 + rh / 2 - 0.5}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#94a3b8"
                    fontSize="1.8"
                    fontWeight="600"
                    className="pointer-events-none uppercase tracking-wider"
                  >
                    {room.name}
                  </text>
                  <text
                    x={room.x1 + rw / 2}
                    y={room.y1 + rh / 2 + 1.8}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#475569"
                    fontSize="1.1"
                    className="pointer-events-none"
                  >
                    {rw.toFixed(0)}m × {rh.toFixed(0)}m
                  </text>
                </g>
              );
            })}

          {/* 2. MEASUREMENT POINTS HEATMAP (Optional) */}
          {showMeasurements &&
            measurements.map((m) => {
              let fill = '#10b981'; // Good
              if (m.quality_category === 'MODERATE') fill = '#f59e0b';
              if (m.quality_category === 'POOR') fill = '#ef4444';
              return (
                <circle
                  key={`meas-${m.id}`}
                  cx={m.x}
                  cy={m.y}
                  r="0.8"
                  fill={fill}
                  opacity="0.65"
                  className="cursor-pointer hover:opacity-100 hover:r-1.5 transition-all"
                  onMouseEnter={() => setHoveredItem({ type: 'measurement', data: m })}
                  onMouseLeave={() => setHoveredItem(null)}
                />
              );
            })}

          {/* 3. ML PREDICTED DEAD ZONES LAYER */}
          {showPredicted &&
            predictedGrid
              .filter((p) => p.predicted_risk === 'POTENTIAL_DEAD_ZONE')
              .map((p, idx) => (
                <rect
                  key={`pred-${idx}`}
                  x={p.x - 1.2}
                  y={p.y - 1.2}
                  width="2.4"
                  height="2.4"
                  rx="0.4"
                  fill="#9333ea"
                  opacity={0.3 + p.dead_zone_probability * 0.4}
                  stroke="#c084fc"
                  strokeWidth="0.15"
                  className="cursor-pointer hover:opacity-90"
                  onMouseEnter={() => setHoveredItem({ type: 'prediction', data: p })}
                  onMouseLeave={() => setHoveredItem(null)}
                />
              ))}

          {/* 4. CURRENT DEAD ZONES LAYER (Polygons & Labels) */}
          {showDeadZones &&
            deadZones.map((dz) => {
              const isSelected = selectedDeadZoneId === dz.id;
              const pointsStr = dz.polygon_points.map((pt) => `${pt[0]},${pt[1]}`).join(' ');

              return (
                <g key={`dz-${dz.id}`}>
                  {/* Outer glow aura */}
                  <polygon
                    points={pointsStr}
                    fill="url(#deadZoneHatch)"
                    stroke={isSelected ? '#f43f5e' : '#e11d48'}
                    strokeWidth={isSelected ? '0.9' : '0.6'}
                    strokeDasharray={isSelected ? 'none' : '1,0.5'}
                    className="cursor-pointer transition-all"
                    onClick={() => onSelectDeadZone && onSelectDeadZone(dz)}
                    onMouseEnter={() => setHoveredItem({ type: 'deadzone', data: dz })}
                    onMouseLeave={() => setHoveredItem(null)}
                  />

                  {/* Marker Pin at Dead Zone Center */}
                  <g
                    transform={`translate(${dz.center_x}, ${dz.center_y})`}
                    className="cursor-pointer"
                    onClick={() => onSelectDeadZone && onSelectDeadZone(dz)}
                    onMouseEnter={() => setHoveredItem({ type: 'deadzone', data: dz })}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    <circle r="2.2" fill="#881337" opacity="0.85" stroke="#f43f5e" strokeWidth="0.4" />
                    <text
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#fff"
                      fontSize="1.3"
                      fontWeight="bold"
                    >
                      DZ
                    </text>
                  </g>
                </g>
              );
            })}

          {/* 5. WALLS LAYER */}
          {showWalls &&
            walls.map((wall) => {
              const isConcrete = wall.wall_type === 'concrete';
              return (
                <line
                  key={`wall-${wall.id}`}
                  x1={wall.x1}
                  y1={wall.y1}
                  x2={wall.x2}
                  y2={wall.y2}
                  stroke={isConcrete ? '#475569' : '#64748b'}
                  strokeWidth={isConcrete ? '0.8' : '0.5'}
                  strokeLinecap="round"
                />
              );
            })}

          {/* 6. RECOMMENDED ACCESS POINTS */}
          {showRecs &&
            recommendations.map((rec) => (
              <g
                key={`rec-${rec.id}`}
                transform={`translate(${rec.candidate_x}, ${rec.candidate_y})`}
                className="cursor-pointer animate-pulse"
                onMouseEnter={() => setHoveredItem({ type: 'recommendation', data: rec })}
                onMouseLeave={() => setHoveredItem(null)}
              >
                {/* Coverage radius preview circle */}
                <circle r="18" fill="none" stroke="#06b6d4" strokeWidth="0.3" strokeDasharray="1,1" opacity="0.6" />
                <circle r="2.4" fill="#0891b2" stroke="#22d3ee" strokeWidth="0.6" />
                <text
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#fff"
                  fontSize="1.2"
                  fontWeight="bold"
                >
                  +AP{rec.priority}
                </text>
              </g>
            ))}

          {/* 7. EXISTING ACCESS POINTS */}
          {showAPs &&
            accessPoints.map((ap) => (
              <g
                key={`ap-${ap.id}`}
                transform={`translate(${ap.x}, ${ap.y})`}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredItem({ type: 'ap', data: ap })}
                onMouseLeave={() => setHoveredItem(null)}
              >
                {/* Radio propagation range halo */}
                <circle r="15" fill="#3b82f6" fillOpacity="0.04" stroke="#60a5fa" strokeWidth="0.25" strokeDasharray="0.8,0.8" />
                <circle r="1.8" fill="#2563eb" stroke="#93c5fd" strokeWidth="0.4" />
                <text
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#ffffff"
                  fontSize="1.0"
                  fontWeight="bold"
                >
                  AP
                </text>
                {/* Label */}
                <text
                  y="2.8"
                  textAnchor="middle"
                  fill="#bfdbfe"
                  fontSize="1.0"
                  fontWeight="500"
                  className="pointer-events-none"
                >
                  {ap.name}
                </text>
              </g>
            ))}
        </svg>

        {/* Live Hover Detail Card overlay */}
        {hoveredItem && (
          <div className="absolute bottom-3 left-3 bg-slate-900/95 border border-slate-700/80 p-3 rounded-lg shadow-2xl backdrop-blur-md max-w-xs text-xs z-20">
            {hoveredItem.type === 'deadzone' && (
              <div>
                <div className="flex items-center space-x-1.5 text-rose-400 font-bold mb-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>{hoveredItem.data.name}</span>
                </div>
                <div className="space-y-0.5 text-slate-300">
                  <p>Severity: <span className="font-semibold text-rose-300">{hoveredItem.data.severity}</span></p>
                  <p>Affected Area: <span className="font-semibold">{hoveredItem.data.affected_area} m²</span></p>
                  <p>Avg RSSI: <span className="font-semibold">{hoveredItem.data.avg_rssi} dBm</span></p>
                  <p>Avg Latency: <span className="font-semibold">{hoveredItem.data.avg_latency} ms</span></p>
                  <p>Packet Loss: <span className="font-semibold">{hoveredItem.data.avg_packet_loss}%</span></p>
                </div>
              </div>
            )}

            {hoveredItem.type === 'prediction' && (
              <div>
                <div className="flex items-center space-x-1.5 text-purple-400 font-bold mb-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Predicted Dead Zone</span>
                </div>
                <div className="space-y-0.5 text-slate-300">
                  <p>Coordinates: ({hoveredItem.data.x}m, {hoveredItem.data.y}m)</p>
                  <p>Dead-Zone Probability: <span className="font-semibold text-purple-300">{(hoveredItem.data.dead_zone_probability * 100).toFixed(1)}%</span></p>
                  <p>Est. RSSI: <span className="font-semibold">{hoveredItem.data.estimated_rssi} dBm</span></p>
                  <p>Distance to nearest AP: <span className="font-semibold">{hoveredItem.data.distance_to_ap} m</span></p>
                </div>
              </div>
            )}

            {hoveredItem.type === 'ap' && (
              <div>
                <div className="flex items-center space-x-1.5 text-blue-400 font-bold mb-1">
                  <Wifi className="w-3.5 h-3.5" />
                  <span>{hoveredItem.data.name}</span>
                </div>
                <div className="space-y-0.5 text-slate-300">
                  <p>SSID: <span className="font-semibold">{hoveredItem.data.ssid}</span></p>
                  <p>Channel: <span className="font-semibold">{hoveredItem.data.channel}</span> ({hoveredItem.data.frequency_ghz} GHz)</p>
                  <p>Tx Power: <span className="font-semibold">{hoveredItem.data.tx_power_dbm} dBm</span></p>
                  <p>Location: ({hoveredItem.data.x}m, {hoveredItem.data.y}m)</p>
                </div>
              </div>
            )}

            {hoveredItem.type === 'recommendation' && (
              <div>
                <div className="flex items-center space-x-1.5 text-cyan-400 font-bold mb-1">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Recommended AP #{hoveredItem.data.priority}</span>
                </div>
                <div className="space-y-0.5 text-slate-300">
                  <p>Location: ({hoveredItem.data.candidate_x}m, {hoveredItem.data.candidate_y}m)</p>
                  <p>Expected Area Gain: <span className="font-semibold text-cyan-300">{hoveredItem.data.expected_dead_zone_reduction_area} m²</span></p>
                  <p className="text-slate-400 italic text-[11px] mt-1">{hoveredItem.data.reason}</p>
                </div>
              </div>
            )}

            {hoveredItem.type === 'measurement' && (
              <div>
                <div className="font-bold text-slate-200 mb-1">Sample Measurement</div>
                <div className="space-y-0.5 text-slate-300">
                  <p>RSSI: <span className="font-semibold">{hoveredItem.data.rssi} dBm</span></p>
                  <p>Quality: <span className="font-semibold">{hoveredItem.data.quality_category} ({hoveredItem.data.quality_score}/100)</span></p>
                  <p>Latency: {hoveredItem.data.latency} ms | Loss: {hoveredItem.data.packet_loss}%</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
