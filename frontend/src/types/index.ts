/**
 * User and Authentication Types
 */

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'partner';
  is_active: boolean;
  partner_id: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}

/**
 * API Response Types
 */

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

/**
 * Auth Context Types
 */

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

/**
 * Validator Types
 */

export interface Validator {
  validator_key: string;
  chain_id: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ValidatorCreate {
  validator_key: string;
  chain_id: string;
  description?: string;
}

export interface ValidatorUpdate {
  description?: string;
  is_active?: boolean;
}

/**
 * Partner Types
 */

export interface Partner {
  partner_id: string;
  partner_name: string;
  legal_entity_name: string | null;
  contact_email: string;
  contact_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartnerCreate {
  partner_name: string;
  legal_entity_name?: string;
  contact_email: string;
  contact_name?: string;
}

export interface PartnerUpdate {
  partner_name?: string;
  legal_entity_name?: string;
  contact_email?: string;
  contact_name?: string;
  is_active?: boolean;
}

/**
 * Agreement Types
 */

export const AgreementStatus = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  SUSPENDED: 'SUSPENDED',
  TERMINATED: 'TERMINATED',
} as const;

export type AgreementStatus = typeof AgreementStatus[keyof typeof AgreementStatus];

export const RevenueComponent = {
  ALL: 'ALL',
  EXEC_FEES: 'EXEC_FEES',
  MEV: 'MEV',
  REWARDS: 'REWARDS',
} as const;

export type RevenueComponent = typeof RevenueComponent[keyof typeof RevenueComponent];

export const AttributionMethod = {
  CLIENT_REVENUE: 'CLIENT_REVENUE',
  STAKE_WEIGHT: 'STAKE_WEIGHT',
  FIXED_SHARE: 'FIXED_SHARE',
} as const;

export type AttributionMethod = typeof AttributionMethod[keyof typeof AttributionMethod];

export interface Agreement {
  agreement_id: string;
  partner_id: string;
  agreement_name: string;
  current_version: number;
  status: AgreementStatus;
  effective_from: string;
  effective_until: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgreementRule {
  rule_id: string;
  agreement_id: string;
  version_number: number;
  rule_order: number;
  chain_id: string | null;
  validator_key: string | null;
  revenue_component: RevenueComponent;
  attribution_method: AttributionMethod;
  commission_rate_bps: number;
  floor_amount_native: string | null;
  cap_amount_native: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgreementCreate {
  partner_id: string;
  agreement_name: string;
  status?: AgreementStatus;
  effective_from: string;
  effective_until?: string;
  rules: AgreementRuleCreate[];
}

export interface AgreementUpdate {
  agreement_name?: string;
  status?: AgreementStatus;
  effective_from?: string;
  effective_until?: string;
}

export interface AgreementRuleCreate {
  rule_order: number;
  chain_id?: string;
  validator_key?: string;
  revenue_component: RevenueComponent;
  attribution_method: AttributionMethod;
  commission_rate_bps: number;
  floor_amount_native?: string;
  cap_amount_native?: string;
}

export interface AgreementWithRules extends Agreement {
  rules: AgreementRule[];
  partner?: Partner;
}

/**
 * Commission Types
 */

export interface CommissionRecord {
  commission_id: string;
  agreement_id: string;
  period_id: string;
  validator_key: string;
  commission_amount_native: string;
  computed_at: string;
}

/**
 * Dashboard Stats Types
 */

export interface ChainInfo {
  chain_id: string;
  name: string;
  validators_count: number;
}

export interface DashboardStats {
  chains: ChainInfo[];
  total_validators: number;
  total_partners: number;
  total_active_agreements: number;
  recent_commissions: CommissionRecord[];
}

/**
 * Paginated List Response
 */

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  data: T[];
}
