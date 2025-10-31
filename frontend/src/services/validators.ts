import type {
  Validator,
  ValidatorCreate,
  ValidatorUpdate,
  PaginatedResponse,
} from '../types';
import { api } from './api';

/**
 * Validators Service
 *
 * API client for validator CRUD operations
 */

export const validatorsService = {
  /**
   * Get all validators with pagination and optional chain filter
   */
  getValidators: async (params?: {
    chain_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Validator>> => {
    const response = await api.get<PaginatedResponse<Validator>>('/api/v1/validators', {
      params,
    });
    return response.data;
  },

  /**
   * Get a single validator by key and chain
   */
  getValidator: async (validator_key: string, chain_id: string): Promise<Validator> => {
    const response = await api.get<Validator>(
      `/api/v1/validators/${validator_key}/${chain_id}`
    );
    return response.data;
  },

  /**
   * Create a new validator
   */
  createValidator: async (data: ValidatorCreate): Promise<Validator> => {
    const response = await api.post<Validator>('/api/v1/validators', data);
    return response.data;
  },

  /**
   * Update an existing validator
   */
  updateValidator: async (
    validator_key: string,
    chain_id: string,
    data: ValidatorUpdate
  ): Promise<Validator> => {
    const response = await api.patch<Validator>(
      `/api/v1/validators/${validator_key}/${chain_id}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a validator
   */
  deleteValidator: async (validator_key: string, chain_id: string): Promise<void> => {
    await api.delete(`/api/v1/validators/${validator_key}/${chain_id}`);
  },
};
