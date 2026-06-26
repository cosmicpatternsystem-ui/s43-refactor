import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [socketStatus, setSocketStatus] = useState('DISCONNECTED');

  useEffect(() => {
    const socket = io('http://127.0.0.1:5002', {
      transports: ["polling"],
      upgrade: false,
      forceNew: false
    });

    socket.on('connect', () => setSocketStatus('CONNECTED'));
    socket.on('disconnect', () => setSocketStatus('DISCONNECTED'));
    socket.on('arzplus_status_update', (payload) => {
      setData(payload);
    });

    return () => socket.disconnect();
  }, []);

  const getStatusColor = (status) => {
    if (status?.includes('BLOOD')) return 'bg-red-600';
    if (status?.includes('BULLISH')) return 'bg-green-600';
    return 'bg-blue-600';
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-slate-700 pb-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-blue-400">ASO-X INTELLIGENCE</h1>
          <p className="text-slate-400 text-sm">Global Market & Multi-Wallet Control</p>
        </div>
        <div className={`px-4 py-1 rounded-full text-xs font-bold ${socketStatus === 'CONNECTED' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
          SOCKET: {socketStatus}
        </div>
      </div>

      {data ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Market Status Card */}
          <div className={`col-span-full ${getStatusColor(data.market_status)} p-4 rounded-lg shadow-lg flex justify-between items-center animate-pulse`}>
            <span className="font-bold text-xl text-white">CURRENT PHASE: {data.market_status}</span>
            <span className="text-sm">Last Scan: {data.last_update}</span>
          </div>

          {/* Global Metrics */}
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl">
            <h3 className="text-slate-400 mb-4 uppercase tracking-wider text-xs font-bold">Global Assets</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-slate-300">Bitcoin</span>
                <span className="text-xl font-mono text-orange-400">${data.global_metrics.btc_price.toLocaleString()}</span>
              </div>
              <div className="flex justify-between border-t border-slate-700 pt-2">
                <span className="text-slate-300">Gold (Ounce)</span>
                <span className="text-xl font-mono text-yellow-500">${data.global_metrics.gold_price.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Wallets & Roles */}
          {data.wallets.map((wallet) => (
            <div key={wallet.id} className="bg-slate-800 p-6 rounded-xl border border-slate-700 hover:border-blue-500 transition-all">
              <div className="flex justify-between items-start mb-4">
                <span className="bg-blue-900/40 text-blue-300 px-2 py-1 rounded text-[10px] font-bold">{wallet.role}</span>
                <span className="text-green-400 text-xs">● {wallet.status}</span>
              </div>
              <h4 className="text-xl font-bold mb-1">{wallet.name}</h4>
              <p className="text-slate-500 text-xs">Liquidity Management System</p>
            </div>
          ))}

          {/* Logic & Strategy */}
          <div className="col-span-full bg-blue-900/20 border border-blue-500/30 p-4 rounded-lg">
            <h4 className="text-blue-400 font-bold mb-2">System Strategy:</h4>
            <p className="text-slate-300 text-sm">
              {data.market_status.includes('BLOOD') 
                ? "ACTION: Market is in heavy discount. Hunter wallet (W3) is authorized for quick entries. Anchor (W1) must hold."
                : "ACTION: Market is stable. Monitoring for volatility spikes. Maintain 70/30 profit ratio."}
            </p>
          </div>

        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-slate-400 italic">Waiting for Intelligence Data from Bridge...</p>
        </div>
      )}
    </div>
  );
}
