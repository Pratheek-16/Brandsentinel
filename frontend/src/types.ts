export type Role = 'creator' | 'manager' | 'reviewer' | 'admin';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  workspace_id: number;
  workspace_name?: string;
  active?: boolean;
}

export interface DemoAccountInfo {
  id: number;
  email: string;
  name: string;
  role: string;
  workspace_id: number;
  workspace_name: string;
}

export interface WorkspaceInfoWithUsers {
  id: number;
  name: string;
  confidential_tier?: string;
  ai_mode?: string;
  accounts: DemoAccountInfo[];
}

export interface FindingSpan {
  start: number;
  end: number;
  text: string;
}

export interface FindingEvidence {
  type?: string;
  id?: string;
  quote?: string;
}

export interface Finding {
  id: number;
  category: 'tone' | 'terminology' | 'messaging' | 'visual' | 'accessibility' | 'claim' | string;
  severity: 'blocker' | 'major' | 'minor' | 'info';
  confidence: number | string;
  span_start: number;
  span_end: number;
  span_text: string;
  span?: FindingSpan;
  evidence_type?: string;
  evidence_id?: string;
  evidence_quote?: string;
  evidence?: FindingEvidence;
  reason: string;
  suggestion_text?: string;
  claim_status?: string;
  status?: 'open' | 'accepted' | 'edited' | 'dismissed';
  selected_replacement?: string | null;
  dismissal_reason?: string | null;
  decided_by?: number | null;
  decided_at?: string | null;
}

export interface ClaimItem {
  claim_text: string;
  span_start: number;
  span_end: number;
  status: 'approved' | 'unsupported' | 'expired' | 'missing_disclaimer';
  reason: string;
  evidence_ref?: string;
  required_disclaimer?: string;
  approved_text?: string;
}

export interface VerifiedSuggestion {
  replacement_text: string;
  verified: boolean;
  verification_reason: string;
  diff_summary?: string;
}

export interface CommentItem {
  id: number;
  content_id: number;
  finding_id?: number;
  author_id: number;
  author_name?: string;
  body: string;
  created_at: string;
}

export interface ContentVersionSummary {
  id: number;
  version_no: number;
  created_at: string | null;
  created_by: number;
  content_hash: string;
}

export interface ContentItem {
  id: number;
  workspace_id: number;
  creator_id: number;
  creator_name?: string;
  creator_email?: string;
  title: string;
  type: string;
  channel: string;
  status: string;
  version_id?: number;
  version_no?: number;
  text_body?: string;
  file_ref?: string;
  versions?: ContentVersionSummary[];
}

export interface RuleItem {
  id: number;
  code: string;
  category: string;
  text: string;
  severity_default: string;
  channels?: string[];
  kb_version_id?: number;
}

export interface FactItem {
  id: number;
  code: string;
  key: string;
  value: string;
  unit?: string;
  source?: string;
  is_stale?: boolean;
  valid_to?: string;
  kb_version_id?: number;
}

export interface TermItem {
  id: number;
  preferred: string;
  banned?: string[] | string;
  case_rule?: string;
  notes?: string;
  kb_version_id?: number;
}

export interface ClaimKBItem {
  id: number;
  approved_text: string;
  evidence_ref?: string;
  required_disclaimer?: string;
  valid_to?: string;
  is_expired?: boolean;
  kb_version_id?: number;
}

export interface AssetItem {
  id: number;
  name: string;
  asset_type: 'palette_color' | 'logo' | 'typography' | 'imagery' | string;
  value: string;
  description?: string;
  kb_version_id?: number;
}

export interface KBVersionItem {
  id: number;
  workspace_id: number;
  version_num: number;
  label: string;
  active: boolean;
  created_at: string;
}

export interface AuditEventItem {
  id: number;
  workspace_id: number;
  actor_id: number;
  action: string;
  entity: string;
  entity_id: number;
  payload_json?: any;
  prev_hash: string;
  hash: string;
  ts: string;
}

export interface AmbiguityRule {
  rule_code: string;
  dismissals_count: number;
  dismissal_rate_pct: number;
  status: string;
  recommendation: string;
}

export interface ReviewResponse {
  has_review?: boolean;
  review_id?: number;
  kb_version_id?: number;
  status?: string;
  redaction_count?: number;
  redacted_counts?: Record<string, number>;
  findings: Finding[];
  review?: {
    id: number;
    version_id: number;
    kb_version_id: number;
    status: string;
    provider: string;
    model: string;
    started_at: string | null;
  };
  ai_usage?: {
    provider: string;
    model: string;
    redaction_count: number;
    redacted_fields?: any;
  };
}
