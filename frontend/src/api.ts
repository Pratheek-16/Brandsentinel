const API_BASE = 'http://localhost:8000';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
    return res.json();
  },

  // Content
  createContent: async (data: { title: string; type: string; channel?: string; body: string }) => {
    const res = await fetch(`${API_BASE}/content/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Content creation failed');
    return res.json();
  },

  uploadContent: async (formData: FormData) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}/content/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Upload failed');
    return res.json();
  },

  getContent: async (contentId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Failed to fetch content');
    return res.json();
  },

  reviewContent: async (contentId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/review`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Review failed');
    return res.json();
  },

  submitContent: async (contentId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/submit`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Submission failed');
    return res.json();
  },

  approveContent: async (contentId: number, decision: string, reason?: string) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ decision, reason }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Approval action failed');
    return res.json();
  },

  // Suggestions (I-1)
  getSuggestions: async (contentId: number, findingId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/suggestions`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to get suggestions');
    return res.json();
  },

  acceptSuggestion: async (contentId: number, findingId: number, replacementText: string) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/accept`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ replacement_text: replacementText }),
    });
    if (!res.ok) throw new Error('Failed to accept suggestion');
    return res.json();
  },

  dismissFinding: async (contentId: number, findingId: number, reason: string) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/findings/${findingId}/dismiss`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error('Failed to dismiss finding');
    return res.json();
  },

  // Claims Ledger
  getClaims: async (contentId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/claims`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch claims ledger');
    return res.json();
  },

  // Comments
  getComments: async (contentId: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/comments`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch comments');
    return res.json();
  },

  addComment: async (contentId: number, body: string, findingId?: number, parentId?: number) => {
    const res = await fetch(`${API_BASE}/content/${contentId}/comments`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ body, finding_id: findingId, parent_id: parentId }),
    });
    if (!res.ok) throw new Error('Failed to post comment');
    return res.json();
  },

  // Knowledge Base
  listRules: async () => {
    const res = await fetch(`${API_BASE}/kb/rules`, { headers: getAuthHeaders() });
    return res.json();
  },
  createRule: async (data: any) => {
    const res = await fetch(`${API_BASE}/kb/rules`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },
  deleteRule: async (id: number) => {
    const res = await fetch(`${API_BASE}/kb/rules/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return res.json();
  },
  listFacts: async () => {
    const res = await fetch(`${API_BASE}/kb/facts`, { headers: getAuthHeaders() });
    return res.json();
  },
  listTerms: async () => {
    const res = await fetch(`${API_BASE}/kb/terms`, { headers: getAuthHeaders() });
    return res.json();
  },
  listClaimsKB: async () => {
    const res = await fetch(`${API_BASE}/kb/claims`, { headers: getAuthHeaders() });
    return res.json();
  },
  atomise: async (guidelinesText: string) => {
    const res = await fetch(`${API_BASE}/kb/atomise`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ guidelines_text: guidelinesText }),
    });
    return res.json();
  },
  confirmImport: async (payload: any) => {
    const res = await fetch(`${API_BASE}/kb/confirm-import`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  },
  listVersions: async () => {
    const res = await fetch(`${API_BASE}/kb/versions`, { headers: getAuthHeaders() });
    return res.json();
  },
  createVersion: async (label: string) => {
    const res = await fetch(`${API_BASE}/kb/versions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ label }),
    });
    return res.json();
  },
  activateVersion: async (id: number) => {
    const res = await fetch(`${API_BASE}/kb/versions/${id}/activate`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  // Vision (I-2)
  analyzeVision: async (file: File) => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/vision/analyze`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) throw new Error('Vision analysis failed');
    return res.json();
  },

  // Audit
  listAudit: async () => {
    const res = await fetch(`${API_BASE}/audit/`, { headers: getAuthHeaders() });
    return res.json();
  },
  verifyAudit: async () => {
    const res = await fetch(`${API_BASE}/audit/verify`, { headers: getAuthHeaders() });
    return res.json();
  },

  // Insights (I-3)
  getInsightsSummary: async () => {
    const res = await fetch(`${API_BASE}/insights/summary`, { headers: getAuthHeaders() });
    return res.json();
  },
  getAmbiguity: async () => {
    const res = await fetch(`${API_BASE}/insights/ambiguity`, { headers: getAuthHeaders() });
    return res.json();
  },
};
