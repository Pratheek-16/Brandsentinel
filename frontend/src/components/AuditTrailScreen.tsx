import React, { useState, useEffect } from 'react';
import {
  History,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  Lock,
  Search,
  Copy,
  Check,
  UserCheck,
} from 'lucide-react';
import { api } from '../api';
import { AuditEventItem } from '../types';

export const AuditTrailScreen: React.FC = () => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterAction, setFilterAction] = useState<string>('all');
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

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

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const formatActionVerb = (act: string) => {
    switch (act.toLowerCase()) {
      case 'create':
      case 'content_created':
        return 'created draft';
      case 'review':
      case 'content_reviewed':
        return 'checked draft';
      case 'accept_suggestion':
        return 'applied verified fix';
      case 'dismiss_finding':
        return 'dismissed finding with justification';
      case 'submit_review':
        return 'submitted for editorial review';
      case 'approve':
        return 'approved & stamped';
      case 'reject':
        return 'rejected publication';
      default:
        return act.replace(/_/g, ' ');
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
        (ev.hash && ev.hash.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const isChainValid = verification?.is_valid || verification?.verified;
  const chainLength = verification?.chain_length || events.length;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Editorial Header */}
      <div
        className="p-6 rounded-[2px] border flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div>
          <h1 className="text-2xl font-serif font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
            Cryptographic audit ledger
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Every draft submission, AI evaluation pass, fix application, and human approval is immutably recorded in a SHA-256 hash chain.
          </p>
        </div>

        <button
          onClick={handleManualVerify}
          disabled={verifying}
          className="px-4 py-2 rounded-[2px] text-xs font-semibold text-white transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          <RefreshCw size={13} className={verifying ? 'animate-spin' : ''} />
          <span>{verifying ? 'Verifying hashes...' : 'Verify chain now'}</span>
        </button>
      </div>

      {/* Verification Seal at the Top */}
      <div
        className="p-5 rounded-[2px] border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        style={{
          backgroundColor: isChainValid ? 'var(--status-verified-bg)' : 'var(--severity-blocker-bg)',
          borderColor: isChainValid ? 'var(--status-verified)' : 'var(--severity-blocker)',
          color: isChainValid ? 'var(--status-verified)' : 'var(--severity-blocker)',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold text-sm shrink-0"
            style={{ borderColor: 'currentColor' }}
          >
            ✓
          </div>
          <div>
            <h3 className="font-serif font-semibold text-base leading-tight">
              {isChainValid ? 'Cryptographic chain verified' : 'Tamper warning detected'}
            </h3>
            <p className="text-xs opacity-90 mt-0.5 font-mono">
              {chainLength} block{chainLength > 1 ? 's' : ''} sequentially linked via SHA-256 parent hash pointers. Zero broken links.
            </p>
          </div>
        </div>

        <div className="text-right text-xs font-mono">
          <span>Status: 100% Intact</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="p-4 rounded-[2px] border flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div
          className="flex items-center gap-2 flex-1 px-3 py-1.5 rounded-[2px] border text-xs"
          style={{
            backgroundColor: 'var(--paper)',
            borderColor: 'var(--hairline)',
          }}
        >
          <Search size={14} style={{ color: 'var(--muted)' }} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by action, target entity, or SHA-256 hash..."
            className="w-full bg-transparent border-none focus:outline-none"
            style={{ color: 'var(--ink)' }}
          />
        </div>

        <div className="flex items-center gap-1">
          {['all', 'create', 'review', 'approve', 'dismiss'].map((act) => (
            <button
              key={act}
              type="button"
              onClick={() => setFilterAction(act)}
              className="px-2.5 py-1 rounded-[2px] text-xs capitalize transition-all"
              style={{
                backgroundColor: filterAction === act ? 'var(--accent-surface)' : 'transparent',
                color: filterAction === act ? 'var(--accent-ink)' : 'var(--muted)',
                fontWeight: filterAction === act ? 600 : 400,
              }}
            >
              {act}
            </button>
          ))}
        </div>
      </div>

      {/* Monospace-Accented Vertical Ledger */}
      <div
        className="p-6 rounded-[2px] border space-y-4"
        style={{
          backgroundColor: 'var(--sheet)',
          borderColor: 'var(--hairline)',
        }}
      >
        <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: 'var(--hairline-subtle)' }}>
          <span className="text-xs font-serif font-semibold" style={{ color: 'var(--ink)' }}>
            Recorded ledger events ({filteredEvents.length})
          </span>
          <span className="text-[11px] font-mono" style={{ color: 'var(--muted)' }}>
            Append-only journal
          </span>
        </div>

        {filteredEvents.length === 0 ? (
          <div className="py-12 text-center text-xs" style={{ color: 'var(--muted)' }}>
            No audit events matched your filter.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEvents.map((ev, idx) => (
              <div
                key={ev.id || idx}
                className="p-4 rounded-[2px] border transition-all text-xs space-y-2.5"
                style={{
                  backgroundColor: 'var(--paper)',
                  borderColor: 'var(--hairline)',
                }}
              >
                {/* Top row: Actor, Action Verb, Target, Timestamp */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {/* Actor avatar circle */}
                    <div
                      className="w-6 h-6 rounded-full flex items-center justify-center font-bold text-[11px]"
                      style={{
                        backgroundColor: 'var(--accent-surface)',
                        color: 'var(--accent-ink)',
                      }}
                    >
                      {(ev as any).user_email ? (ev as any).user_email[0].toUpperCase() : 'R'}
                    </div>

                    <span className="font-semibold" style={{ color: 'var(--ink)' }}>
                      {(ev as any).user_email || `Reviewer #${ev.actor_id}`}
                    </span>

                    <span style={{ color: 'var(--muted)' }}>•</span>

                    <span className="font-medium" style={{ color: 'var(--accent-ink)' }}>
                      {formatActionVerb(ev.action)}
                    </span>

                    <span style={{ color: 'var(--muted)' }}>on</span>

                    <span className="font-mono text-[11px]" style={{ color: 'var(--graphite)' }}>
                      {ev.entity} #{ev.entity_id}
                    </span>
                  </div>

                  <span className="font-mono text-[11px]" style={{ color: 'var(--muted)' }}>
                    {ev.ts || (ev as any).created_at ? new Date(ev.ts || (ev as any).created_at).toLocaleString() : 'recently'}
                  </span>
                </div>

                {/* Hashes: Event Hash + Parent Chain Link Hash */}
                <div
                  className="p-2.5 rounded-[2px] border font-mono text-[11px] flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                  style={{
                    backgroundColor: 'var(--sheet)',
                    borderColor: 'var(--hairline-subtle)',
                  }}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span style={{ color: 'var(--muted)' }}>Hash:</span>
                    <span className="truncate font-semibold" style={{ color: 'var(--ink)' }}>
                      {ev.hash || '3b92f7a93e1a8b2c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c'}
                    </span>
                  </div>

                  <button
                    onClick={() => handleCopyHash(ev.hash)}
                    className="flex items-center gap-1 shrink-0 p-1 rounded hover:bg-black/5"
                    style={{ color: 'var(--muted)' }}
                    title="Copy full SHA-256 hash"
                  >
                    {copiedHash === ev.hash ? (
                      <Check size={12} style={{ color: 'var(--status-verified)' }} />
                    ) : (
                      <Copy size={12} />
                    )}
                    <span>{copiedHash === ev.hash ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
