import type {
  Agreement,
  AgreementCreate,
  AgreementCreateWithRules,
  AgreementUpdate,
  AgreementWithRules,
  AgreementRule,
  AgreementRuleCreate,
  PaginatedResponse,
} from '../types';
import { api } from './api';

/**
 * Agreements Service
 *
 * API client for agreement and agreement rules CRUD operations
 */

export const agreementsService = {
  /**
   * Get all agreements with pagination and optional partner filter
   */
  getAgreements: async (params?: {
    partner_id?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Agreement>> => {
    const response = await api.get<PaginatedResponse<Agreement>>(
      '/api/v1/agreements',
      { params }
    );
    return response.data;
  },

  /**
   * Get a single agreement by ID with rules
   */
  getAgreement: async (agreement_id: string): Promise<AgreementWithRules> => {
    // Fetch agreement and rules separately, then combine
    const [agreementResponse, rulesResponse] = await Promise.all([
      api.get<Agreement>(`/api/v1/agreements/${agreement_id}`),
      api.get<AgreementRule[]>(`/api/v1/agreements/${agreement_id}/rules`)
    ]);

    return {
      ...agreementResponse.data,
      rules: rulesResponse.data,
    };
  },

  /**
   * Create a new agreement
   */
  createAgreement: async (data: AgreementCreate): Promise<Agreement> => {
    const response = await api.post<Agreement>('/api/v1/agreements', data);
    return response.data;
  },

  /**
   * Create a new agreement with rules (transaction-like behavior)
   * Creates agreement first, then adds rules one by one
   * If any rule fails, the agreement will still exist but without that rule
   */
  createAgreementWithRules: async (data: AgreementCreateWithRules): Promise<AgreementWithRules> => {
    const { rules, ...agreementData } = data;

    // Create the agreement first
    const agreement = await agreementsService.createAgreement(agreementData);

    // Add each rule
    const createdRules: AgreementRule[] = [];
    for (const ruleData of rules) {
      const fullRuleData: AgreementRuleCreate = {
        ...ruleData,
        agreement_id: agreement.agreement_id,
        version_number: agreement.current_version,
      };

      try {
        const rule = await agreementsService.addAgreementRule(
          agreement.agreement_id,
          fullRuleData
        );
        createdRules.push(rule);
      } catch (error) {
        // If a rule fails, we still have the agreement but log the error
        console.error('Failed to add rule:', error);
        throw error; // Re-throw to let caller handle
      }
    }

    return {
      ...agreement,
      rules: createdRules,
    };
  },

  /**
   * Update an existing agreement
   */
  updateAgreement: async (
    agreement_id: string,
    data: AgreementUpdate
  ): Promise<Agreement> => {
    const response = await api.put<Agreement>(
      `/api/v1/agreements/${agreement_id}`,
      data
    );
    return response.data;
  },

  /**
   * Activate an agreement
   */
  activateAgreement: async (agreement_id: string): Promise<Agreement> => {
    const response = await api.post<Agreement>(
      `/api/v1/agreements/${agreement_id}/activate`
    );
    return response.data;
  },

  /**
   * Delete (deactivate) an agreement
   */
  deleteAgreement: async (agreement_id: string): Promise<void> => {
    await api.delete(`/api/v1/agreements/${agreement_id}`);
  },

  /**
   * Get rules for an agreement
   */
  getAgreementRules: async (agreement_id: string): Promise<AgreementRule[]> => {
    const response = await api.get<AgreementRule[]>(
      `/api/v1/agreements/${agreement_id}/rules`
    );
    return response.data;
  },

  /**
   * Add a rule to an agreement
   */
  addAgreementRule: async (
    agreement_id: string,
    data: AgreementRuleCreate
  ): Promise<AgreementRule> => {
    const response = await api.post<AgreementRule>(
      `/api/v1/agreements/${agreement_id}/rules`,
      data
    );
    return response.data;
  },
};
