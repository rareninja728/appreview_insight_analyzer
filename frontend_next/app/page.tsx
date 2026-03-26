"use client";

import React, { useState, useEffect } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line 
} from "recharts";
import { 
  Mail, Settings, Activity, Send, AlertTriangle, 
  CheckCircle2, Loader2, BarChart3, TrendingUp 
} from "lucide-react";

// ── Components ──────────────────────────────────────────────

const MetricCard = ({ title, value, trend, icon: Icon, color }: any) => (
  <div className="bg-[#161b22] border border-[#30363d] rounded-2xl p-6 shadow-lg hover:border-[#00d284] transition-all">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-xl bg-${color}/10 text-${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      {trend && (
        <span className={`px-2 py-1 rounded-lg text-xs font-bold ${trend.startsWith('+') ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          {trend}
        </span>
      )}
    </div>
    <p className="text-[#8b949e] text-sm font-semibold uppercase tracking-wider">{title}</p>
    <p className="text-3xl font-bold mt-1 text-white">{value}</p>
  </div>
);

const ThemeCard = ({ label, description, urgency }: any) => {
  const urgencyColors: any = {
    high: "border-red-500 bg-red-500/5",
    med: "border-yellow-500 bg-yellow-500/5",
    low: "border-[#00d284] bg-[#00d284]/5"
  };
  
  return (
    <div className={`border-l-4 rounded-xl p-4 mb-3 flex items-center justify-between ${urgencyColors[urgency || 'low']}`}>
      <div>
        <h4 className="text-white font-bold text-sm">{label}</h4>
        <p className="text-[#8b949e] text-xs mt-1">{description}</p>
      </div>
      <button className="p-2 hover:bg-white/5 rounded-lg text-[#8b949e] transition-all">
        <Activity className="w-4 h-4" />
      </button>
    </div>
  );
};

// ── Main Page ────────────────────────────────────────────────

export default function Dashboard() {
  const [email, setEmail] = useState("sugandhawankar123@gmail.com");
  const [weeks, setWeeks] = useState(1);
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [stats, setStats] = useState({ total: 0, rating: 0.0, weeks: 1 });
  const [reviewsData, setReviewsData] = useState([]);
  
  const API_BASE = "https://appreviewinsightanalyzer-production.up.railway.app";

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/reviews?limit=1000`);
      const data = await resp.json();
      if (data && data.length > 0) {
        setReviewsData(data);
        const avg = data.reduce((sum: number, r: any) => sum + (r.rating || 0), 0) / data.length;
        setStats({ total: data.length, rating: Number(avg.toFixed(1)), weeks: 1 });
      }
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    }
  };

  const runPipeline = async () => {
    setLoading(true);
    setPipelineStep(1);
    
    try {
      // Step 0: Sync Config (Weeks & Email)
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_address: email, weeks_back: weeks })
      });

      // Simulate steps for UI feel
      await new Promise(r => setTimeout(r, 1500));
      setPipelineStep(2);
      await new Promise(r => setTimeout(r, 2000));
      setPipelineStep(3);
      await new Promise(r => setTimeout(r, 1500));
      setPipelineStep(4);
      
      // Actual Pipeline Run
      const response = await fetch(`${API_BASE}/api/run_pipeline`, { 
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ email: email, weeks_back: weeks }) 
      });
      
      if (!response.ok) throw new Error("Pipeline Execution Failed");
      
      setPipelineStep(0);
      alert("✅ Weekly Pulse successfully sent!");
      // Optionally reload data here
    } catch (e) {
      alert("❌ Pipeline failed: " + (e as Error).message);
    } finally {
      setLoading(false);
      setPipelineStep(0);
    }
  };

  const deriveChartData = () => {
    if (!reviewsData || reviewsData.length === 0) {
      return [
        { name: "Mon", reviews: 0 }, { name: "Tue", reviews: 0 }, { name: "Wed", reviews: 0 },
        { name: "Thu", reviews: 0 }, { name: "Fri", reviews: 0 }, { name: "Sat", reviews: 0 }, { name: "Sun", reviews: 0 }
      ];
    }
    // Simple mock spread for UI demo if no dates available, 
    // or we could count by day if we had date strings in reviews.
    return [
      { name: "Mon", reviews: Math.floor(stats.total * 0.1) },
      { name: "Tue", reviews: Math.floor(stats.total * 0.15) },
      { name: "Wed", reviews: Math.floor(stats.total * 0.2) },
      { name: "Thu", reviews: Math.floor(stats.total * 0.12) },
      { name: "Fri", reviews: Math.floor(stats.total * 0.18) },
      { name: "Sat", reviews: Math.floor(stats.total * 0.1) },
      { name: "Sun", reviews: Math.floor(stats.total * 0.15) },
    ];
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#f0f6fc] font-outfit">
      
      {/* Header Banner */}
      <div className="h-64 bg-gradient-to-r from-[#00d284] via-[#00b0e4] to-[#2c9aff] relative flex items-center justify-center">
        <div className="text-center z-10">
          <h1 className="text-5xl font-black mb-3">INDmoney Weekly Pulse</h1>
          <p className="text-lg opacity-90 font-light tracking-wide italic font-body">Your weekly digest of user feedback insights</p>
        </div>
        <div className="absolute bottom-6 bg-white/10 backdrop-blur-md px-4 py-1.5 rounded-full text-xs font-bold border border-white/20 flex items-center gap-2">
          <span className="w-2.5 h-2.5 bg-white rounded-full animate-pulse shadow-[0_0_10px_white]"></span>
          LIVE UPDATES ACTIVE
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10 -mt-12 relative z-20">
        
        {/* Quick Actions Panel */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-3xl p-8 mb-10 shadow-2xl">
          <div className="flex flex-col md:flex-row items-center gap-6 justify-center max-w-4xl mx-auto">
            <div className="flex-grow w-full md:w-auto relative group">
              <Mail className="absolute left-5 top-1/2 -translate-y-1/2 text-[#8b949e] group-focus-within:text-[#00d284] transition-all" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Target Email Address"
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-2xl py-4 pl-14 pr-6 focus:outline-none focus:border-[#00d284] focus:ring-4 focus:ring-[#00d284]/10 transition-all text-lg font-medium"
              />
            </div>
            
            {/* Weeks Selection Dropdown */}
            <div className="w-full md:w-32 relative group">
               <select 
                  value={weeks} 
                  onChange={(e) => setWeeks(Number(e.target.value))}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-2xl py-4 px-4 focus:outline-none focus:border-[#00d284] focus:ring-4 focus:ring-[#00d284]/10 transition-all text-lg font-bold text-[#00d284] appearance-none cursor-pointer"
               >
                  <option value={1}>1 Week</option>
                  <option value={2}>2 Weeks</option>
                  <option value={3}>3 Weeks</option>
                  <option value={4}>4 Weeks</option>
                  <option value={8}>8 Weeks</option>
                  <option value={12}>12 Weeks</option>
               </select>
            </div>

            <button 
              onClick={runPipeline}
              disabled={loading}
              className="bg-[#00d284] text-black font-black px-10 py-4 rounded-2xl flex items-center gap-4 hover:scale-105 hover:shadow-[0_0_40px_rgba(0,210,132,0.4)] disabled:opacity-50 transition-all text-lg"
            >
              {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Send className="w-6 h-6" />}
              {loading ? "PROCESSING..." : "GENERATE PULSE"}
            </button>
          </div>
        </div>

        {/* Dash Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Visuals (2 Col) */}
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-[#161b22] border border-[#30363d] rounded-3xl p-8 h-[500px]">
              <div className="flex justify-between items-center mb-10">
                <div>
                  <span className="text-xs font-bold text-[#8b949e] uppercase tracking-widest">Growth Analytics</span>
                  <h2 className="text-2xl font-bold mt-1">Review Volume Trends</h2>
                </div>
                <div className="flex gap-2">
                  <div className="bg-[#0d1117] px-4 py-2 rounded-xl text-xs font-bold border border-[#30363d]">LAST {weeks} WEEKS</div>
                </div>
              </div>
              <div className="h-[340px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deriveChartData()}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#30363d" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{fill: '#8b949e', fontSize: 13, fontWeight: 'bold'}}
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{fill: '#8b949e', fontSize: 13}}
                    />
                    <Tooltip 
                      cursor={{fill: 'rgba(44, 154, 255, 0.1)'}}
                      contentStyle={{backgroundColor: '#0d1117', border: '1px solid #30363d', borderRadius: '12px'}}
                    />
                    <Bar 
                      dataKey="reviews" 
                      fill="#2c9aff" 
                      radius={[6, 6, 0, 0]} 
                      barSize={40}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               <MetricCard title="Total Reviews" value={stats.total.toString()} trend="+12.5%" icon={BarChart3} color="blue" />
               <MetricCard title="Avg Rating" value={`${stats.rating}/5`} trend="+0.1" icon={TrendingUp} color="green" />
            </div>
          </div>

          {/* Right Insights (1 Col) */}
          <div className="space-y-8">
            <div className="bg-[#161b22] border border-[#30363d] rounded-3xl p-8">
               <div className="flex items-center gap-3 mb-8">
                  <AlertTriangle className="text-yellow-500 w-5 h-5" />
                  <span className="text-xs font-black text-[#8b949e] uppercase tracking-widest">Key Insights</span>
               </div>
               <ThemeCard label="App Instability" description="High frequency of crashes on Android v14" urgency="high" />
               <ThemeCard label="Login UX" description="Users requesting biometric login fix" urgency="med" />
               <ThemeCard label="Dark Mode" description="Positive feedback on new dark mode" urgency="low" />
            </div>

            <div className="bg-gradient-to-br from-[#161b22] to-[#0d1117] border border-[#30363d] rounded-3xl p-8 relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-all transform rotate-12 scale-150">
                  <Settings className="w-24 h-24 text-white" />
               </div>
               <h3 className="text-xl font-black mb-2">Automate Weekly</h3>
               <p className="text-[#8b949e] text-sm leading-relaxed mb-6">Set your pulse reports on auto-pilot to be sent every Monday at 9:00 AM.</p>
               <button className="w-full bg-[#30363d] hover:bg-[#00d284] hover:text-black py-4 rounded-2xl font-black text-sm transition-all border border-white/5 uppercase tracking-widest">
                  Configure Settings
               </button>
            </div>
          </div>
        </div>
      </div>

      {/* Processing Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-[100] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-[#161b22] rounded-3xl p-10 border border-[#30363d] text-center shadow-3xl">
            <h3 className="text-3xl font-black mb-8 animate-pulse text-[#00d284]">PROCESSING PULSE...</h3>
            <div className="space-y-6 text-left mb-10">
              {[
                { id: 1, text: "Ingesting Review Stream" },
                { id: 2, text: "Groq LLM Semantic Analysis" },
                { id: 3, text: "Building Weekly Pulse Report" },
                { id: 4, text: "Delivering Insight Pulse" }
              ].map((step) => (
                <div key={step.id} className={`flex items-center gap-4 transition-all ${pipelineStep >= step.id ? 'opacity-100 scale-100 text-[#00d284]' : 'opacity-30 scale-95'}`}>
                  <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold font-mono ${pipelineStep >= step.id ? 'border-[#00d284] bg-[#00d284] text-black shadow-[0_0_20px_rgba(0,210,132,0.5)]' : 'border-[#30363d]'}`}>
                    {pipelineStep > step.id ? <CheckCircle2 className="w-6 h-6" /> : step.id}
                  </div>
                  <span className={`text-lg transition-all ${pipelineStep === step.id ? 'font-black translate-x-2' : 'font-semibold'}`}>
                    {step.text}
                  </span>
                </div>
              ))}
            </div>
            <div className="h-2 w-full bg-[#0d1117] rounded-full overflow-hidden border border-[#30363d]">
               <div className="h-full bg-gradient-to-r from-[#00d284] to-[#2c9aff] transition-all duration-700" style={{ width: `${(pipelineStep / 4) * 100}%` }}></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
