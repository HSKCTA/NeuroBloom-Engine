import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ChartData, ChartOptions
} from 'chart.js';
import { Activity, Eye, Brain, Wifi, ScanLine, FileText, Calculator } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface EEGPower { delta: number; theta: number; low_alpha: number; high_alpha: number; low_beta: number; high_beta: number; low_gamma: number; mid_gamma: number; }
interface VisionData { yaw: number; gaze: number; attention: number; hyperactivity_index: number; focus_ratio: number; blink_count: number; }
interface Packet { diagnosis: string; timestamp: number; eeg_power: EEGPower; vision: VisionData; metrics?: { tbr: number; cog_load: number; stress_index: number; }; }

const Dashboard: React.FC = () => {
  const [socketStatus, setSocketStatus] = useState("DISCONNECTED");
  const [activeTest, setActiveTest] = useState("ADHD"); // 'ADHD', 'DYSGRAPHIA', 'DYSCALCULIA'
  const [data, setData] = useState<Packet>({
    diagnosis: "INIT...", timestamp: 0,
    eeg_power: { delta: 0, theta: 0, low_alpha: 0, high_alpha: 0, low_beta: 0, high_beta: 0, low_gamma: 0, mid_gamma: 0 },
    vision: { yaw: 0, gaze: 0, attention: 0, hyperactivity_index: 0, focus_ratio: 0, blink_count: 0 },
    metrics: { tbr: 0, cog_load: 0, stress_index: 0 }
  });

  const [chartData, setChartData] = useState<ChartData<'line'>>({
    labels: [], datasets: [
      { label: 'Delta', data: [], borderColor: '#94a3b8', borderWidth: 1 },
      { label: 'Theta', data: [], borderColor: '#ef4444', borderWidth: 2 },
      { label: 'L-Beta', data: [], borderColor: '#84cc16', borderWidth: 2 },
      { label: 'M-Gamma', data: [], borderColor: '#3b82f6', borderWidth: 1 },
    ]
  });

  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => setSocketStatus("CONNECTED");
    ws.onclose = () => setSocketStatus("DISCONNECTED");
    ws.onmessage = (event) => {
      const response = JSON.parse(event.data);
      if (response.type === "DYSGRAPHIA_RESULT") { setIsScanning(false); setScanResult(response.diagnosis); return; }
      const packet = response as Packet;
      setData(packet);

      setChartData(prev => {
        const newLabels = [...(prev.labels as string[]), ""];
        const appendData = (idx: number, val: number) => {
          const nd = [...(prev.datasets[idx].data as number[]), val];
          if (nd.length > 50) nd.shift(); return nd;
        };
        if (newLabels.length > 50) newLabels.shift();
        return {
          labels: newLabels, datasets: [
            { ...prev.datasets[0], data: appendData(0, packet.eeg_power.delta) },
            { ...prev.datasets[1], data: appendData(1, packet.eeg_power.theta) },
            { ...prev.datasets[2], data: appendData(2, packet.eeg_power.low_beta) },
            { ...prev.datasets[3], data: appendData(3, packet.eeg_power.mid_gamma) },
          ]
        };
      });
    };
    return () => ws.close();
  }, []);

  const handleScan = () => { setIsScanning(true); setScanResult(null); const ws = new WebSocket('ws://localhost:8000/ws'); ws.onopen = () => { ws.send("SCAN_HANDWRITING"); ws.close(); }; };
  const statusColor = data.diagnosis === "DISTRACTED" ? "bg-red-600" : (data.diagnosis === "HIGH STRESS" ? "bg-orange-600" : "bg-emerald-600");
  const chartOptions: ChartOptions<'line'> = { animation: false, responsive: true, maintainAspectRatio: false, elements: { point: { radius: 0 }, line: { tension: 0.3 } }, scales: { y: { beginAtZero: true, grid: { color: '#334155' } }, x: { display: false } }, plugins: { legend: { display: true, labels: { color: '#cbd5e1' } } } };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6 font-mono">
      <header className="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
        <div><h1 className="text-2xl font-bold flex gap-2"><Brain className="text-blue-400" /> NeuroBloom</h1></div>
        <div className="flex gap-4">
          <div className="flex bg-slate-800 rounded p-1">
            <button onClick={() => setActiveTest("ADHD")} className={`px-4 py-1 text-xs font-bold rounded ${activeTest === "ADHD" ? "bg-blue-600" : "hover:bg-slate-700"}`}>ADHD</button>
            <button onClick={() => setActiveTest("DYSGRAPHIA")} className={`px-4 py-1 text-xs font-bold rounded ${activeTest === "DYSGRAPHIA" ? "bg-purple-600" : "hover:bg-slate-700"}`}>DYSGRAPHIA</button>
            <button onClick={() => setActiveTest("DYSCALCULIA")} className={`px-4 py-1 text-xs font-bold rounded ${activeTest === "DYSCALCULIA" ? "bg-orange-600" : "hover:bg-slate-700"}`}>DYSCALCULIA</button>
          </div>
          <div className={`px-4 py-2 rounded ${socketStatus === "CONNECTED" ? "bg-green-900" : "bg-red-900"} flex items-center gap-2 text-sm font-bold`}><Wifi size={16} /> {socketStatus}</div>
        </div>
      </header>

      {/* DYNAMIC DIAGNOSIS CARD */}
      <div className={`${statusColor} rounded-lg p-6 mb-8 text-center shadow-lg border border-white/10`}>
        <h2 className="text-xl opacity-80 mb-2 font-light">{activeTest} SCREENING ACTIVE</h2>
        <div className="text-5xl font-black tracking-widest uppercase">{data.diagnosis}</div>
        <div className="mt-4 flex justify-center gap-8 text-sm opacity-90">
          {activeTest === "ADHD" && <>
            <div className="bg-black/20 px-4 py-2 rounded">THETA/BETA RATIO: {data.metrics?.tbr?.toFixed(2)}</div>
            <div className="bg-black/20 px-4 py-2 rounded">HYPERACTIVITY: {data.vision.hyperactivity_index.toFixed(1)}</div>
          </>}
          {activeTest === "DYSCALCULIA" && <>
            <div className="bg-black/20 px-4 py-2 rounded">COGNITIVE LOAD: {data.metrics?.cog_load?.toFixed(2)}</div>
            <div className="bg-black/20 px-4 py-2 rounded">STRESS INDEX: {data.metrics?.stress_index?.toFixed(2)}</div>
          </>}
          <div className="bg-black/20 px-4 py-2 rounded">FOCUS RATIO: {data.vision.focus_ratio}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT PANEL: CHANGES BASED ON MODE */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-yellow-400">
            <Eye size={20} /> Biometric Markers
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-900 p-4 rounded text-center">
              <div className="text-slate-400 text-xs mb-1">HEAD STABILITY</div>
              <div className="text-xl font-bold text-white">{(100 - data.vision.hyperactivity_index).toFixed(0)}%</div>
            </div>
            <div className="bg-slate-900 p-4 rounded text-center">
              <div className="text-slate-400 text-xs mb-1">GAZE ENTROPY</div>
              <div className="text-xl font-bold text-white">{data.vision.gaze.toFixed(2)}</div>
            </div>
            <div className="bg-slate-900 p-4 rounded text-center">
              <div className="text-slate-400 text-xs mb-1">BLINK RATE</div>
              <div className="text-xl font-bold text-white">{data.vision.blink_count}</div>
            </div>
            <div className="bg-slate-900 p-4 rounded text-center">
              <div className="text-slate-400 text-xs mb-1">ATTENTION SPAN</div>
              <div className="text-xl font-bold text-white">{data.vision.focus_ratio}%</div>
            </div>
          </div>

          {activeTest === "DYSGRAPHIA" && (
            <div className="bg-slate-900/50 p-4 rounded border border-dashed border-slate-600">
              <h4 className="text-sm font-bold text-slate-300 mb-3 flex gap-2"><FileText size={16} /> Writing Analysis</h4>
              <button onClick={handleScan} disabled={isScanning} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded font-bold transition-all"><ScanLine /> {isScanning ? "SCANNING..." : "RUN OCR SCAN"}</button>
              {scanResult && <div className="mt-4 p-4 bg-slate-800 text-center font-black text-xl border border-white/20">{scanResult}</div>}
            </div>
          )}
        </div>

        {/* RIGHT PANEL: SPECTRUM */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-bold mb-4 flex gap-2 text-purple-400"><Activity size={20} /> Neuro-Spectral History</h3>
          <div className="h-64 relative"><Line data={chartData} options={chartOptions} /></div>
          <div className="mt-4 text-xs text-center text-slate-400">Displaying: Theta (ADHD), Beta (Stress), Gamma (Cognitive Load)</div>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;