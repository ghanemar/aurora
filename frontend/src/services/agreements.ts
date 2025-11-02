import type {
  Agreement,
  AgreementCreate,
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
    const response = await api.get<AgreementWithRules>(
      `/api/v1/agreements/${agreement_id}`
    );
    return response.data;
  },

  /**
   * Create a new agreement with rules
   */
  createAgreement: async (data: AgreementCreate): Promise<Agreement> => {
    const response = await api.post<Agreement>('/api/v1/agreements', data);
    return response.data;
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
