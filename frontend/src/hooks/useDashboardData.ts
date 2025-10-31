import { useQuery } from '@tanstack/react-query';
import type { DashboardStats, ChainInfo } from '../types';
import { api } from '../services/api';
import YAML from 'yaml';

/**
 * Custom hook to fetch dashboard data
 *
 * Provides:
 * - Configured chains from chains.yaml
 * - Count of validators per chain
 * - Count of partners
 * - Count of active agreements
 * - Recent commission calculations
 */

interface ChainConfig {
  chain_id: string;
  name: string;
  period_type: string;
  native_unit: string;
  native_decimals: number;
  finality_lag: number;
  providers: Record<string, string>;
}

interface ChainsYAML {
  chains: ChainConfig[];
}

export const useDashboardData = () => {
  // Fetch chains configuration
  const chainsQuery = useQuery({
    queryKey: ['chains-config'],
    queryFn: async (): Promise<ChainConfig[]> => {
      try {
        // Fetch chains.yaml from public folder or config endpoint
        const response = await fetch('/config/chains.yaml');
        if (!response.ok) {
          throw new Error('Failed to fetch chains configuration');
        }
        const text = await response.text();
        const config = YAML.parse(text) as ChainsYAML;
        return config.chains;
      } catch (error) {
        console.error('Error loading chains config:', error);
        // Fallback to hardcoded chains if config file not found
        return [
          {
            chain_id: 'solana-mainnet',
            name: 'Solana Mainnet',
            period_type: 'EPOCH',
            native_unit: 'SOL',
            native_decimals: 9,
            finality_lag: 32,
            providers: {},
          },
          {
            chain_id: 'solana-testnet',
            name: 'Solana Testnet',
            period_type: 'EPOCH',
            native_unit: 'SOL',
            native_decimals: 9,
            finality_lag: 32,
            providers: {},
          },
        ];
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch validators count per chain
  const validatorsQuery = useQuery({
    queryKey: ['validators-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/validators/stats');
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Fetch partners count
  const partnersQuery = useQuery({
    queryKey: ['partners-count'],
    queryFn: async () => {
      const response = await api.get('/api/v1/partners/count');
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Fetch active agreements count
  const agreementsQuery = useQuery({
    queryKey: ['agreements-count'],
    queryFn: async () => {
      const response = await api.get('/api/v1/agreements/count', {
        params: { status: 'ACTIVE' },
      });
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Fetch recent commissions
  const commissionsQuery = useQuery({
    queryKey: ['recent-commissions'],
    queryFn: async () => {
      const response = await api.get('/api/v1/commissions/recent', {
        params: { limit: 10 },
      });
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Combine data into dashboard stats
  const dashboardStats: DashboardStats | undefined =
    chainsQuery.data && validatorsQuery.data
      ? {
          chains:
            chainsQuery.data?.map((chain: ChainConfig) => ({
              chain_id: chain.chain_id,
              name: chain.name,
              validators_count:
                validatorsQuery.data?.chains?.[chain.chain_id] || 0,
            })) || [],
          total_validators: validatorsQuery.data?.total || 0,
          total_partners: partnersQuery.data?.count || 0,
          total_active_agreements: agreementsQuery.data?.count || 0,
          recent_commissions: commissionsQuery.data?.data || [],
        }
      : undefined;

  return {
    data: dashboardStats,
    isLoading:
      chainsQuery.isLoading ||
      validatorsQuery.isLoading ||
      partnersQuery.isLoading ||
      agreementsQuery.isLoading ||
      commissionsQuery.isLoading,
    isError:
      chainsQuery.isError ||
      validatorsQuery.isError ||
      partnersQuery.isError ||
      agreementsQuery.isError ||
      commissionsQuery.isError,
    error:
      chainsQuery.error ||
      validatorsQuery.error ||
      partnersQuery.error ||
      agreementsQuery.error ||
      commissionsQuery.error,
    refetch: () => {
      chainsQuery.refetch();
      validatorsQuery.refetch();
      partnersQuery.refetch();
      agreementsQuery.refetch();
      commissionsQuery.refetch();
    },
  };
};
