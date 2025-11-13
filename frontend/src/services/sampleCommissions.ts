import type { SampleEpoch } from '../types';
import { api } from './api';

/**
 * Sample Commissions Service
 *
 * API client for sample data commission calculations (epochs 800-860)
 */

export interface ValidatorSummary {
  validator_vote_pubkey: string;
  validator_name: string;
  total_stake_lamports: number;
  partner_stake_lamports: number;
  stake_percentage: string;
  partner_commission_lamports: number;
}

export interface SampleCommissionCalculation {
  partner_id: string;
  partner_name: string;
  wallet_count: number;
  validator_count: number;
  start_epoch: number;
  end_epoch: number;
  epoch_count: number;
  total_partner_stake_lamports: number;
  total_partner_rewards_lamports: number;
  commission_rate: string;
  total_commission_lamports: number;
  validator_summaries: ValidatorSummary[];
  epoch_details: Array<{
    epoch: number;
    validator_vote_pubkey: string;
    validator_name: string;
    total_active_stake_lamports: number;
    partner_stake_lamports: number;
    stake_percentage: string;
    validator_commission_lamports: number;
    total_staker_rewards_lamports: number;
    partner_rewards_lamports: number;
    commission_rate: string;
    partner_commission_lamports: number;
  }>;
}

export interface AllPartnersCommissionCalculation {
  start_epoch: number;
  end_epoch: number;
  epoch_count: number;
  commission_rate: string;
  partners: SampleCommissionCalculation[];
}

export const sampleCommissionsService = {
  /**
   * Get available sample data epochs (800-860)
   */
  getEpochs: async (): Promise<{ epochs: SampleEpoch[] }> => {
    const response = await api.get<{ epochs: SampleEpoch[] }>(
      '/api/v1/sample-commissions/epochs'
    );
    return response.data;
  },

  /**
   * Calculate commission for a specific partner across epoch range
   */
  calculatePartnerCommission: async (params: {
    partner_id: string;
    start_epoch: number;
    end_epoch: number;
    commission_rate?: number;
  }): Promise<SampleCommissionCalculation> => {
    const { partner_id, start_epoch, end_epoch, commission_rate = 0.5 } = params;
    const response = await api.get<SampleCommissionCalculation>(
      `/api/v1/sample-commissions/partners/${partner_id}`,
      {
        params: {
          start_epoch,
          end_epoch,
          commission_rate,
        },
      }
    );
    return response.data;
  },

  /**
   * Calculate commissions for all partners across epoch range
   */
  calculateAllPartnersCommission: async (params: {
    start_epoch: number;
    end_epoch: number;
    commission_rate?: number;
  }): Promise<AllPartnersCommissionCalculation> => {
    const { start_epoch, end_epoch, commission_rate = 0.5 } = params;
    const response = await api.get<AllPartnersCommissionCalculation>(
      '/api/v1/sample-commissions/all',
      {
        params: {
          start_epoch,
          end_epoch,
          commission_rate,
        },
      }
    );
    return response.data;
  },
};
