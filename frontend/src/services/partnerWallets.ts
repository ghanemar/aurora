import type {
  PartnerWallet,
  PartnerWalletCreate,
  PartnerWalletUpdate,
  PartnerWalletListResponse,
  BulkUploadResult,
  WalletValidationResult,
} from '../types';
import { api } from './api';

/**
 * Partner Wallets Service
 *
 * API client for partner wallet CRUD operations including bulk upload
 */

export const partnerWalletsService = {
  /**
   * Get all wallets for a partner with pagination and filters
   */
  getWallets: async (
    partnerId: string,
    params?: {
      page?: number;
      page_size?: number;
      chain_id?: string;
      is_active?: boolean;
    }
  ): Promise<PartnerWalletListResponse> => {
    const response = await api.get<PartnerWalletListResponse>(
      `/api/v1/partners/${partnerId}/wallets`,
      { params }
    );
    return response.data;
  },

  /**
   * Get a single wallet by ID
   */
  getWallet: async (partnerId: string, walletId: string): Promise<PartnerWallet> => {
    const response = await api.get<PartnerWallet>(
      `/api/v1/partners/${partnerId}/wallets/${walletId}`
    );
    return response.data;
  },

  /**
   * Create a new wallet for a partner
   */
  createWallet: async (
    partnerId: string,
    data: PartnerWalletCreate
  ): Promise<PartnerWallet> => {
    const response = await api.post<PartnerWallet>(
      `/api/v1/partners/${partnerId}/wallets`,
      data
    );
    return response.data;
  },

  /**
   * Update an existing wallet
   */
  updateWallet: async (
    partnerId: string,
    walletId: string,
    data: PartnerWalletUpdate
  ): Promise<PartnerWallet> => {
    const response = await api.put<PartnerWallet>(
      `/api/v1/partners/${partnerId}/wallets/${walletId}`,
      data
    );
    return response.data;
  },

  /**
   * Deactivate a wallet (soft delete)
   */
  deleteWallet: async (partnerId: string, walletId: string): Promise<void> => {
    await api.delete(`/api/v1/partners/${partnerId}/wallets/${walletId}`);
  },

  /**
   * Bulk upload wallets from CSV file
   */
  bulkUpload: async (
    partnerId: string,
    file: File,
    skipDuplicates: boolean = true
  ): Promise<BulkUploadResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<BulkUploadResult>(
      `/api/v1/partners/${partnerId}/wallets/bulk?skip_duplicates=${skipDuplicates}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Export wallets to CSV
   */
  exportWallets: async (
    partnerId: string,
    filters?: {
      chain_id?: string;
      is_active?: boolean;
    }
  ): Promise<Blob> => {
    const response = await api.get(
      `/api/v1/partners/${partnerId}/wallets/export/csv`,
      {
        params: filters,
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Validate wallet's stake history
   */
  validateWallet: async (
    partnerId: string,
    walletId: string
  ): Promise<WalletValidationResult> => {
    const response = await api.get<WalletValidationResult>(
      `/api/v1/partners/${partnerId}/wallets/${walletId}/validate`
    );
    return response.data;
  },

  /**
   * Get count of wallets for a partner
   */
  getWalletCount: async (
    partnerId: string,
    filters?: {
      chain_id?: string;
      is_active?: boolean;
    }
  ): Promise<number> => {
    const response = await api.get<PartnerWalletListResponse>(
      `/api/v1/partners/${partnerId}/wallets`,
      {
        params: { page: 1, page_size: 1, ...filters },
      }
    );
    return response.data.total;
  },
};
