import type {
  Partner,
  PartnerCreate,
  PartnerUpdate,
  PaginatedResponse,
} from '../types';
import { api } from './api';

/**
 * Partners Service
 *
 * API client for partner CRUD operations
 */

export const partnersService = {
  /**
   * Get all partners with pagination
   */
  getPartners: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Partner>> => {
    const response = await api.get<PaginatedResponse<Partner>>('/api/v1/partners', {
      params,
    });
    return response.data;
  },

  /**
   * Get a single partner by ID
   */
  getPartner: async (partner_id: string): Promise<Partner> => {
    const response = await api.get<Partner>(`/api/v1/partners/${partner_id}`);
    return response.data;
  },

  /**
   * Create a new partner
   */
  createPartner: async (data: PartnerCreate): Promise<Partner> => {
    const response = await api.post<Partner>('/api/v1/partners', data);
    return response.data;
  },

  /**
   * Update an existing partner
   */
  updatePartner: async (
    partner_id: string,
    data: PartnerUpdate
  ): Promise<Partner> => {
    const response = await api.put<Partner>(`/api/v1/partners/${partner_id}`, data);
    return response.data;
  },

  /**
   * Toggle partner active status
   */
  togglePartnerStatus: async (partner_id: string): Promise<Partner> => {
    const response = await api.patch<Partner>(
      `/api/v1/partners/${partner_id}/status`
    );
    return response.data;
  },

  /**
   * Get partner deletion info
   */
  getPartnerDeletionInfo: async (
    partner_id: string
  ): Promise<{ agreement_count: number }> => {
    const response = await api.get<{ agreement_count: number }>(
      `/api/v1/partners/${partner_id}/deletion-info`
    );
    return response.data;
  },

  /**
   * Delete a partner with optional cascade
   */
  deletePartner: async (
    partner_id: string,
    cascade: boolean = false
  ): Promise<{ partner_deleted: number; agreements_deleted: number }> => {
    const response = await api.delete<{
      partner_deleted: number;
      agreements_deleted: number;
    }>(`/api/v1/partners/${partner_id}`, {
      params: { cascade },
    });
    return response.data;
  },
};
