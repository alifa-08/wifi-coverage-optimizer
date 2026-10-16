import React, { useState, useEffect, useCallback } from 'react';
import {
  Server,
  ShieldCheck,
  Users,
  HardDrive,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Power,
  ChevronDown,
  ChevronUp,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';
import { api, adminAuth } from '../api/client';
import { GatewayStatus, GatewayTelemetry, GatewayLiveClient, GatewayEvent } from '../types';

export const GatewayQuotas: React.FC = () => {
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [telemetry, setTelemetry] = useState<GatewayTelemetry | null>(null);
  const [liveClients, setLiveClients] = useState<GatewayLiveClient[]>([]);
  const [events, setEvents] = useState<GatewayEvent[]>([]);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const [showAuditEvents, setShowAuditEvents] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [deauthingMac, setDeauthingMac] = useState<string | null>(null);

  const fetchGatewayData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [statusRes, telemetryRes, sessionsRes] = await Promise.all([
        api.getGatewayStatus().catch((err) => ({
          gateway_ip: '192.168.214.2',
          gateway_connected: false,
          opennds_running: false,
          active_clients_count: 0,
          error: err.response?.data?.detail || err.message || 'Gateway unreachable',
        })),
        api.getGatewayTelemetry().catch(() => null),
        api.getGatewaySessions().catch(() => ({
          gateway_connected: false,
          active_clients_count: 0,
          live_clients: [],
          recent_history: [],
        })),
      ]);

      setStatus(statusRes);
      setTelemetry(telemetryRes);
      setLiveClients(sessionsRes.live_clients || []);

      if (adminAuth.isAuthenticated()) {
        try {
          const evts = await api.adminGetEvents(25);
          setEvents(evts);
        } catch {}
      }
    } catch (err: any) {
      setActionMessage({ type: 'error', text: 'Error polling gateway: ' + err.message });
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchGatewayData();
  }, [fetchGatewayData]);

  const handleDeauthClient = async (mac: string) => {
    if (!window.confirm(`Terminate session and disconnect hardware client ${mac}?`)) return;
    setDeauthingMac(mac);
    setActionMessage(null);
    try {
      await api.adminDeauthClient(mac);
      setActionMessage({ type: 'success', text: `Client ${mac} disconnected via ndsctl.` });
      await fetchGatewayData();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || err.message || 'Deauth failed' });
    } finally {
      setDeauthingMac(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs uppercase tracking-wider mb-1">
            <Server className="w-4 h-4" />
            <span>Hardware Network Node • Live Gateway Status</span>
          </div>
          <h1 className="text-xl font-extrabold text-white tracking-tight">Campus Gateway &amp; Quotas</h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Real-time synchronization with OpenWrt 25.12.5 and OpenNDS 10.3.1. Enforces binary IEC data limits (1 GiB = 1,024 MiB) through kernel netfilter traffic accounting.
          </p>
        </div>

        <button
          onClick={fetchGatewayData}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-all cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Poll Gateway</span>
        </button>
      </div>

      {/* Action Notification Message */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs animate-in fade-in ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
              : 'bg-rose-950/40 border-rose-500/40 text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionMessage.text}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-slate-400 hover:text-white text-xs px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* 4 Concise KPI Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Actual Gateway Connectivity */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            status?.gateway_connected && status?.opennds_running
              ? 'bg-slate-900 border-emerald-500/40'
              : 'bg-rose-950/20 border-rose-500/40'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Gateway State</span>
            {status?.gateway_connected && status?.opennds_running ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/40">
                <CheckCircle2 className="w-3 h-3" /> Online
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/20 px-2 py-0.5 rounded-full border border-rose-500/40">
                <XCircle className="w-3 h-3" /> Standby
              </span>
            )}
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <Server className="w-4 h-4 text-indigo-400" />
            OpenWrt {status?.opennds_version || '25.12.5'}
          </p>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            IP: {status?.gateway_ip || '192.168.214.2'} ({status?.managed_interface || 'br-lan'})
          </p>
        </div>

        {/* Card 2: OpenNDS Status */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">OpenNDS Daemon</span>
            <span className="text-[10px] font-semibold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/30">
              Port 2050
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            FAS Level 1 Mode
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Redirection &bull; SHA256 Authdir
          </p>
        </div>

        {/* Card 3: Active Authenticated Devices */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Active Devices</span>
            <span className="text-[10px] font-bold text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-500/30">
              Live Netfilter
            </span>
          </div>
          <p className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            {liveClients.length}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Authorized client devices
          </p>
        </div>

        {/* Card 4: Daily Quota Policy */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Quota Standard</span>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/30">
              Binary IEC
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
            <HardDrive className="w-4 h-4 text-emerald-400" />
            1 GiB = 1,024 MiB
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Upload: 15% &bull; Download: 85%
          </p>
        </div>
      </div>

      {/* Active Connected Client Devices Table */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Live Connected Devices on Gateway ({liveClients.length})
            </h2>
            <p className="text-xs text-slate-400">
              Hardware client sessions active in OpenNDS iptables rules on interface <code className="text-slate-300">br-lan</code>.
            </p>
          </div>
        </div>

        {liveClients.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Client MAC</th>
                  <th className="py-2.5 px-3">IP Address</th>
                  <th className="py-2.5 px-3">Associated Student</th>
                  <th className="py-2.5 px-3">Data Uploaded</th>
                  <th className="py-2.5 px-3">Data Downloaded</th>
                  <th className="py-2.5 px-3">Session State</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {liveClients.map((client) => (
                  <tr key={client.mac} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-200">{client.mac}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{client.ip || '—'}</td>
                    <td className="py-2.5 px-3 text-indigo-300 font-semibold">{client.student_id || 'Campus Client'}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300 flex items-center gap-1">
                      <ArrowUpRight className="w-3.5 h-3.5 text-indigo-400" />
                      {(client.upload_bytes / (1024 * 1024)).toFixed(2)} MB
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">
                      <span className="flex items-center gap-1">
                        <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" />
                        {(client.download_bytes / (1024 * 1024)).toFixed(2)} MB
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Authorized
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleDeauthClient(client.mac)}
                        disabled={deauthingMac === client.mac}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-all cursor-pointer ml-auto"
                        title="Disconnect client device from OpenWrt"
                      >
                        <Power className="w-3.5 h-3.5" />
                        <span>Disconnect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-400 border border-slate-800/60 rounded-xl bg-slate-950/40 space-y-1">
            <p className="font-semibold text-slate-300">No client devices currently authorized on OpenWrt gateway.</p>
            <p className="text-slate-400">
              When students authenticate through the captive portal, their hardware MAC address appears here automatically.
            </p>
          </div>
        )}
      </div>

      {/* Expandable Section: Technical OpenNDS & Netfilter Architecture */}
      <div className="border border-slate-800 rounded-2xl bg-slate-900/60 overflow-hidden">
        <button
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
          className="w-full flex items-center justify-between p-4 text-xs font-bold text-slate-200 hover:text-white hover:bg-slate-800/40 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Technical Gateway Architecture &amp; Netfilter Diagnostics</span>
          </div>
          {showTechnicalDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTechnicalDetails && (
          <div className="p-5 border-t border-slate-800 space-y-4 text-xs bg-slate-950/40">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <h4 className="font-bold text-white uppercase text-[11px] text-indigo-300">
                  OpenNDS FAS Level 1 Redirection
                </h4>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  OpenNDS intercepts HTTP port 80 requests from unauthenticated clients on <code className="text-slate-300 font-mono">br-lan</code> and redirects to FAS authdir with hashed query tokens: <code className="text-slate-300 font-mono">?fas=[token]&amp;tok=[sha256(hid+faskey)]</code>.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <h4 className="font-bold text-white uppercase text-[11px] text-emerald-300">
                  Netfilter Kernel Accounting
                </h4>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Upon authentication, <code className="text-slate-300 font-mono">ndsctl auth &lt;mac&gt; &lt;mins&gt; &lt;up_kb&gt; &lt;down_kb&gt;</code> writes iptables filter rules in the Linux kernel. Clients are automatically disconnected when either byte quota is reached or the session window expires.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Expandable Section: Security & Quota Audit Events Log */}
      <div className="border border-slate-800 rounded-2xl bg-slate-900/60 overflow-hidden">
        <button
          onClick={() => setShowAuditEvents(!showAuditEvents)}
          className="w-full flex items-center justify-between p-4 text-xs font-bold text-slate-200 hover:text-white hover:bg-slate-800/40 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            <span>Security &amp; Quota Audit Log ({events.length} events recorded)</span>
          </div>
          {showAuditEvents ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAuditEvents && (
          <div className="p-5 border-t border-slate-800 space-y-3 bg-slate-950/40">
            {events.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Event Type</th>
                      <th className="py-2.5 px-3">Student USN</th>
                      <th className="py-2.5 px-3">Actor</th>
                      <th className="py-2.5 px-3">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-medium">
                    {events.map((evt) => (
                      <tr key={evt.id} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-2 px-3 font-semibold text-slate-200">{evt.event_type}</td>
                        <td className="py-2 px-3 font-mono text-emerald-300">{evt.student_id || '—'}</td>
                        <td className="py-2 px-3 text-slate-400">{evt.actor}</td>
                        <td className="py-2 px-3 text-slate-300">{evt.details}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-xs text-slate-400 py-4">No audit events recorded yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
