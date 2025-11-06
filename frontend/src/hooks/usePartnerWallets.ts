import { useMutation, useQuery, useQueryClient } from '@tantml/react-query';
import type {
  PartnerWallet,
  PartnerWalletCreate,
  PartnerWalletUpdate,
  PartnerWalletListResponse,
  BulkUploadResult,
  WalletValidationResult,
} from '../types';
import { partnerWalletsService } from '../services/partnerWallets';

/**
 * React Query hooks for Partner Wallet operations
 */

// Query keys
export const walletKeys = {
  all: ['partner-wallets'] as const,
  lists: () => [...walletKeys.all, 'list'] as const,
  list: (partnerId: string, filters?: Record<string, any>) =>
    [...walletKeys.lists(), partnerId, filters] as const,
  details: () => [...walletKeys.all, 'detail'] as const,
  detail: (partnerId: string, walletId: string) =>
    [...walletKeys.details(), partnerId, walletId] as const,
  validation: (partnerId: string, walletId: string) =>
    [...walletKeys.all, 'validation', partnerId, walletId] as const,
  count: (partnerId: string, filters?: Record<string, any>) =>
    [...walletKeys.all, 'count', partnerId, filters] as const,
};

/**
 * Fetch wallets for a partner with pagination and filters
 */
export function usePartnerWallets(
  partnerId: string,
  params?: {
    page?: number;
    page_size?: number;
    chain_id?: string;
    is_active?: boolean;
  }
) {
  return useQuery({
    queryKey: walletKeys.list(partnerId, params),
    queryFn: () => partnerWalletsService.getWallets(partnerId, params),
    enabled: !!partnerId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Fetch a single wallet by ID
 */
export function usePartnerWallet(partnerId: string, walletId: string) {
  return useQuery({
    queryKey: walletKeys.detail(partnerId, walletId),
    queryFn: () => partnerWalletsService.getWallet(partnerId, walletId),
    enabled: !!partnerId && !!walletId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Fetch wallet count for a partner
 */
export function usePartnerWalletCount(
  partnerId: string,
  filters?: {
    chain_id?: string;
    is_active?: boolean;
  }
) {
  return useQuery({
    queryKey: walletKeys.count(partnerId, filters),
    queryFn: () => partnerWalletsService.getWalletCount(partnerId, filters),
    enabled: !!partnerId,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Create a new wallet for a partner
 */
export function useCreateWallet(partnerId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PartnerWalletCreate) =>
      partnerWalletsService.createWallet(partnerId, data),
    onSuccess: () => {
      // Invalidate all wallet lists for this partner
      queryClient.invalidateQueries({ queryKey: walletKeys.lists() });
      queryClient.invalidateQueries({ queryKey: walletKeys.count(partnerId) });
    },
  });
}

/**
 * Update an existing wallet
 */
export function useUpdateWallet(partnerId: string, walletId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PartnerWalletUpdate) =>
      partnerWalletsService.updateWallet(partnerId, walletId, data),
    onSuccess: (updatedWallet) => {
      // Update the specific wallet in cache
      queryClient.setQueryData(
        walletKeys.detail(partnerId, walletId),
        updatedWallet
      );

      // Invalidate lists to reflect changes
      queryClient.invalidateQueries({ queryKey: walletKeys.lists() });
    },
  });
}

/**
 * Delete (deactivate) a wallet
 */
export function useDeleteWallet(partnerId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (walletId: string) =>
      partnerWalletsService.deleteWallet(partnerId, walletId),
    onSuccess: () => {
      // Invalidate all wallet lists for this partner
      queryClient.invalidateQueries({ queryKey: walletKeys.lists() });
      queryClient.invalidateQueries({ queryKey: walletKeys.count(partnerId) });
    },
  });
}

/**
 * Bulk upload wallets from CSV
 */
export function useBulkUploadWallets(partnerId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      skipDuplicates = true,
    }: {
      file: File;
      skipDuplicates?: boolean;
    }) => partnerWalletsService.bulkUpload(partnerId, file, skipDuplicates),
    onSuccess: () => {
      // Invalidate all wallet lists for this partner
      queryClient.invalidateQueries({ queryKey: walletKeys.lists() });
      queryClient.invalidateQueries({ queryKey: walletKeys.count(partnerId) });
    },
  });
}

/**
 * Export wallets to CSV
 */
export function useExportWallets(partnerId: string) {
  return useMutation({
    mutationFn: (filters?: { chain_id?: string; is_active?: boolean }) =>
      partnerWalletsService.exportWallets(partnerId, filters),
  });
}

/**
 * Validate wallet's stake history
 */
export function useValidateWallet(partnerId: string, walletId: string) {
  return useQuery({
    queryKey: walletKeys.validation(partnerId, walletId),
    queryFn: () => partnerWalletsService.validateWallet(partnerId, walletId),
    enabled: false, // Manual trigger only
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
