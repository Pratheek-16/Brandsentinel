import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, AlertCircle, RefreshCw, Lock, Filter, Search } from 'lucide-react';
import { api } from '../api';
import { AuditEventItem } from '../types';

export const AuditTrailScreen: React.FC = () => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [filterAction, setFilterAction] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadAudit = async () => {
    try {
      setLoading(true);
      const [evs, ver] = await Promise.all([
        api.listAudit().catch(() => []),
        api.verifyAudit().catch(() => null),
      ]);
      setEvents(evs || []);
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
      setVerifying(true);
      const ver = await api.verifyAudit();
      setVerification(ver);
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (filterAction !== 'all' && !ev.action.toLowerCase().includes(filterAction.toLowerCase())) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        ev.action.toLowerCase().includes(q) ||
        ev.entity.toLowerCase().includes(q) ||
        String(ev.entity_id).includes(q) ||
        ev.hash.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
            <Lock className="w-5 h-5 text-blue-600" />
            <span>Cryptographic Hash-Chained Audit Ledger</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Every creation, review, suggestion acceptance, dismissal, and approval decision is immutably chained via SHA-256 block hashing.
          </p>
        </div>

        <button
          onClick={handleManualVerify}
          disabled={verifying}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
          <span>{verifying ? 'Validating Hashes...' : 'Verify Cryptographic Chain'}</span>
        </button>
      </div>

      {/* Verification Status Card */}
      {verification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-mono shadow-2xs ${
            verification.is_valid || verification.verified
              ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
              : 'bg-red-50 border-red-300 text-red-950'
          }`}
        >
          <div className="flex items-center space-x-3">
            {verification.is_valid || verification.verified ? (
              <ShieldCheck className="w-6 h-6 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 shrink-0" />
            )}
            <div>
              <div className="font-bold text-sm">
                {verification.is_valid || verification.verified
                  ? 'Audit Chain Cryptographically Valid'
                  : 'TAMPER DETECTED: AUDIT CHAIN INTEGRITY COMPROMISED'}
              </div>
              <div className="text-[11px] opacity-80 mt-0.5">
                Verified {verification.chain_length || verification.total_events || events.length} events from genesis to head block with zero breaks.
              </div>
            </div>
          </div>

          <div className="text-right text-[11px] hidden sm:block">
            <div className="font-semibold text-slate-700">Head Block Hash:</div>
            <div className="truncate max-w-[180px] text-slate-500 font-mono">
              {verification.details?.head_hash || (events[0] ? events[0].hash : 'GENESIS')}
            </div>
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2 flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by action, entity ID, or hash..."
            className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono text-xs"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:outline-none font-semibold text-slate-700 text-xs"
          >
            <option value="all">All Actions</option>
            <option value="content">Content Events</option>
            <option value="approved">Approvals & Signatures</option>
            <option value="suggestion">Fixes & Replacements</option>
            <option value="dismiss">Dismissals</option>
            <option value="kb">Knowledge Base</option>
          </select>
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Chronological Audit Ledger
          </span>
          <span className="text-xs text-slate-400 font-mono">
            {filteredEvents.length} Events Displayed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Timestamp</th>
                <th className="px-4 py-3 text-left">Action</th>
                <th className="px-4 py-3 text-left">Entity</th>
                <th className="px-4 py-3 text-left">Actor</th>
                <th className="px-4 py-3 text-left">Prev Block Hash</th>
                <th className="px-4 py-3 text-left">Current Block Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-slate-400 font-sans">
                    No matching audit events found.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-900">#{ev.id}</td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      {new Date(ev.ts).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded font-bold bg-blue-50 text-blue-700 border border-blue-200 whitespace-nowrap">
                        {ev.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {ev.entity} #{ev.entity_id}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">User #{ev.actor_id}</td>
                    <td
                      className="px-4 py-3 text-slate-400 truncate max-w-[120px]"
                      title={ev.prev_hash}
                    >
                      {ev.prev_hash.slice(0, 10)}...
                    </td>
                    <td
                      className="px-4 py-3 font-bold text-slate-900 truncate max-w-[120px]"
                      title={ev.hash}
                    >
                      {ev.hash.slice(0, 10)}...
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
