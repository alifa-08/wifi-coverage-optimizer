import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import {
  Floor,
  Building,
  Room,
  SurveySession,
  SurveyMeasurement,
  LiveWifiStatus,
  SurveyAnalysisResult,
  DeadZone,
} from '../types';
import {
  Radio,
  MapPin,
  RefreshCw,
  Plus,
  Trash2,
  Download,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Wifi,
  Activity,
  Layers,
  Sparkles,
  FileSpreadsheet,
  Info,
  Crosshair,
  Sliders,
} from 'lucide-react';

interface RealSurveyProps {
  currentFloor: Floor | null;
  buildings: Building[];
  onFloorChange?: (floorId: number) => void;
  onNavigateToDeadZones?: (deadZone: DeadZone) => void;
}

export const RealSurvey: React.FC<RealSurveyProps> = ({
  currentFloor,
  buildings,
  onFloorChange,
  onNavigateToDeadZones,
}) => {
  // Floor State (with automatic fallback load if parent hasn't resolved it)
  const [activeFloor, setActiveFloor] = useState<Floor | null>(currentFloor);

  // Session State
  const [sessions, setSessions] = useState<SurveySession[]>([]);
  const [activeSession, setActiveSession] = useState<SurveySession | null>(null);
  const [sessionName, setSessionName] = useState<string>('Campus Floor Survey');
  const [pingTarget, setPingTarget] = useState<string>('auto');
  const [defaultGateway, setDefaultGateway] = useState<string>('Detecting...');

  // Active Placement Pin
  const [selectedCoord, setSelectedCoord] = useState<{ x: number; y: number } | null>(null);
  const [pointNote, setPointNote] = useState<string>('');

  // Live Telemetry
  const [liveWifi, setLiveWifi] = useState<LiveWifiStatus | null>(null);
  const [isQueryingWifi, setIsQueryingWifi] = useState<boolean>(false);
  const [isCapturing, setIsCapturing] = useState<boolean>(false);

  // Analysis State
  const [analysisResult, setAnalysisResult] = useState<SurveyAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [selectedPoint, setSelectedPoint] = useState<SurveyMeasurement | null>(null);

  // Layer toggles
  const [showRooms, setShowRooms] = useState<boolean>(true);
  const [showSurveyPoints, setShowSurveyPoints] = useState<boolean>(true);
  const [showDetectedDeadZones, setShowDetectedDeadZones] = useState<boolean>(true);

  // Status/Alert message
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);

  const floorWidth = 80;
  const floorHeight = 50;

  // Sync floor from props or fetch default
  useEffect(() => {
    if (currentFloor) {
      setActiveFloor(currentFloor);
    } else {
      api.getFloor(1).then((f) => setActiveFloor(f)).catch(console.error);
    }
  }, [currentFloor]);

  // Initial load
  useEffect(() => {
    loadGateway();
    fetchLiveWifi();
    loadSessions();
  }, [activeFloor?.id]);

  const loadGateway = async () => {
    try {
      const gw = await api.getDefaultGateway();
      setDefaultGateway(gw.default_gateway);
    } catch {
      setDefaultGateway('192.168.1.1 (fallback)');
    }
  };

  const loadSessions = async () => {
    if (!activeFloor) return;
    try {
      const list = await api.getSurveySessions(activeFloor.id);
      setSessions(list);
      if (list.length > 0) {
        setActiveSession(list[0]);
      } else {
        createNewSession(`Survey - ${activeFloor.name}`);
      }
    } catch (err) {
      console.error('Failed to load survey sessions:', err);
    }
  };

  const createNewSession = async (customName?: string) => {
    if (!activeFloor) return;
    const name = customName || sessionName || `Survey Session ${new Date().toLocaleTimeString()}`;
    try {
      const newSess = await api.createSurveySession({
        name,
        building_id: activeFloor.building_id,
        floor_id: activeFloor.id,
        ping_target: pingTarget,
        floorplan_width_m: floorWidth,
        floorplan_height_m: floorHeight,
      });
      setSessions([newSess, ...sessions]);
      setActiveSession(newSess);
      setAnalysisResult(null);
      setStatusMessage({ type: 'success', text: `Created survey session: "${newSess.name}"` });
    } catch (err) {
      console.error('Failed to create survey session:', err);
      setStatusMessage({ type: 'error', text: 'Failed to create new survey session.' });
    }
  };

  const fetchLiveWifi = async () => {
    setIsQueryingWifi(true);
    try {
      const data = await api.getLiveWifi(pingTarget);
      setLiveWifi(data);
    } catch (err) {
      console.error('Failed to query Windows Wi-Fi telemetry:', err);
    } finally {
      setIsQueryingWifi(false);
    }
  };

  // Find room containing coordinate
  const getRoomAtCoord = (x: number, y: number): Room | undefined => {
    return activeFloor?.rooms?.find(
      (r) => x >= r.x1 && x <= r.x2 && y >= r.y1 && y <= r.y2
    );
  };

  // Floorplan coordinate placement
  const setPinAtCoordinates = (x: number, y: number) => {
    const clampedX = Math.max(0.5, Math.min(floorWidth - 0.5, Math.round(x * 10) / 10));
    const clampedY = Math.max(0.5, Math.min(floorHeight - 0.5, Math.round(y * 10) / 10));
    setSelectedCoord({ x: clampedX, y: clampedY });
    setSelectedPoint(null);

    const room = getRoomAtCoord(clampedX, clampedY);
    if (room && !pointNote) {
      setPointNote(room.name);
    }
  };

  // Handles click/pointer on SVG canvas
  const handleFloorplanClick = (e: React.MouseEvent<SVGSVGElement> | React.PointerEvent<SVGSVGElement>) => {
    e.preventDefault();
    e.stopPropagation();

    const svg = svgRef.current || e.currentTarget;
    const rect = svg.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const mappedX = (clickX / rect.width) * floorWidth;
    const mappedY = (clickY / rect.height) * floorHeight;

    setPinAtCoordinates(mappedX, mappedY);
  };

  const handleSelectRoomCenter = (room: Room) => {
    const cx = Math.round(((room.x1 + room.x2) / 2) * 10) / 10;
    const cy = Math.round(((room.y1 + room.y2) / 2) * 10) / 10;
    setSelectedCoord({ x: cx, y: cy });
    setPointNote(room.name);
    setSelectedPoint(null);
  };

  const handleCaptureMeasurement = async () => {
    if (!activeSession) {
      setStatusMessage({ type: 'error', text: 'Please start or select a survey session first.' });
      return;
    }
    if (!selectedCoord) {
      setStatusMessage({
        type: 'error',
        text: 'Please click on the digital floorplan to choose your physical location first.',
      });
      return;
    }

    setIsCapturing(true);
    setStatusMessage(null);
    try {
      const newMeas = await api.captureSurveyMeasurement(activeSession.id, {
        x: selectedCoord.x,
        y: selectedCoord.y,
        notes: pointNote || undefined,
        target_ip: pingTarget,
      });

      const updatedMeasurements = [newMeas, ...(activeSession.measurements || [])];
      const updatedSession = { ...activeSession, measurements: updatedMeasurements };
      setActiveSession(updatedSession);
      setSessions(sessions.map((s) => (s.id === updatedSession.id ? updatedSession : s)));

      await fetchLiveWifi();

      setStatusMessage({
        type: 'success',
        text: `Captured Point #${newMeas.id} at (${newMeas.x}m, ${newMeas.y}m) | Signal: ${newMeas.signal_value ?? 'N/A'}${newMeas.signal_unit} | Latency: ${newMeas.latency_ms?.toFixed(1) ?? 'N/A'}ms`,
      });

      setPointNote('');
    } catch (err: any) {
      console.error('Failed to capture survey measurement:', err);
      setStatusMessage({
        type: 'error',
        text: err?.response?.data?.detail || 'Failed to capture live measurement from Windows adapter.',
      });
    } finally {
      setIsCapturing(false);
    }
  };

  const handleClearMeasurements = async () => {
    if (!activeSession) return;
    if (!window.confirm('Are you sure you want to clear all survey points in this session?')) return;

    try {
      await api.clearSurveyMeasurements(activeSession.id);
      const updatedSession = { ...activeSession, measurements: [] };
      setActiveSession(updatedSession);
      setSessions(sessions.map((s) => (s.id === updatedSession.id ? updatedSession : s)));
      setAnalysisResult(null);
      setSelectedPoint(null);
      setStatusMessage({ type: 'info', text: 'All survey points cleared for this session.' });
    } catch (err) {
      console.error('Failed to clear measurements:', err);
    }
  };

  const handleAnalyzeSurvey = async () => {
    if (!activeSession) return;
    if (!activeSession.measurements || activeSession.measurements.length === 0) {
      setStatusMessage({
        type: 'error',
        text: 'Cannot run dead-zone detection without survey measurements. Capture at least 1 point.',
      });
      return;
    }

    setIsAnalyzing(true);
    setStatusMessage(null);
    try {
      const res = await api.analyzeSurveySession(activeSession.id);
      setAnalysisResult(res);
      setStatusMessage({
        type: 'success',
        text: `Analysis complete! Detected ${res.dead_zones.length} dead zone(s) from ${res.total_survey_points} survey locations.`,
      });
    } catch (err: any) {
      console.error('Failed to analyze survey session:', err);
      setStatusMessage({
        type: 'error',
        text: err?.response?.data?.detail || 'Error running dead-zone detection on survey data.',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const measurementCount = activeSession?.measurements?.length || 0;
  const currentRoom = selectedCoord ? getRoomAtCoord(selectedCoord.x, selectedCoord.y) : undefined;

  return (
    <div className="space-y-6">
      {/* 1. Header & Operating Mode Indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
              <Radio className="w-3.5 h-3.5 mr-1.5 animate-pulse text-amber-400" />
              REAL COLLEGE SURVEY MODE
            </span>
            <span className="text-xs text-slate-400 font-mono">
              [is_synthetic: false | Windows WLAN API &amp; Netsh]
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Physical Campus Walkthrough Survey
          </h1>
          <p className="text-xs text-slate-400 max-w-3xl">
            Collect authentic local Wi-Fi measurements with your laptop. Walk to physical locations in your college
            building, mark your coordinate on the floorplan, and capture telemetry from Windows network interfaces.
            All captured data flows into the AI dead-zone detection &amp; prediction pipeline.
          </p>
        </div>

        {/* Action Quick Links */}
        <div className="flex flex-wrap items-center gap-2">
          {activeSession && (
            <a
              href={api.exportSurveyCsvUrl(activeSession.id)}
              download={`survey_session_${activeSession.id}.csv`}
              className="inline-flex items-center px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-all shadow-sm cursor-pointer"
              title="Export captured real measurements to CSV"
            >
              <Download className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
              Export Session CSV
            </a>
          )}
          <a
            href={api.sampleSurveyCsvUrl()}
            download="sample_real_survey_template.csv"
            className="inline-flex items-center px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold transition-all shadow-sm cursor-pointer"
            title="Download sample real-world survey CSV template"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            Sample CSV Template
          </a>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          className={`px-4 py-3 rounded-xl border text-xs font-medium flex items-center justify-between ${
            statusMessage.type === 'success'
              ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-200'
              : statusMessage.type === 'error'
              ? 'bg-rose-950/60 border-rose-800/80 text-rose-200'
              : 'bg-blue-950/60 border-blue-800/80 text-blue-200'
          }`}
        >
          <div className="flex items-center space-x-2">
            {statusMessage.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
            {statusMessage.type === 'error' && <XCircle className="w-4 h-4 text-rose-400 shrink-0" />}
            {statusMessage.type === 'info' && <Info className="w-4 h-4 text-blue-400 shrink-0" />}
            <span>{statusMessage.text}</span>
          </div>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-slate-400 hover:text-white text-xs px-2 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Top Controls: Floor, Session & Gateway Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Floor Selection */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Floor &amp; Building</span>
            <span className="text-xs font-semibold text-indigo-400">
              {activeFloor?.name ?? 'Floor 1'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={activeFloor?.id || 1}
              onChange={(e) => {
                const id = Number(e.target.value);
                if (onFloorChange) onFloorChange(id);
                api.getFloor(id).then((f) => setActiveFloor(f)).catch(console.error);
              }}
              className="flex-1 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {buildings.length > 0 ? (
                buildings.flatMap((b) =>
                  b.floors.map((f) => (
                    <option key={f.id} value={f.id}>
                      {b.name} - {f.name}
                    </option>
                  ))
                )
              ) : (
                <option value={1}>CSE Department Academic Block - Floor 1</option>
              )}
            </select>
          </div>
          <div className="text-[11px] text-slate-400">
            Dimensions: {floorWidth}m x {floorHeight}m (Digital Canvas Calibrated)
          </div>
        </div>

        {/* Survey Session Picker */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Survey Session</span>
            <span className="text-xs font-mono font-bold text-amber-400">
              {measurementCount} Point{measurementCount !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={activeSession?.id || ''}
              onChange={(e) => {
                const found = sessions.find((s) => s.id === Number(e.target.value));
                if (found) {
                  setActiveSession(found);
                  setAnalysisResult(null);
                }
              }}
              className="flex-1 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  #{s.id} - {s.name} ({s.measurements?.length || 0} pts)
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                const name = prompt('Enter new survey session title:', `Survey ${new Date().toLocaleDateString()}`);
                if (name) createNewSession(name);
              }}
              className="p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-all cursor-pointer"
              title="Start New Survey Session"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Status: {activeSession?.status || 'IN_PROGRESS'}</span>
            {measurementCount > 0 && (
              <button
                onClick={handleClearMeasurements}
                className="text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1 cursor-pointer"
              >
                <Trash2 className="w-3 h-3" /> Clear Points
              </button>
            )}
          </div>
        </div>

        {/* Ping / Gateway Settings */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Network Ping Target</span>
            <span className="text-xs font-mono text-emerald-400">
              GW: {defaultGateway}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={pingTarget}
              onChange={(e) => setPingTarget(e.target.value)}
              placeholder="auto (Default Gateway) or 192.168.1.1"
              className="flex-1 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={fetchLiveWifi}
              disabled={isQueryingWifi}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-all cursor-pointer"
              title="Refresh Live Wi-Fi & Ping"
            >
              <RefreshCw className={`w-4 h-4 ${isQueryingWifi ? 'animate-spin text-indigo-400' : ''}`} />
            </button>
          </div>
          <div className="text-[11px] text-slate-400">
            Pinging the local gateway tests Wi-Fi link latency, bypassing internet congestion.
          </div>
        </div>
      </div>

      {/* 3. Live Hardware Telemetry Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 p-5 rounded-2xl shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Wifi className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-slate-400 font-medium">Windows WLAN Adapter Telemetry</div>
              <div className="text-base font-bold text-white flex items-center gap-2">
                {liveWifi?.connected ? (
                  <>
                    <span>SSID: <span className="text-indigo-300 font-mono">{liveWifi.ssid || 'Connected'}</span></span>
                    <span className="text-xs font-mono text-slate-400">({liveWifi.bssid || 'BSSID'})</span>
                  </>
                ) : (
                  <span className="text-rose-400">Wi-Fi Disconnected</span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={fetchLiveWifi}
            disabled={isQueryingWifi}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold self-start md:self-auto cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isQueryingWifi ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Poll Adapter</span>
          </button>
        </div>

        {/* Real Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-4">
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Signal Quality</div>
            <div className="text-lg font-black text-white mt-0.5">
              {liveWifi?.signal_percent !== null && liveWifi?.signal_percent !== undefined
                ? `${liveWifi.signal_percent}%`
                : 'N/A'}
            </div>
            <div className="text-[10px] text-indigo-400">Native Windows API</div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">RSSI</div>
            <div className="text-lg font-black text-emerald-400 mt-0.5">
              {liveWifi?.rssi_dbm !== null && liveWifi?.rssi_dbm !== undefined
                ? `${liveWifi.rssi_dbm} dBm`
                : 'N/A'}
            </div>
            <div className="text-[10px] text-slate-400">
              {liveWifi?.is_rssi_estimated ? 'Est. via (Signal/2)-100' : 'Hardware Measured'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Channel / Band</div>
            <div className="text-lg font-black text-white mt-0.5">
              {liveWifi?.channel ? `Ch ${liveWifi.channel}` : 'N/A'}
            </div>
            <div className="text-[10px] text-purple-400">{liveWifi?.band || 'Unknown Band'}</div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Radio Standard</div>
            <div className="text-sm font-bold text-white mt-1 truncate" title={liveWifi?.radio_type || 'Unknown'}>
              {liveWifi?.radio_type || '802.11'}
            </div>
            <div className="text-[10px] text-slate-400">
              {liveWifi?.link_speed_mbps ? `${liveWifi.link_speed_mbps} Mbps` : 'Physical Layer'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Link Latency</div>
            <div className="text-lg font-black text-amber-400 mt-0.5">
              {liveWifi?.latency_ms !== null && liveWifi?.latency_ms !== undefined
                ? `${liveWifi.latency_ms.toFixed(1)} ms`
                : 'N/A'}
            </div>
            <div className="text-[10px] text-slate-400 truncate" title={liveWifi?.ping_target || 'Gateway'}>
              Target: {liveWifi?.ping_target || 'Gateway'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Packet Loss</div>
            <div className="text-lg font-black text-sky-400 mt-0.5">
              {liveWifi?.packet_loss_percent !== null && liveWifi?.packet_loss_percent !== undefined
                ? `${liveWifi.packet_loss_percent}%`
                : '0%'}
            </div>
            <div className="text-[10px] text-slate-400">ICMP Echo Reply</div>
          </div>
        </div>
      </div>

      {/* 4. Floorplan Survey Canvas & Capture Control */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left: Map Area (3 cols) */}
        <div className="lg:col-span-3 space-y-3">
          {/* Layer toggles & Map Toolbar */}
          <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs">
            <div className="flex items-center space-x-2 text-slate-300 font-semibold">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Map Overlay:</span>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setShowSurveyPoints(!showSurveyPoints)}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  showSurveyPoints
                    ? 'bg-amber-600 text-white shadow-sm shadow-amber-900/50'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                Survey Points ({measurementCount})
              </button>
              <button
                onClick={() => setShowDetectedDeadZones(!showDetectedDeadZones)}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  showDetectedDeadZones
                    ? 'bg-rose-600 text-white shadow-sm shadow-rose-900/50'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                Detected Dead Zones ({analysisResult?.dead_zones?.length || 0})
              </button>
              <button
                onClick={() => setShowRooms(!showRooms)}
                className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  showRooms ? 'bg-slate-700 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                Architectural Rooms
              </button>
            </div>
          </div>

          {/* Quick-Pick Location Presets */}
          {activeFloor?.rooms && activeFloor.rooms.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800/80 px-4 py-2.5 rounded-xl text-xs space-y-1.5">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Crosshair className="w-3.5 h-3.5 text-indigo-400" />
                <span>Quick-Pin Locations (Click room to position target pin):</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {activeFloor.rooms.map((r) => {
                  const isCurrent = currentRoom?.id === r.id;
                  return (
                    <button
                      key={`room-chip-${r.id}`}
                      onClick={() => handleSelectRoomCenter(r)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all cursor-pointer ${
                        isCurrent
                          ? 'bg-indigo-600 text-white border-indigo-400 shadow-sm shadow-indigo-600/40'
                          : 'bg-slate-950/80 text-slate-300 border-slate-700/80 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      {r.name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Density Warning Banner if < 4 points */}
          {measurementCount < 4 && (
            <div className="flex items-center space-x-3 px-4 py-3 bg-amber-950/40 border border-amber-800/60 rounded-xl text-amber-200 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <div>
                <span className="font-bold">Low Survey Density ({measurementCount}/4 points captured): </span>
                <span>
                  For reliable spatial clustering and dead-zone boundary estimation, we recommend marking and capturing
                  at least 4-8 distinct locations across the floor.
                </span>
              </div>
            </div>
          )}

          {/* Interactive SVG Floorplan Canvas */}
          <div
            className="relative w-full aspect-[80/50] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl p-2 flex items-center justify-center select-none"
            style={{ cursor: 'crosshair', userSelect: 'none' }}
            onDragStart={(e) => e.preventDefault()}
          >
            <svg
              ref={svgRef}
              viewBox={`0 0 ${floorWidth} ${floorHeight}`}
              className="w-full h-full select-none"
              style={{
                maxHeight: '640px',
                cursor: 'crosshair',
                userSelect: 'none',
                touchAction: 'none',
              }}
              onPointerDown={handleFloorplanClick}
              onClick={handleFloorplanClick}
              onDragStart={(e) => e.preventDefault()}
            >
              <defs>
                {/* Dead zone hatched pattern */}
                <pattern
                  id="surveyDeadZoneHatch"
                  width="4"
                  height="4"
                  patternTransform="rotate(45 0 0)"
                  patternUnits="userSpaceOnUse"
                >
                  <line x1="0" y1="0" x2="0" y2="4" stroke="#f43f5e" strokeWidth="1.2" opacity="0.7" />
                </pattern>
              </defs>

              {/* 0. FULL-SURFACE CLICKABLE BACKGROUND PLATE */}
              <rect
                x="0"
                y="0"
                width={floorWidth}
                height={floorHeight}
                fill="#090d16"
                style={{ cursor: 'crosshair', pointerEvents: 'all' }}
              />

              {/* 1. ROOMS LAYER */}
              {showRooms &&
                activeFloor?.rooms?.map((room) => {
                  const rw = room.x2 - room.x1;
                  const rh = room.y2 - room.y1;
                  return (
                    <g key={`room-${room.id}`} style={{ pointerEvents: 'all' }}>
                      <rect
                        x={room.x1}
                        y={room.y1}
                        width={rw}
                        height={rh}
                        fill={room.room_type === 'corridor' ? '#1e293b' : '#0f172a'}
                        stroke="#334155"
                        strokeWidth="0.4"
                        opacity="0.9"
                        style={{ cursor: 'crosshair', pointerEvents: 'all' }}
                      />
                      <text
                        x={room.x1 + rw / 2}
                        y={room.y1 + rh / 2 - 0.5}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#94a3b8"
                        fontSize="1.8"
                        fontWeight="600"
                        style={{ pointerEvents: 'none' }}
                        className="uppercase tracking-wider select-none"
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
                        style={{ pointerEvents: 'none' }}
                        className="select-none"
                      >
                        {rw.toFixed(0)}m × {rh.toFixed(0)}m
                      </text>
                    </g>
                  );
                })}

              {/* 2. WALLS LAYER */}
              {activeFloor?.walls?.map((wall) => (
                <line
                  key={`wall-${wall.id}`}
                  x1={wall.x1}
                  y1={wall.y1}
                  x2={wall.x2}
                  y2={wall.y2}
                  stroke="#64748b"
                  strokeWidth="0.8"
                  strokeLinecap="round"
                  style={{ pointerEvents: 'none' }}
                />
              ))}

              {/* 3. ACCESS POINTS HALOS (IF KNOWN) */}
              {activeFloor?.access_points?.map((ap) => (
                <g key={`ap-${ap.id}`} style={{ pointerEvents: 'none' }}>
                  <circle
                    cx={ap.x}
                    cy={ap.y}
                    r="15"
                    fill="#3b82f6"
                    opacity="0.06"
                  />
                  <circle
                    cx={ap.x}
                    cy={ap.y}
                    r="1.4"
                    fill="#2563eb"
                    stroke="#ffffff"
                    strokeWidth="0.4"
                  />
                  <text
                    x={ap.x}
                    y={ap.y + 2.5}
                    textAnchor="middle"
                    fill="#60a5fa"
                    fontSize="1.1"
                    fontWeight="bold"
                  >
                    {ap.name}
                  </text>
                </g>
              ))}

              {/* 4. DETECTED DEAD ZONES FROM REAL SURVEY */}
              {showDetectedDeadZones &&
                analysisResult?.dead_zones?.map((dz) => {
                  const bb = dz.bounding_box;
                  const bw = bb.max_x - bb.min_x;
                  const bh = bb.max_y - bb.min_y;
                  return (
                    <g
                      key={`survey-dz-${dz.id}`}
                      style={{ cursor: 'pointer', pointerEvents: 'all' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onNavigateToDeadZones) onNavigateToDeadZones(dz);
                      }}
                    >
                      <rect
                        x={bb.min_x}
                        y={bb.min_y}
                        width={bw}
                        height={bh}
                        fill="url(#surveyDeadZoneHatch)"
                        stroke="#f43f5e"
                        strokeWidth="0.8"
                        rx="1"
                        opacity="0.9"
                      />
                      <text
                        x={dz.center_x}
                        y={dz.center_y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#f43f5e"
                        fontSize="1.6"
                        fontWeight="bold"
                        style={{ pointerEvents: 'none' }}
                      >
                        {dz.name}
                      </text>
                    </g>
                  );
                })}

              {/* 5. CAPTURED SURVEY POINTS */}
              {showSurveyPoints &&
                activeSession?.measurements?.map((m, idx) => {
                  let fill = '#10b981'; // GOOD
                  if (m.quality_category === 'MODERATE') fill = '#f59e0b';
                  if (m.quality_category === 'POOR') fill = '#ef4444';

                  const isSelected = selectedPoint?.id === m.id;

                  return (
                    <g
                      key={`survey-meas-${m.id}`}
                      style={{ cursor: 'pointer', pointerEvents: 'all' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedPoint(m);
                      }}
                    >
                      <circle
                        cx={m.x}
                        cy={m.y}
                        r={isSelected ? 1.8 : 1.2}
                        fill={fill}
                        stroke="#ffffff"
                        strokeWidth={isSelected ? 0.6 : 0.3}
                        opacity={0.9}
                      />
                      <text
                        x={m.x}
                        y={m.y + 0.3}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#000000"
                        fontSize="0.9"
                        fontWeight="bold"
                        style={{ pointerEvents: 'none' }}
                      >
                        {idx + 1}
                      </text>
                    </g>
                  );
                })}

              {/* 6. ACTIVE PLACEMENT PIN (ANIMATED RETICLE) */}
              {selectedCoord && (
                <g style={{ pointerEvents: 'none' }} className="animate-pulse">
                  {/* Crosshair target lines */}
                  <line
                    x1={selectedCoord.x - 3}
                    y1={selectedCoord.y}
                    x2={selectedCoord.x + 3}
                    y2={selectedCoord.y}
                    stroke="#818cf8"
                    strokeWidth="0.4"
                  />
                  <line
                    x1={selectedCoord.x}
                    y1={selectedCoord.y - 3}
                    x2={selectedCoord.x}
                    y2={selectedCoord.y + 3}
                    stroke="#818cf8"
                    strokeWidth="0.4"
                  />
                  {/* Concentric rings */}
                  <circle
                    cx={selectedCoord.x}
                    cy={selectedCoord.y}
                    r="2.2"
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="0.5"
                    strokeDasharray="1,1"
                  />
                  <circle
                    cx={selectedCoord.x}
                    cy={selectedCoord.y}
                    r="1.0"
                    fill="#4f46e5"
                    stroke="#ffffff"
                    strokeWidth="0.4"
                  />
                  <circle
                    cx={selectedCoord.x}
                    cy={selectedCoord.y}
                    r="0.3"
                    fill="#ffffff"
                  />
                  {/* Coordinate Tag Badge */}
                  <rect
                    x={selectedCoord.x - 14}
                    y={selectedCoord.y - 4.5}
                    width="28"
                    height="3.2"
                    rx="0.8"
                    fill="#1e1b4b"
                    stroke="#818cf8"
                    strokeWidth="0.3"
                    opacity="0.95"
                  />
                  <text
                    x={selectedCoord.x}
                    y={selectedCoord.y - 2.5}
                    textAnchor="middle"
                    fill="#c7d2fe"
                    fontSize="1.3"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    PIN: X={selectedCoord.x}m, Y={selectedCoord.y}m
                  </text>
                </g>
              )}
            </svg>

            {/* Instruction badge inside map */}
            {!selectedCoord && (
              <div
                className="absolute top-4 left-4 bg-slate-900/95 border border-slate-700/80 px-3 py-2 rounded-lg text-[11px] text-slate-300 flex items-center space-x-2 backdrop-blur-sm shadow-lg select-none"
                style={{ pointerEvents: 'none' }}
              >
                <Crosshair className="w-3.5 h-3.5 text-indigo-400" />
                <span>Click anywhere on the floorplan to place your target survey pin</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Capture Action Panel (1 col) */}
        <div className="space-y-4">
          {/* Target Location Card */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-indigo-400" />
                Location Pin
              </span>
              {selectedCoord ? (
                <span className="text-xs font-mono font-bold text-emerald-400">
                  X: {selectedCoord.x}m | Y: {selectedCoord.y}m
                </span>
              ) : (
                <span className="text-xs text-amber-400 font-semibold italic">Click floorplan to pin</span>
              )}
            </div>

            {/* Location context */}
            {currentRoom && (
              <div className="bg-indigo-950/40 border border-indigo-500/30 px-3 py-2 rounded-lg text-xs text-indigo-200 flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span>Located inside: <strong className="text-white">{currentRoom.name}</strong></span>
              </div>
            )}

            {/* Coordinate Fine-Tuning */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <span className="flex items-center gap-1">
                  <Sliders className="w-3 h-3 text-slate-400" />
                  Fine-Tune Pin (Meters)
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-mono">X Axis (0–{floorWidth}m):</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max={floorWidth}
                    value={selectedCoord ? selectedCoord.x : ''}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val)) {
                        setPinAtCoordinates(val, selectedCoord?.y ?? 25.0);
                      }
                    }}
                    placeholder="e.g. 25.0"
                    className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase font-mono">Y Axis (0–{floorHeight}m):</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max={floorHeight}
                    value={selectedCoord ? selectedCoord.y : ''}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val)) {
                        setPinAtCoordinates(selectedCoord?.x ?? 40.0, val);
                      }
                    }}
                    placeholder="e.g. 15.0"
                    className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Location Notes / Room Identifier:
              </label>
              <input
                type="text"
                value={pointNote}
                onChange={(e) => setPointNote(e.target.value)}
                placeholder="e.g. Near window in Lab 101"
                className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Prominent Capture Button */}
            <button
              onClick={handleCaptureMeasurement}
              disabled={isCapturing || !selectedCoord}
              className={`w-full py-3.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center space-x-2 transition-all shadow-lg ${
                isCapturing
                  ? 'bg-indigo-700 text-slate-300 cursor-wait'
                  : !selectedCoord
                  ? 'bg-slate-800 text-slate-400 border border-slate-700 opacity-60 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/40 cursor-pointer animate-pulse'
              }`}
            >
              <Radio className={`w-4 h-4 ${isCapturing ? 'animate-spin' : ''}`} />
              <span>
                {isCapturing
                  ? 'Querying Windows Adapter & Ping...'
                  : selectedCoord
                  ? `Capture Measurement at (${selectedCoord.x}m, ${selectedCoord.y}m)`
                  : 'Select Location on Map to Enable'}
              </span>
            </button>

            <div className="text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1 text-slate-400">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Captures real Windows SSID, BSSID, RSSI</span>
              </div>
              <div className="flex items-center gap-1 text-slate-400">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pings local gateway for latency &amp; packet loss</span>
              </div>
            </div>
          </div>

          {/* AI Dead-Zone Detection on Real Data Button */}
          <div className="bg-gradient-to-br from-slate-900 to-indigo-950/60 border border-indigo-500/30 p-5 rounded-2xl shadow-xl space-y-3">
            <div className="flex items-center space-x-2 text-indigo-300">
              <Sparkles className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Dead-Zone Analysis Pipeline</h3>
            </div>
            <p className="text-xs text-slate-300">
              Run DBSCAN spatial clustering and multi-factor RF dead-zone scoring on your captured real survey points.
            </p>

            <button
              onClick={handleAnalyzeSurvey}
              disabled={isAnalyzing || measurementCount === 0}
              className={`w-full py-3 px-4 rounded-xl text-xs font-bold flex items-center justify-center space-x-2 transition-all ${
                isAnalyzing
                  ? 'bg-purple-800 text-slate-300 cursor-wait'
                  : measurementCount === 0
                  ? 'bg-slate-800 text-slate-400 opacity-60 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 cursor-pointer'
              }`}
            >
              <Activity className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>{isAnalyzing ? 'Running Detection...' : 'Run Dead-Zone Detection'}</span>
            </button>

            {analysisResult && (
              <div className="mt-3 p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1.5 text-xs">
                <div className="flex justify-between font-semibold">
                  <span className="text-slate-400">Dead Zones Found:</span>
                  <span className="text-rose-400 font-bold">{analysisResult.dead_zones.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Survey Points:</span>
                  <span className="text-slate-200">{analysisResult.total_survey_points}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg RSSI:</span>
                  <span className="text-emerald-400 font-mono">{analysisResult.average_rssi_dbm.toFixed(1)} dBm</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Latency:</span>
                  <span className="text-amber-400 font-mono">{analysisResult.average_latency_ms.toFixed(1)} ms</span>
                </div>
              </div>
            )}
          </div>

          {/* Selected Point Details Card */}
          {selectedPoint && (
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-xl space-y-2 text-xs">
              <div className="flex items-center justify-between font-bold text-slate-300 pb-2 border-b border-slate-800">
                <span>Point #{selectedPoint.id} Inspector</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    selectedPoint.quality_category === 'GOOD'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : selectedPoint.quality_category === 'MODERATE'
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-rose-500/20 text-rose-300'
                  }`}
                >
                  {selectedPoint.quality_category}
                </span>
              </div>
              <div className="space-y-1 text-slate-400">
                <div>Coord: <span className="text-slate-200">({selectedPoint.x}m, {selectedPoint.y}m)</span></div>
                <div>SSID: <span className="text-indigo-300 font-mono">{selectedPoint.ssid || 'N/A'}</span></div>
                <div>BSSID: <span className="text-slate-300 font-mono">{selectedPoint.bssid || 'N/A'}</span></div>
                <div>Signal: <span className="text-slate-200">{selectedPoint.signal_value}{selectedPoint.signal_unit}</span></div>
                <div>RSSI: <span className="text-emerald-400 font-mono">{selectedPoint.rssi_estimated_dbm} dBm</span></div>
                <div>Latency: <span className="text-amber-400 font-mono">{selectedPoint.latency_ms?.toFixed(1)} ms</span></div>
                <div>Loss: <span className="text-sky-400 font-mono">{selectedPoint.packet_loss_percent}%</span></div>
                {selectedPoint.notes && <div>Notes: <span className="text-slate-300 italic">{selectedPoint.notes}</span></div>}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5. Survey Measurements Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">
              Captured Survey Measurements ({measurementCount})
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Source: Windows Netsh WLAN Collector (Hardware Verified)
          </span>
        </div>

        {measurementCount === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No survey measurements captured yet in this session. Click on the floorplan to place a pin and capture your first point!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950/70 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">#</th>
                  <th className="px-4 py-3">Location (X, Y)</th>
                  <th className="px-4 py-3">SSID</th>
                  <th className="px-4 py-3">BSSID</th>
                  <th className="px-4 py-3">Signal (%)</th>
                  <th className="px-4 py-3">Est. RSSI</th>
                  <th className="px-4 py-3">Ch / Band</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3">Loss</th>
                  <th className="px-4 py-3">Quality</th>
                  <th className="px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {activeSession?.measurements?.map((m, idx) => (
                  <tr
                    key={`table-m-${m.id}`}
                    onClick={() => setSelectedPoint(m)}
                    className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                      selectedPoint?.id === m.id ? 'bg-indigo-950/40' : ''
                    }`}
                  >
                    <td className="px-4 py-2.5 font-bold text-slate-400">{idx + 1}</td>
                    <td className="px-4 py-2.5 font-semibold text-white">({m.x}m, {m.y}m)</td>
                    <td className="px-4 py-2.5 text-indigo-300 font-sans">{m.ssid || 'Unknown'}</td>
                    <td className="px-4 py-2.5 text-slate-400 text-[11px]">{m.bssid || 'N/A'}</td>
                    <td className="px-4 py-2.5 font-semibold">{m.signal_value ?? 'N/A'}%</td>
                    <td className="px-4 py-2.5 text-emerald-400">{m.rssi_estimated_dbm ?? 'N/A'} dBm</td>
                    <td className="px-4 py-2.5 text-purple-400">{m.channel ? `Ch ${m.channel}` : 'N/A'}</td>
                    <td className="px-4 py-2.5 text-amber-400">
                      {m.latency_ms !== null && m.latency_ms !== undefined ? `${m.latency_ms.toFixed(1)} ms` : 'N/A'}
                    </td>
                    <td className="px-4 py-2.5 text-sky-400">{m.packet_loss_percent ?? 0}%</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-sans font-bold ${
                          m.quality_category === 'GOOD'
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : m.quality_category === 'MODERATE'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-rose-500/20 text-rose-300'
                        }`}
                      >
                        {m.quality_category}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 text-[10px]">
                      {new Date(m.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
