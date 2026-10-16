import React, { useState } from 'react';
import { PlayCircle, Upload, FileText, RefreshCw, Cpu, Sparkles, Radio, Layers, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import { Building, Floor, DeadZone } from '../types';
import { RealSurvey } from './RealSurvey';

interface SimulationControlProps {
  floorId: number;
  currentFloor: Floor | null;
  buildings: Building[];
  onSimulationComplete: () => void;
  onNavigateToDeadZones?: (dz: DeadZone) => void;
}

export const SimulationControl: React.FC<SimulationControlProps> = ({
  floorId,
  currentFloor,
  buildings,
  onSimulationComplete,
  onNavigateToDeadZones,
}) => {
  const [activeTab, setActiveTab] = useState<'simulation' | 'real-survey' | 'csv'>('simulation');

  // Virtual RF Simulation State
  const [scenario, setScenario] = useState('Laboratory Dead Zone');
  const [gridSpacing, setGridSpacing] = useState(2.0);
  const [includeNoise, setIncludeNoise] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isGeneratingDemo, setIsGeneratingDemo] = useState(false);
  const [simStatus, setSimStatus] = useState<string | null>(null);

  // CSV Import State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const scenarios = [
    'Laboratory Dead Zone',
    'Balanced Coverage',
    'Corridor Dead Zone',
    'Poor AP Placement',
  ];

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setSimStatus('Configuring scenario APs...');
    try {
      await api.applyScenario(floorId, scenario);
      setSimStatus('Simulating multi-wall path loss ray-tracing...');
      await api.runSimulation({
        floor_id: floorId,
        scenario_name: scenario,
        grid_spacing: gridSpacing,
        include_noise: includeNoise,
        save_to_db: true,
      });
      setSimStatus('Simulation complete! Updated dashboard and dead-zone clusters.');
      onSimulationComplete();
    } catch (err: any) {
      setSimStatus(`Error: ${err?.message || 'Simulation failed'}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleGenerateDemo = async () => {
    setIsGeneratingDemo(true);
    setSimStatus(`Executing one-click end-to-end pipeline for '${scenario}'...`);
    try {
      const res = await api.generateDemo(scenario);
      setSimStatus(`Demo environment ready! Measurements: ${res.measurements_count}, Dead Zones: ${res.dead_zones_count}, Accuracy: ${(res.ml_accuracy * 100).toFixed(1)}%`);
      onSimulationComplete();
    } catch (err: any) {
      setSimStatus(`Error: ${err?.message || 'Demo generation failed'}`);
    } finally {
      setIsGeneratingDemo(false);
    }
  };

  const handleUploadCSV = async () => {
    if (!csvFile) return;
    setIsUploading(true);
    setUploadStatus('Uploading and parsing field survey CSV...');
    try {
      const res = await api.uploadCSV(csvFile, floorId);
      setUploadStatus(`Success: ${res.message}. Detected ${res.dead_zones_detected} dead zones.`);
      onSimulationComplete();
    } catch (err: any) {
      setUploadStatus(`Upload error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const downloadSampleCSV = () => {
    const csvContent =
      'timestamp,floor,x,y,rssi,latency,packet_loss,throughput,ap_id\n' +
      '2026-10-04T10:00:00,1,10.5,8.2,-48.2,14.5,0.2,210.4,1\n' +
      '2026-10-04T10:00:05,1,12.0,15.4,-52.1,18.0,0.5,185.0,1\n' +
      '2026-10-04T10:00:10,1,38.5,35.0,-84.5,210.0,24.5,1.2,2\n' +
      '2026-10-04T10:00:15,1,42.0,38.0,-87.2,260.0,31.0,0.8,2\n' +
      '2026-10-04T10:00:20,1,45.0,42.0,-89.0,320.0,38.0,0.5,2\n' +
      '2026-10-04T10:00:25,1,68.0,39.0,-45.0,12.0,0.1,230.0,2\n';

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'sample_wifi_measurements.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
        <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider mb-1">
          <PlayCircle className="w-4 h-4" />
          <span>Testing Studio &bull; Synthetic Simulation &amp; Real Surveys</span>
        </div>
        <h1 className="text-xl font-extrabold text-white tracking-tight">
          Simulation &amp; Testing
        </h1>
        <p className="text-xs text-slate-400 max-w-2xl mt-1">
          Configure multi-wall COST-231 virtual RF propagation models, ingest external survey CSV datasets, or capture real-world laptop Wi-Fi measurements.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('simulation')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'simulation'
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>RF Simulation &amp; Scenarios</span>
        </button>

        <button
          onClick={() => setActiveTab('real-survey')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'real-survey'
              ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Real Laptop WLAN Survey</span>
        </button>

        <button
          onClick={() => setActiveTab('csv')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeTab === 'csv'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Upload className="w-3.5 h-3.5" />
          <span>CSV Dataset Import</span>
        </button>
      </div>

      {/* Tab 1: Virtual RF Simulation */}
      {activeTab === 'simulation' && (
        <div className="space-y-6 animate-in fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scenario Selection & Execution */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>Simulation Scenarios &amp; Parameters</span>
              </h3>

              <div className="space-y-3.5 text-xs">
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Predefined Scenario</label>
                  <select
                    value={scenario}
                    onChange={(e) => setScenario(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-200 font-semibold focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    {scenarios.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-slate-300 font-semibold block mb-1">
                    Sample Grid Spacing: {gridSpacing}m ({Math.round(80 / gridSpacing) * Math.round(50 / gridSpacing)} spatial points)
                  </label>
                  <input
                    type="range"
                    min="1.5"
                    max="4.0"
                    step="0.5"
                    value={gridSpacing}
                    onChange={(e) => setGridSpacing(parseFloat(e.target.value))}
                    className="w-full accent-indigo-500 cursor-pointer"
                  />
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <input
                    type="checkbox"
                    id="noiseToggle"
                    checked={includeNoise}
                    onChange={(e) => setIncludeNoise(e.target.checked)}
                    className="accent-indigo-500 cursor-pointer w-4 h-4 rounded"
                  />
                  <label htmlFor="noiseToggle" className="text-slate-300 font-medium cursor-pointer">
                    Include Shadowing &amp; Multi-Path Fading Noise (σ = 1.8 dB)
                  </label>
                </div>

                <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <button
                    onClick={handleRunSimulation}
                    disabled={isSimulating || isGeneratingDemo}
                    className="flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 transition-all cursor-pointer disabled:opacity-50"
                  >
                    {isSimulating ? <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" /> : <PlayCircle className="w-4 h-4 text-indigo-400" />}
                    <span>{isSimulating ? 'Simulating...' : 'Run Simulation'}</span>
                  </button>

                  <button
                    onClick={handleGenerateDemo}
                    disabled={isSimulating || isGeneratingDemo}
                    className="flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-50"
                  >
                    {isGeneratingDemo ? <RefreshCw className="w-4 h-4 animate-spin text-white" /> : <Sparkles className="w-4 h-4 text-amber-300" />}
                    <span>{isGeneratingDemo ? 'Synthesizing...' : 'Generate Demo Environment'}</span>
                  </button>
                </div>

                {simStatus && (
                  <p className="text-xs text-indigo-300 bg-indigo-950/40 p-2.5 rounded-lg border border-indigo-900/40 mt-2">
                    {simStatus}
                  </p>
                )}
              </div>
            </div>

            {/* Model Information Card */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 text-xs">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Simulation Methodology [SYNTHETIC BENCHMARK]</span>
              </h3>

              <p className="text-slate-300 leading-relaxed">
                The virtual engine computes radio frequency propagation based on the empirical <strong>COST-231 Multi-Wall Path Loss Model</strong>:
              </p>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-indigo-300 text-[11px]">
                PL(d) = PL₀ + 10 · n · log₁₀(d) + Σ (W_i · AF_i) + X_σ
              </div>

              <ul className="space-y-1.5 text-slate-400 list-disc list-inside">
                <li><strong className="text-slate-200">PL₀:</strong> Free space reference loss at 1 meter</li>
                <li><strong className="text-slate-200">n = 2.4:</strong> Indoor path loss exponent for campus buildings</li>
                <li><strong className="text-slate-200">AF_i:</strong> Concrete partition attenuation (15 dB per heavy wall)</li>
                <li><strong className="text-slate-200">X_σ:</strong> Log-normal shadow fading distribution</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Real Laptop WLAN Survey */}
      {activeTab === 'real-survey' && (
        <div className="space-y-4 animate-in fade-in">
          <RealSurvey
            currentFloor={currentFloor}
            buildings={buildings}
            onFloorChange={() => {}}
            onNavigateToDeadZones={onNavigateToDeadZones}
          />
        </div>
      )}

      {/* Tab 3: CSV Dataset Import */}
      {activeTab === 'csv' && (
        <div className="space-y-6 animate-in fade-in">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>External Walk-Test Survey CSV Ingestion</span>
              </h3>
              <button
                onClick={downloadSampleCSV}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Download Sample Template</span>
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Upload field measurements recorded using hardware survey tools or smartphone apps. Format: <code className="text-slate-300 bg-slate-950 px-1 py-0.5 rounded font-mono">timestamp, floor, x, y, rssi, latency, packet_loss, throughput, ap_id</code>.
            </p>

            <div className="space-y-3 text-xs max-w-xl">
              <div className="border-2 border-dashed border-slate-800 hover:border-slate-700 rounded-xl p-6 text-center bg-slate-950/50">
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
                  className="text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
                />
                {csvFile && (
                  <p className="text-xs text-emerald-400 font-semibold mt-2">
                    Selected file: {csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              <button
                onClick={handleUploadCSV}
                disabled={!csvFile || isUploading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/30 transition-all cursor-pointer disabled:opacity-50"
              >
                {isUploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                <span>{isUploading ? 'Ingesting Dataset...' : 'Upload & Detect Dead Zones'}</span>
              </button>

              {uploadStatus && (
                <p className="text-xs text-emerald-300 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-900/40">
                  {uploadStatus}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
