import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Sparkles,
  Layers,
  ShieldCheck,
  Signal,
  Clock,
  WifiOff,
  Cpu,
  ArrowRight,
  Server,
  Users,
  HardDrive,
  CheckCircle2,
} from 'lucide-react';
import { DashboardSummary, Floor, DeadZone, GatewayStatus, GatewayTelemetry } from '../types';
import { api } from '../api/client';
import { StatCard } from '../components/StatCard';
import { SeverityBadge } from '../components/SeverityBadge';
import { FloorplanMap } from '../components/FloorplanMap';
import { PageId } from '../components/Sidebar';

interface DashboardProps {
  summary: DashboardSummary | null;
  floor: Floor | null;
  onNavigate: (page: PageId) => void;
  onSelectDeadZone: (dz: DeadZone) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  summary,
  floor,
  onNavigate,
  onSelectDeadZone,
}) => {
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null);
  const [gatewayTelemetry, setGatewayTelemetry] = useState<GatewayTelemetry | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchGatewayData = async () => {
      try {
        const [st, tel] = await Promise.all([
          api.getGatewayStatus().catch(() => null),
          api.getGatewayTelemetry().catch(() => null),
        ]);
        if (isMounted) {
          setGatewayStatus(st);
          setGatewayTelemetry(tel);
        }
      } catch {
        // Silently fail-safe
      }
    };
    fetchGatewayData();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Real Available System Information Summary Banner */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Integrated Campus Network &amp; Wi-Fi Overview
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Live status from OpenWrt 25.12.5 gateway node and multi-wall RF simulation engine.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={() => onNavigate('gateway-quotas')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 font-semibold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              <span>Gateway Node</span>
            </button>
            <button
              onClick={() => onNavigate('student-management')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 font-semibold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Users className="w-3.5 h-3.5 text-indigo-400" />
              <span>Student Roster</span>
            </button>
          </div>
        </div>

        {/* 4 Core Summary Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Gateway Connection
            </span>
            <div className="text-xs font-bold text-slate-100 mt-1 flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate">
                {gatewayStatus?.gateway_connected ? 'OpenWrt 25.12.5 (Online)' : 'Standby / Safe'}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
              IP: {gatewayStatus?.gateway_ip || '192.168.214.2'} (br-lan)
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Active Authorized Devices
            </span>
            <div className="text-base font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
              <Users className="w-4 h-4 text-emerald-400" />
              <span>{gatewayStatus?.active_clients_count ?? 0}</span>
              <span className="text-xs text-slate-400 font-normal">devices</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">
              Netfilter kernel accounting
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Student Accounts
            </span>
            <div className="text-base font-bold text-indigo-300 mt-1 flex items-center gap-1.5">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>{gatewayTelemetry?.total_demo_students ?? 5}</span>
              <span className="text-xs text-slate-400 font-normal">accounts</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">
              Fleet Quota Managed
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Daily Fleet Quota
            </span>
            <div className="text-xs font-bold text-slate-200 mt-1 flex items-center gap-1.5">
              <HardDrive className="w-3.5 h-3.5 text-teal-400 shrink-0" />
              <span className="font-mono">
                {gatewayTelemetry?.total_consumed_quota_mb ?? 0} / {gatewayTelemetry?.total_allocated_quota_mb ?? 5120} MiB
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">
              Standard: 1 GiB = 1,024 MiB
            </span>
          </div>
        </div>
      </div>

      {/* Primary RF Wi-Fi KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard
          title="Current Dead Zones"
          value={summary?.current_dead_zones ?? 0}
          unit="clusters"
          subtitle="Spatially clustered"
          icon={AlertTriangle}
          variant="danger"
        />
        <StatCard
          title="Predicted Dead Zones"
          value={summary?.predicted_dead_zones ?? 0}
          unit="grid pts"
          subtitle="Random Forest risk points"
          icon={Sparkles}
          variant="purple"
        />
        <StatCard
          title="Dead-Zone Area"
          value={summary?.total_dead_zone_area ?? 0}
          unit="m²"
          subtitle={`${summary?.percentage_affected ?? 0}% of floorplan`}
          icon={Layers}
          variant="warning"
        />
        <StatCard
          title="Coverage Score"
          value={summary?.coverage_score ?? 0}
          unit="/100"
          subtitle="Composite RF health"
          icon={ShieldCheck}
          variant="success"
        />
        <StatCard
          title="Average RSSI"
          value={summary?.avg_rssi ?? 0}
          unit="dBm"
          subtitle="Floor signal level"
          icon={Signal}
          variant="default"
        />
      </div>

      {/* Floorplan & Detected Dead Zones Split Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Floorplan Overview (2 cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Live Floorplan Overview
              </h2>
              <p className="text-xs text-slate-400">
                Visualizing physical rooms, concrete partitions, access points, and dead-zone polygons
              </p>
            </div>
            <button
              onClick={() => onNavigate('wifi-coverage')}
              className="flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer"
            >
              <span>Full Interactive Map</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {floor && (
            <FloorplanMap
              rooms={floor.rooms}
              walls={floor.walls}
              accessPoints={floor.access_points}
              deadZones={summary?.dead_zones || []}
              onSelectDeadZone={(dz) => {
                onSelectDeadZone(dz);
                onNavigate('dead-zone-prediction');
              }}
              showControls={true}
            />
          )}
        </div>

        {/* Top Detected Dead Zones List (1 col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Detected Dead Zones
            </h2>
            <button
              onClick={() => onNavigate('dead-zone-prediction')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer"
            >
              View All ({summary?.dead_zones?.length || 0})
            </button>
          </div>

          <div className="space-y-2.5">
            {summary?.dead_zones && summary.dead_zones.length > 0 ? (
              summary.dead_zones.map((dz) => (
                <div
                  key={dz.id}
                  onClick={() => {
                    onSelectDeadZone(dz);
                    onNavigate('dead-zone-prediction');
                  }}
                  className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer shadow-md group"
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 group-hover:text-indigo-400">
                        {dz.name}
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        Affected Area: <span className="font-semibold text-slate-300">{dz.affected_area} m²</span>
                      </p>
                    </div>
                    <SeverityBadge severity={dz.severity} />
                  </div>

                  <div className="grid grid-cols-3 gap-1 py-1.5 px-2 bg-slate-950/60 rounded-lg text-[10px] text-slate-400 mb-2">
                    <div>
                      RSSI: <span className="text-rose-400 font-semibold">{dz.avg_rssi} dBm</span>
                    </div>
                    <div>
                      Latency: <span className="text-slate-200 font-semibold">{dz.avg_latency} ms</span>
                    </div>
                    <div>
                      Loss: <span className="text-amber-400 font-semibold">{dz.avg_packet_loss}%</span>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 line-clamp-1">
                    <span className="font-medium text-slate-300">Cause: </span>
                    {dz.contributing_factors[0] || 'Path loss obstruction'}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-xs text-slate-400">
                <p>No active dead zones detected in this scenario.</p>
                <p className="mt-1 text-slate-400">Run a simulation in Simulation &amp; Testing to detect clusters.</p>
              </div>
            )}
          </div>

          {/* Quick Action Navigation Buttons */}
          <div className="pt-2 grid grid-cols-2 gap-2">
            <button
              onClick={() => onNavigate('ap-optimization')}
              className="p-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/30 hover:bg-indigo-600/20 text-indigo-300 font-semibold text-xs transition-all text-center cursor-pointer"
            >
              AP Recommendations
            </button>
            <button
              onClick={() => onNavigate('before-after')}
              className="p-2.5 rounded-lg bg-emerald-600/10 border border-emerald-500/30 hover:bg-emerald-600/20 text-emerald-300 font-semibold text-xs transition-all text-center cursor-pointer"
            >
              Before vs After
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
