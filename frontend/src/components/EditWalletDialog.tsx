import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  FormControlLabel,
  Checkbox,
  Alert,
  Box,
} from '@mui/material';
import { useCreateWallet, useUpdateWallet } from '../hooks/usePartnerWallets';
import { validateWalletAddress, validateIntroducedDate } from '../utils/walletValidation';
import type { PartnerWallet, PartnerWalletCreate, PartnerWalletUpdate } from '../types';

/**
 * Edit Wallet Dialog Component
 *
 * Features:
 * - Add/Edit wallet
 * - Chain-specific address validation
 * - Date validation
 * - All fields editable
 */

interface EditWalletDialogProps {
  open: boolean;
  mode: 'create' | 'edit';
  partnerId: string;
  wallet?: PartnerWallet;
  onClose: () => void;
}

export const EditWalletDialog: React.FC<EditWalletDialogProps> = ({
  open,
  mode,
  partnerId,
  wallet,
  onClose,
}) => {
  const [chainId, setChainId] = useState('solana-mainnet');
  const [walletAddress, setWalletAddress] = useState('');
  const [introducedDate, setIntroducedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [fieldErrors, setFieldErrors] = useState<{
    chainId?: string;
    walletAddress?: string;
    introducedDate?: string;
  }>({});

  const createMutation = useCreateWallet(partnerId);
  const updateMutation = useUpdateWallet(
    partnerId,
    wallet?.wallet_id || ''
  );

  // Initialize form
  useEffect(() => {
    if (mode === 'edit' && wallet) {
      setChainId(wallet.chain_id);
      setWalletAddress(wallet.wallet_address);
      setIntroducedDate(wallet.introduced_date);
      setNotes(wallet.notes || '');
      setIsActive(wallet.is_active);
    } else {
      // Reset form in create mode
      setChainId('');
      setWalletAddress('');
      setIntroducedDate('');
      setNotes('');
      setIsActive(true);
    }
    setFieldErrors({});
  }, [mode, wallet, open]);

  const validateForm = (): boolean => {
    const errors: {
      chainId?: string;
      walletAddress?: string;
      introducedDate?: string;
    } = {};

    if (!chainId.trim()) {
      errors.chainId = 'Chain is required';
    }

    if (!walletAddress.trim()) {
      errors.walletAddress = 'Wallet address is required';
    } else if (chainId) {
      const validation = validateWalletAddress(walletAddress.trim(), chainId);
      if (!validation.isValid) {
        errors.walletAddress = validation.error;
      }
    }

    if (!introducedDate) {
      errors.introducedDate = 'Introduced date is required';
    } else {
      const validation = validateIntroducedDate(introducedDate);
      if (!validation.isValid) {
        errors.introducedDate = validation.error;
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      if (mode === 'create') {
        const data: PartnerWalletCreate = {
          chain_id: chainId.trim(),
          wallet_address: walletAddress.trim(),
          introduced_date: introducedDate,
          notes: notes.trim() || undefined,
        };
        await createMutation.mutateAsync(data);
      } else {
        const data: PartnerWalletUpdate = {
          chain_id: chainId.trim(),
          wallet_address: walletAddress.trim(),
          introduced_date: introducedDate,
          notes: notes.trim() || undefined,
          is_active: isActive,
        };
        await updateMutation.mutateAsync(data);
      }
      onClose();
    } catch (error) {
      console.error('Failed to save wallet:', error);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;
  const error = createMutation.error || updateMutation.error;

  // Get today's date in YYYY-MM-DD format for max date validation
  const today = new Date().toISOString().split('T')[0];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === 'create' ? 'Add Wallet' : 'Edit Wallet'}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error instanceof Error ? error.message : 'Operation failed'}
            </Alert>
          )}

          <FormControl fullWidth margin="dense" error={!!fieldErrors.chainId}>
            <InputLabel>Chain *</InputLabel>
            <Select
              value={chainId}
              onChange={(e) => {
                setChainId(e.target.value);
                setFieldErrors((prev) => ({ ...prev, chainId: undefined }));
              }}
              label="Chain *"
            >
              <MenuItem value="solana-mainnet">Solana</MenuItem>
            </Select>
            {fieldErrors.chainId && (
              <Box sx={{ color: 'error.main', fontSize: '0.75rem', mt: 0.5 }}>
                {fieldErrors.chainId}
              </Box>
            )}
          </FormControl>

          <TextField
            fullWidth
            margin="dense"
            label="Wallet Address *"
            value={walletAddress}
            onChange={(e) => {
              setWalletAddress(e.target.value);
              setFieldErrors((prev) => ({ ...prev, walletAddress: undefined }));
            }}
            error={!!fieldErrors.walletAddress}
            helperText={fieldErrors.walletAddress || 'Enter the blockchain wallet address'}
            InputProps={{
              sx: { fontFamily: 'monospace' },
            }}
          />

          <TextField
            fullWidth
            margin="dense"
            type="date"
            label="Introduced Date *"
            value={introducedDate}
            onChange={(e) => {
              setIntroducedDate(e.target.value);
              setFieldErrors((prev) => ({ ...prev, introducedDate: undefined }));
            }}
            error={!!fieldErrors.introducedDate}
            helperText={
              fieldErrors.introducedDate ||
              'Date when this wallet was introduced by the partner'
            }
            InputLabelProps={{
              shrink: true,
            }}
            inputProps={{
              max: today,
            }}
          />

          <TextField
            fullWidth
            margin="dense"
            label="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            multiline
            rows={3}
            helperText="Optional notes about this wallet"
          />

          {mode === 'edit' && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                />
              }
              label="Active"
              sx={{ mt: 1 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : mode === 'create' ? 'Add' : 'Save'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
