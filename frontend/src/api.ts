import {
  User,
  WorkspaceInfoWithUsers,
  Finding,
  ClaimItem,
  VerifiedSuggestion,
  CommentItem,
  ContentItem,
  RuleItem,
  FactItem,
  TermItem,
  ClaimKBItem,
  AssetItem,
  KBVersionItem,
  AuditEventItem,
  ReviewResponse,
} from './types';

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : window.location.origin);

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<{ access_token: string; user: User }> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  getMe: async (): Promise<User> => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Session expired' }));
      throw new Error(err.detail || 'Session expired');
    }
    return res.json();
  },

  listWorkspaces: async (): Promise<WorkspaceInfoWithUsers[]> => {
    const res = await fetch(`${API_BASE}/auth/workspaces`);
    if (!res.ok) throw new Error('Failed to fetch workspaces');
    return res.json();
  },

  // Content & Drafts
  listContents: async (): Promise<ContentItem[]> => {
    const res = await fetch(`${API_BASE}/content/`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to list workspace drafts');
    return res.json();
  },

  createContent: async (data: {
    title: string;
    type: string;
    channel?: string;
    body: string;
  }): Promise<{ content_id: number; version_id: number; title: string; workspace_id: number }> => {
    const res = await fetch(`${API_BASE}/content/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Content creation failed' }));
      throw new Error(err.detail || 'Content creation failed');
    }
    return res.json();
  },

  uploadContent: async (formData: FormData): Promise<{ content_id: number; version_id: number; title: string }> => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}/content/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  getContent: async (contentId: number): Promise<ContentItem> => {
    const res = await fetch(`${API_BASE}/content/${contentId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch content' }));
      throw new Error(err.detail || 'Failed to fetch content');
    }
    return res.json();
  },

  // Review runs
  getReview: async (contentId: number): Promise<ReviewResponse> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/review`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch review' }));
      throw new Error(err.detail || 'Failed to fetch review');
    }
    return res.json();
  },

  reviewContent: async (contentId: number): Promise<ReviewResponse> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/review`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Review failed' }));
      throw new Error(err.detail || 'Review failed');
    }
    return res.json();
  },

  submitContent: async (
    contentId: number
  ): Promise<{ status: string; escalated: boolean; escalation_reason?: string; message: string }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/submit`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Submission failed' }));
      throw new Error(err.detail || 'Submission failed');
    }
    return res.json();
  },

  approveContent: async (
    contentId: number,
    decision: 'approved' | 'changes_requested' | 'rejected',
    reason?: string
  ): Promise<{ approval_id: number; decision: string; status: string; signature_hash: string }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ decision, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Approval action failed' }));
      throw new Error(err.detail || 'Approval action failed');
    }
    return res.json();
  },

  // Suggestions & Finding Actions (I-1)
  getSuggestions: async (
    contentId: number,
    findingId: number
  ): Promise<{ finding_id: number; original_text: string; suggestions: VerifiedSuggestion[] }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/suggestions`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to get suggestions');
    return res.json();
  },

  acceptSuggestion: async (
    contentId: number,
    findingId: number,
    replacementText: string
  ): Promise<{ message: string; version_no: number; text_body: string; finding_id: number; status: string }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/accept`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ custom_text: replacementText, replacement_text: replacementText }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to accept suggestion' }));
      throw new Error(err.detail || 'Failed to accept suggestion');
    }
    return res.json();
  },

  editFinding: async (
    contentId: number,
    findingId: number,
    replacementText: string
  ): Promise<{ message: string; version_no: number; text_body: string; finding_id: number; status: string }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/edit`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ custom_text: replacementText, replacement_text: replacementText }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to save edit' }));
      throw new Error(err.detail || 'Failed to save edit');
    }
    return res.json();
  },

  dismissFinding: async (
    contentId: number,
    findingId: number,
    reason: string
  ): Promise<{ message: string; finding_id: number; status: string }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/dismiss`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to dismiss finding' }));
      throw new Error(err.detail || 'Failed to dismiss finding');
    }
    return res.json();
  },

  // Claims Ledger
  getClaims: async (contentId: number): Promise<{ content_id: number; total_claims: number; claims: ClaimItem[] }> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/claims`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch claims ledger');
    return res.json();
  },

  // Comments
  getComments: async (contentId: number): Promise<CommentItem[]> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/comments`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch comments');
    return res.json();
  },

  addComment: async (
    contentId: number,
    body: string,
    findingId?: number,
    parentId?: number
  ): Promise<CommentItem> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/comments`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ body, finding_id: findingId, parent_id: parentId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to post comment' }));
      throw new Error(err.detail || 'Failed to post comment');
    }
    return res.json();
  },

  // Knowledge Base CRUD
  listRules: async (): Promise<RuleItem[]> => {
    const res = await fetch(`${API_BASE}/kb/rules`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  createRule: async (data: {
    code: string;
    category: string;
    text: string;
    severity_default: string;
    channels?: string[];
  }): Promise<RuleItem> => {
    const res = await fetch(`${API_BASE}/kb/rules`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create rule');
    return res.json();
  },

  deleteRule: async (id: number): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/kb/rules/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete rule');
    return res.json();
  },

  listFacts: async (): Promise<FactItem[]> => {
    const res = await fetch(`${API_BASE}/kb/facts`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch facts');
    return res.json();
  },

  createFact: async (data: {
    code: string;
    key: string;
    value: string;
    unit?: string;
    source?: string;
    valid_to?: string;
  }): Promise<FactItem> => {
    const res = await fetch(`${API_BASE}/kb/facts`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create fact');
    return res.json();
  },

  deleteFact: async (id: number): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/kb/facts/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete fact');
    return res.json();
  },

  listTerms: async (): Promise<TermItem[]> => {
    const res = await fetch(`${API_BASE}/kb/terms`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch terms');
    return res.json();
  },

  createTerm: async (data: {
    preferred: string;
    banned?: string[];
    case_rule?: string;
    notes?: string;
  }): Promise<TermItem> => {
    const res = await fetch(`${API_BASE}/kb/terms`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create term');
    return res.json();
  },

  deleteTerm: async (id: number): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/kb/terms/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete term');
    return res.json();
  },

  listClaimsKB: async (): Promise<ClaimKBItem[]> => {
    const res = await fetch(`${API_BASE}/kb/claims`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch claims KB');
    return res.json();
  },

  createClaimKB: async (data: {
    approved_text: string;
    evidence_ref?: string;
    required_disclaimer?: string;
    valid_to?: string;
  }): Promise<ClaimKBItem> => {
    const res = await fetch(`${API_BASE}/kb/claims`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create claim');
    return res.json();
  },

  deleteClaimKB: async (id: number): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/kb/claims/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete claim');
    return res.json();
  },

  listAssets: async (): Promise<AssetItem[]> => {
    const res = await fetch(`${API_BASE}/kb/assets`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch assets');
    return res.json();
  },

  createAsset: async (data: {
    name: string;
    asset_type: string;
    value: string;
    description?: string;
  }): Promise<AssetItem> => {
    const res = await fetch(`${API_BASE}/kb/assets`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create asset');
    return res.json();
  },

  deleteAsset: async (id: number): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/kb/assets/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete asset');
    return res.json();
  },

  atomise: async (guidelinesText: string): Promise<{ candidates: any[] }> => {
    const res = await fetch(`${API_BASE}/kb/atomise`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ guidelines_text: guidelinesText }),
    });
    if (!res.ok) throw new Error('Atomisation failed');
    return res.json();
  },

  confirmImport: async (payload: { rules: any[] }): Promise<{ saved_rules: number; message: string }> => {
    const res = await fetch(`${API_BASE}/kb/confirm-import`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Import confirmation failed');
    return res.json();
  },

  listVersions: async (): Promise<KBVersionItem[]> => {
    const res = await fetch(`${API_BASE}/kb/versions`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch versions');
    return res.json();
  },

  createVersion: async (label: string): Promise<KBVersionItem> => {
    const res = await fetch(`${API_BASE}/kb/versions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ label }),
    });
    if (!res.ok) throw new Error('Failed to create snapshot');
    return res.json();
  },

  activateVersion: async (id: number): Promise<{ message: string; version_id: number }> => {
    const res = await fetch(`${API_BASE}/kb/versions/${id}/activate`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to activate version');
    return res.json();
  },

  // Vision (I-2)
  analyzeVision: async (file: File): Promise<any> => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/vision/analyze`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Vision analysis failed' }));
      throw new Error(err.detail || 'Vision analysis failed');
    }
    return res.json();
  },

  // Audit
  listAudit: async (): Promise<AuditEventItem[]> => {
    const res = await fetch(`${API_BASE}/audit/`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch audit log');
    return res.json();
  },

  verifyAudit: async (): Promise<{ is_valid: boolean; verified: boolean; chain_length: number; total_events: number; details: any }> => {
    const res = await fetch(`${API_BASE}/audit/verify`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to verify audit log');
    return res.json();
  },

  // Insights (I-3)
  getInsightsSummary: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/insights/summary`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch insights summary');
    return res.json();
  },

  getAmbiguity: async (): Promise<{ total_rules_analyzed: number; flagged_count: number; flagged_rules: any[]; all_signals?: any[]; health_status?: string }> => {
    const res = await fetch(`${API_BASE}/insights/ambiguity`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch ambiguity report');
    return res.json();
  },

  acceptClarification: async (payload: { signal_type: string; target_code?: string; term_preferred?: string; clarified_text: string }): Promise<any> => {
    const res = await fetch(`${API_BASE}/insights/accept-clarification`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to accept clarification' }));
      throw new Error(err.detail || 'Failed to accept clarification');
    }
    return res.json();
  },

  getHealth: async (): Promise<{ status: string; ai_provider?: { name: string; status: string; label: string; has_key: boolean } }> => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch system health');
    return res.json();
  },

  getAILedger: async (contentId: number): Promise<any> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/ai-ledger`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to fetch AI usage ledger');
    return res.json();
  },

  exportCertificate: async (contentId: number, format: 'markdown' | 'json' | 'html' = 'markdown'): Promise<any> => {
    const res = await fetch(`${API_BASE}/content/${contentId}/export?format=${format}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to export governance certificate');
    if (format === 'json') return res.json();
    return res.text();
  },
};
