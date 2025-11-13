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
  EXEC_FEES: 'EXEC_FEES',
  MEV_TIPS: 'MEV_TIPS',
  VOTE_REWARDS: 'VOTE_REWARDS',
  COMMISSION: 'COMMISSION',
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
  revenue_component: RevenueComponent;
  commission_rate_bps: number;
  attribution_method: AttributionMethod;
  validator_key: string | null;
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
}

export interface AgreementCreateWithRules extends AgreementCreate {
  rules: Omit<AgreementRuleCreate, 'agreement_id' | 'version_number'>[];
}

export interface AgreementUpdate {
  agreement_name?: string;
  status?: AgreementStatus;
  effective_from?: string;
  effective_until?: string;
}

export interface AgreementRuleCreate {
  agreement_id: string;
  version_number: number;
  rule_order: number;
  revenue_component: RevenueComponent;
  commission_rate_bps: number;
  attribution_method: AttributionMethod;
  validator_key?: string;
}

export interface AgreementWithRules extends Agreement {
  rules: AgreementRule[];
  partner?: Partner;
}

/**
 * Period Types
 */

export interface Period {
  period_id: string;
  chain_id: string;
  epoch_number: number | null;
  start_time: string;
  end_time: string;
}

/**
 * Sample Data Epoch Types
 */

export interface SampleEpoch {
  epoch: number;
  total_active_stake_lamports: number;
  total_staker_rewards_lamports: number;
}

export interface SampleEpochRange {
  start_epoch: number;
  end_epoch: number;
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

export interface CommissionLine {
  partner_id: string;
  agreement_id: string;
  rule_id: string;
  chain_id: string;
  period_id: string;
  validator_key: string;
  revenue_component: string;
  base_amount_native: string;
  commission_rate_bps: number;
  commission_native: string;
  attribution_method: string;
}

export interface CommissionBreakdown {
  total_commission: string;
  exec_fees_commission: string;
  mev_commission: string;
  rewards_commission: string;
  lines: CommissionLine[];
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
 * Partner Wallet Types
 */

export interface PartnerWallet {
  wallet_id: string;
  partner_id: string;
  chain_id: string;
  wallet_address: string;
  introduced_date: string; // YYYY-MM-DD format
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PartnerWalletCreate {
  chain_id: string;
  wallet_address: string;
  introduced_date: string;
  notes?: string;
}

export interface PartnerWalletUpdate {
  chain_id?: string;
  wallet_address?: string;
  introduced_date?: string;
  notes?: string;
  is_active?: boolean;
}

export interface PartnerWalletListResponse {
  total: number;
  page: number;
  page_size: number;
  wallets: PartnerWallet[];
}

export interface BulkUploadResult {
  success: number;
  skipped: number;
  errors: Array<{
    row: number;
    wallet_address?: string;
    error: string;
    existing_partner?: string;
  }>;
}

export interface WalletValidationResult {
  valid: boolean;
  stake_events_count: number;
  first_stake_date: string | null;
  last_stake_date: string | null;
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
