import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import type { Validator, ValidatorCreate, ValidatorUpdate } from '../types';

/**
 * Validator Form Component
 *
 * Features:
 * - Add/Edit validator
 * - Form validation (required fields, vote account format)
 * - Chain selection dropdown
 * - Error handling
 * - Loading state
 */

interface ValidatorFormProps {
  open: boolean;
  mode: 'create' | 'edit';
  validator?: Validator;
  chains: Array<{ chain_id: string; name: string }>;
  onClose: () => void;
  onSubmit: (data: ValidatorCreate | ValidatorUpdate) => Promise<void>;
}

// Basic Solana base58 validation
const isValidSolanaAddress = (address: string): boolean => {
  // Solana addresses are 32-44 characters and use base58 alphabet
  const base58Regex = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  return base58Regex.test(address);
};

export const ValidatorForm: React.FC<ValidatorFormProps> = ({
  open,
  mode,
  validator,
  chains,
  onClose,
  onSubmit,
}) => {
  const [validatorKey, setValidatorKey] = useState('');
  const [chainId, setChainId] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{
    validatorKey?: string;
    chainId?: string;
  }>({});

  // Initialize form with validator data in edit mode
  useEffect(() => {
    if (mode === 'edit' && validator) {
      setValidatorKey(validator.validator_key);
      setChainId(validator.chain_id);
      setDescription(validator.description || '');
    } else {
      // Reset form in create mode
      setValidatorKey('');
      setChainId('');
      setDescription('');
    }
    setError(null);
    setFieldErrors({});
  }, [mode, validator, open]);

  const validateForm = (): boolean => {
    const errors: { validatorKey?: string; chainId?: string } = {};

    if (!validatorKey.trim()) {
      errors.validatorKey = 'Validator key is required';
    } else if (!isValidSolanaAddress(validatorKey.trim())) {
      errors.validatorKey = 'Invalid Solana vote account format';
    }

    if (!chainId) {
      errors.chainId = 'Chain selection is required';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    setError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      if (mode === 'create') {
        const data: ValidatorCreate = {
          validator_key: validatorKey.trim(),
          chain_id: chainId,
          description: description.trim() || undefined,
        };
        await onSubmit(data);
      } else {
        const data: ValidatorUpdate = {
          description: description.trim() || undefined,
        };
        await onSubmit(data);
      }

      // Reset form and close dialog
      setValidatorKey('');
      setChainId('');
      setDescription('');
      setFieldErrors({});
      onClose();
    } catch (err: any) {
      console.error('Form submission error:', err);
      setError(
        err.response?.data?.detail ||
          `Failed to ${mode} validator. Please try again.`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      setFieldErrors({});
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Add New Validator' : 'Edit Validator'}
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Validator Key */}
        <TextField
          label="Validator Key"
          fullWidth
          margin="normal"
          value={validatorKey}
          onChange={(e) => {
            setValidatorKey(e.target.value);
            setFieldErrors((prev) => ({ ...prev, validatorKey: undefined }));
          }}
          disabled={loading || mode === 'edit'}
          required
          error={!!fieldErrors.validatorKey}
          helperText={
            fieldErrors.validatorKey || 'Solana vote account public key (base58)'
          }
          autoFocus={mode === 'create'}
        />

        {/* Chain Selection */}
        <TextField
          select
          label="Chain"
          fullWidth
          margin="normal"
          value={chainId}
          onChange={(e) => {
            setChainId(e.target.value);
            setFieldErrors((prev) => ({ ...prev, chainId: undefined }));
          }}
          disabled={loading || mode === 'edit'}
          required
          error={!!fieldErrors.chainId}
          helperText={fieldErrors.chainId || 'Select blockchain network'}
        >
          {chains.map((chain) => (
            <MenuItem key={chain.chain_id} value={chain.chain_id}>
              {chain.name}
            </MenuItem>
          ))}
        </TextField>

        {/* Description */}
        <TextField
          label="Description"
          fullWidth
          margin="normal"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={loading}
          multiline
          rows={3}
          placeholder="Optional description or notes"
        />
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {mode === 'create' ? 'Add Validator' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
