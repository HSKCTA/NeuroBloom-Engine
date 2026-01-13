// DysgraphiaUploader.tsx
import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';

// API Configuration (Points to his local Python server)
const API_URL = "http://localhost:8000/scan";

interface ScanResult {
    status: string;
    diagnosis: string;
    score: number;
}

const DysgraphiaUploader: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ScanResult | null>(null);
    const [preview, setPreview] = useState<string | null>(null);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Show preview
        setPreview(URL.createObjectURL(file));
        setLoading(true);
        setResult(null);

        // Create Form Data for API
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Upload failed", error);
            alert("Error connecting to Python Backend. Is dysgraphia_server.py running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md w-full bg-slate-900 border border-slate-700 rounded-xl p-6 text-white font-mono shadow-2xl">
            <div className="flex items-center gap-2 mb-6 border-b border-slate-700 pb-4">
                <FileText className="text-indigo-400" />
                <h2 className="text-xl font-bold">Dysgraphia Scanner</h2>
            </div>

            {/* UPLOAD AREA */}
            <div className="relative group cursor-pointer">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 z-10 cursor-pointer"
                />
                <div className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${preview ? "border-indigo-500 bg-slate-800" : "border-slate-600 hover:border-indigo-400 hover:bg-slate-800"
                    }`}>
                    {preview ? (
                        <img src={preview} alt="Preview" className="h-48 w-full object-cover rounded shadow-lg mx-auto" />
                    ) : (
                        <>
                            <Upload className="mx-auto h-12 w-12 text-slate-500 mb-2 group-hover:text-indigo-400" />
                            <p className="text-sm text-slate-400">Click or Drag Handwriting Image Here</p>
                        </>
                    )}
                </div>
            </div>

            {/* LOADING STATE */}
            {loading && (
                <div className="mt-6 flex items-center justify-center text-indigo-400 gap-2">
                    <Loader2 className="animate-spin" /> Analyzing Geometry...
                </div>
            )}

            {/* RESULTS DISPLAY */}
            {result && !loading && (
                <div className={`mt-6 p-5 rounded-lg border-l-4 animate-in fade-in slide-in-from-bottom-2 ${result.diagnosis.includes("HIGH") ? "bg-red-950/40 border-red-500" : "bg-emerald-950/40 border-emerald-500"
                    }`}>
                    <div className="flex justify-between items-start mb-2">
                        <span className={`text-xs font-bold uppercase tracking-wider ${result.diagnosis.includes("HIGH") ? "text-red-400" : "text-emerald-400"
                            }`}>
                            Diagnostic Result
                        </span>
                        {result.diagnosis.includes("HIGH") ? <AlertTriangle size={18} className="text-red-500" /> : <CheckCircle size={18} className="text-emerald-500" />}
                    </div>

                    <div className="text-3xl font-black mb-2">{result.diagnosis}</div>

                    <div className="flex justify-between text-xs opacity-70 mb-1">
                        <span>Risk Probability</span>
                        <span>{(result.score * 100).toFixed(1)}%</span>
                    </div>

                    {/* Probability Bar */}
                    <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-1000 ${result.diagnosis.includes("HIGH") ? "bg-red-500" : "bg-emerald-500"}`}
                            style={{ width: `${result.score * 100}%` }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default DysgraphiaUploader;