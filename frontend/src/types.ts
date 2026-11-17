export type Role = 'creator' | 'manager' | 'reviewer' | 'admin';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  workspace_id: number;
}

export interface Finding {
  id: number;
  category: 'tone' | 'terminology' | 'messaging' | 'visual' | 'accessibility' | 'claim';
  severity: 'blocker' | 'major' | 'minor' | 'info';
  confidence: string;
  span_start: number;
  span_end: number;
  span_text: string;
  evidence_type?: string;
  evidence_id?: string;
  evidence_quote?: string;
  reason: string;
  suggestion_text?: string;
  claim_status?: string;
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
}

export interface CommentItem {
  id: number;
  content_id: number;
  finding_id?: number;
  author_id: number;
  body: string;
  created_at: string;
}

export interface RuleItem {
  id: number;
  code: string;
  category: string;
  text: string;
  severity_default: string;
  channels?: string[];
}

export interface FactItem {
  id: number;
  code: string;
  key: string;
  value: string;
  unit?: string;
  source?: string;
}

export interface TermItem {
  id: number;
  preferred: string;
  banned?: string[];
  case_rule?: string;
  notes?: string;
}

export interface ClaimKBItem {
  id: number;
  approved_text: string;
  evidence_ref?: string;
  required_disclaimer?: string;
  valid_to?: string;
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
