import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Button,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';
import type { PartnerWallet } from '../types';

/**
 * Delete Wallet Dialog Component
 *
 * Features:
 * - Delete confirmation with wallet details
 * - Warning about commission calculation impact
 * - Soft delete explanation
 */

interface DeleteWalletDialogProps {
  open: boolean;
  wallet: PartnerWallet | null;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting: boolean;
}

export const DeleteWalletDialog: React.FC<DeleteWalletDialogProps> = ({
  open,
  wallet,
  onClose,
  onConfirm,
  isDeleting,
}) => {
  if (!wallet) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="warning" />
        Delete Wallet
      </DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to deactivate this wallet?
        </DialogContentText>

        <Box sx={{ mt: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Wallet Details:
          </Typography>
          <Box
            sx={{
              bgcolor: 'background.paper',
              p: 2,
              borderRadius: 1,
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="body2">
              <strong>Chain:</strong> {wallet.chain_id}
            </Typography>
            <Typography
              variant="body2"
              sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}
            >
              <strong>Address:</strong> {wallet.wallet_address}
            </Typography>
            <Typography variant="body2">
              <strong>Introduced:</strong>{' '}
              {new Date(wallet.introduced_date).toLocaleDateString()}
            </Typography>
            {wallet.notes && (
              <Typography variant="body2">
                <strong>Notes:</strong> {wallet.notes}
              </Typography>
            )}
          </Box>
        </Box>

        <Alert severity="info" icon={<WarningIcon />}>
          <Typography variant="body2">
            This will <strong>deactivate</strong> the wallet (soft delete). It will no longer
            be used for commission calculations going forward, but historical data will be
            preserved.
          </Typography>
        </Alert>

        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Impact on Commissions:</strong> This may affect commission calculations
            for periods after {new Date(wallet.introduced_date).toLocaleDateString()}.
          </Typography>
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isDeleting}>
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          color="error"
          variant="contained"
          disabled={isDeleting}
        >
          {isDeleting ? 'Deleting...' : 'Delete'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
