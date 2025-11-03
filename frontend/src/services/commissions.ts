import type {
  Period,
  CommissionLine,
  CommissionBreakdown,
  PaginatedResponse,
} from '../types';
import { api } from './api';

/**
 * Commissions Service
 *
 * API client for commission calculation and period operations
 */

export const commissionsService = {
  /**
   * Get canonical periods with pagination and optional chain filter
   */
  getPeriods: async (params?: {
    chain_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Period>> => {
    const response = await api.get<PaginatedResponse<Period>>('/api/v1/periods', {
      params,
    });
    return response.data;
  },

  /**
   * Calculate commission lines for a partner in a specific period
   */
  getCommissionLines: async (params: {
    partner_id: string;
    period_id: string;
    chain_id?: string;
    validator_key?: string;
  }): Promise<CommissionLine[]> => {
    const { partner_id, period_id, chain_id, validator_key } = params;
    const response = await api.get<CommissionLine[]>(
      `/api/v1/commissions/partners/${partner_id}`,
      {
        params: {
          period_id,
          chain_id,
          validator_key,
        },
      }
    );
    return response.data;
  },

  /**
   * Get commission breakdown by revenue component for a partner in a specific period
   */
  getCommissionBreakdown: async (params: {
    partner_id: string;
    period_id: string;
    validator_key?: string;
  }): Promise<CommissionBreakdown> => {
    const { partner_id, period_id, validator_key } = params;
    const response = await api.get<CommissionBreakdown>(
      `/api/v1/commissions/partners/${partner_id}/breakdown`,
      {
        params: {
          period_id,
          validator_key,
        },
      }
    );
    return response.data;
  },
};
