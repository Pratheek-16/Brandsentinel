import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, AlertCircle, RefreshCw, Lock } from 'lucide-react';
import { api } from '../api';
import { AuditEventItem } from '../types';

export const AuditTrailScreen: React.FC = () => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadAudit = async () => {
    try {
      setLoading(true);
      const evs = await api.listAudit();
      setEvents(evs || []);
      const ver = await api.verifyAudit();
      setVerification(ver);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, []);

  const handleManualVerify = async () => {
    try {
      setLoading(true);
      const ver = await api.verifyAudit();
      setVerification(ver);
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <Lock className="w-5 h-5 text-blue-600" />
            <span>Cryptographic Hash-Chained Audit Log</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Every creation, review, suggestion acceptance, and approval is immutably linked via SHA-256 prev_hash chaining.
          </p>
        </div>

        <button
          onClick={handleManualVerify}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-md shadow-sm transition-colors flex items-center space-x-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Verify Integrity</span>
        </button>
      </div>

      {/* Verification Status Card */}
      {verification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-mono ${
            verification.is_valid
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-red-50 border-red-300 text-red-900'
          }`}
        >
          <div className="flex items-center space-x-2">
            {verification.is_valid ? (
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600" />
            )}
            <div>
              <div className="font-bold">
                {verification.is_valid ? 'Audit Chain Cryptographically Valid' : 'TAMPER DETECTED IN AUDIT LOG'}
              </div>
              <div className="text-[11px] opacity-80">
                Verified {verification.total_events} events from genesis to head block.
              </div>
            </div>
          </div>

          <div className="text-right text-[11px]">
            <div>Head Hash: {verification.details?.head_hash?.slice(0, 16)}...</div>
          </div>
        </div>
      )}

      {/* Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 uppercase">Chronological Ledger Events</span>
          <span className="text-xs text-slate-400 font-mono">{events.length} Recorded Events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-4 py-3 text-left">Event ID</th>
                <th className="px-4 py-3 text-left">Timestamp</th>
                <th className="px-4 py-3 text-left">Action</th>
                <th className="px-4 py-3 text-left">Entity</th>
                <th className="px-4 py-3 text-left">Actor</th>
                <th className="px-4 py-3 text-left">Previous Hash</th>
                <th className="px-4 py-3 text-left">Block Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-400 font-sans">
                    No governance actions recorded yet.
                  </td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-2.5 font-bold">#{ev.id}</td>
                    <td className="px-4 py-2.5 text-slate-500">{new Date(ev.ts).toLocaleString()}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200">
                        {ev.action}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      {ev.entity} #{ev.entity_id}
                    </td>
                    <td className="px-4 py-2.5">User #{ev.actor_id}</td>
                    <td className="px-4 py-2.5 text-slate-400 truncate max-w-[120px]" title={ev.prev_hash}>
                      {ev.prev_hash.slice(0, 12)}...
                    </td>
                    <td className="px-4 py-2.5 font-bold text-slate-900 truncate max-w-[120px]" title={ev.hash}>
                      {ev.hash.slice(0, 12)}...
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
