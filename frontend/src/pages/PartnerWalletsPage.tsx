import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Alert,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useParams } from 'react-router-dom';
import {
  usePartnerWallets,
  useDeleteWallet,
} from '../hooks/usePartnerWallets';
import type { PartnerWallet } from '../types';

// Import dialogs (to be created next)
import { EditWalletDialog } from '../components/EditWalletDialog';
import { BulkUploadWalletsDialog } from '../components/BulkUploadWalletsDialog';
import { DeleteWalletDialog } from '../components/DeleteWalletDialog';
import { AppLayout } from '../components/AppLayout';

/**
 * Partner Wallets Page
 *
 * Features:
 * - List wallets for a partner in MUI DataGrid
 * - Add/Edit/Delete wallets
 * - Bulk CSV upload
 * - Export to CSV
 * - Wallet validation
 * - Pagination and filtering
 */

export const PartnerWalletsPage: React.FC = () => {
  const { partnerId } = useParams<{ partnerId: string }>();

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [chainFilter] = useState<string | undefined>();
  const [activeFilter] = useState<boolean | undefined>(true);

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedWallet, setSelectedWallet] = useState<PartnerWallet | undefined>();

  const [bulkUploadOpen, setBulkUploadOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [walletToDelete, setWalletToDelete] = useState<PartnerWallet | null>(null);

  // Fetch wallets
  const {
    data: walletsData,
    isLoading,
    isError,
    error,
  } = usePartnerWallets(partnerId!, {
    page: page + 1, // API is 1-indexed
    page_size: pageSize,
    chain_id: chainFilter,
    is_active: activeFilter,
  });

  // Delete mutation
  const deleteMutation = useDeleteWallet(partnerId!);

  // Handlers
  const handleEdit = (wallet: PartnerWallet) => {
    setFormMode('edit');
    setSelectedWallet(wallet);
    setFormOpen(true);
  };

  const handleDelete = (wallet: PartnerWallet) => {
    setWalletToDelete(wallet);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (walletToDelete) {
      try {
        await deleteMutation.mutateAsync(walletToDelete.wallet_id);
        // Close dialog and reset state on success
        setDeleteDialogOpen(false);
        setWalletToDelete(null);
      } catch (error) {
        // Error is handled by the mutation error state
        console.error('Delete failed:', error);
      }
    }
  };

  // DataGrid columns
  const columns: GridColDef<PartnerWallet>[] = [
    {
      field: 'chain_id',
      headerName: 'Chain',
      width: 130,
      renderCell: (params: GridRenderCellParams<PartnerWallet>) => (
        <Chip label={params.value} size="small" variant="outlined" />
      ),
    },
    {
      field: 'wallet_address',
      headerName: 'Wallet Address',
      width: 400,
      flex: 1,
      renderCell: (params: GridRenderCellParams<PartnerWallet>) => (
        <Typography
          variant="body2"
          sx={{
            fontFamily: 'monospace',
            fontSize: '0.85rem',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'introduced_date',
      headerName: 'Introduced',
      width: 120,
      valueFormatter: (value) => {
        if (!value) return '-';
        return new Date(value).toLocaleDateString();
      },
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (params: GridRenderCellParams<PartnerWallet>) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'notes',
      headerName: 'Notes',
      width: 200,
      valueGetter: (value) => value || '-',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams<PartnerWallet>) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleEdit(params.row)}
            title="Edit Wallet"
          >
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row)}
            title="Delete Wallet"
            color="error"
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const wallets = walletsData?.wallets || [];
  const totalRows = walletsData?.total || 0;

  if (!partnerId) {
    return (
      <Container>
        <Alert severity="error">Partner ID is required</Alert>
      </Container>
    );
  }

  return (
    <AppLayout>
      <Box>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Error loading wallets: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          )}

          {deleteMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Delete failed: {deleteMutation.error?.message}
            </Alert>
          )}

          <Paper sx={{ p: 2 }}>
            <DataGrid
              rows={wallets}
              columns={columns}
              loading={isLoading}
              getRowId={(row) => row.wallet_id}
              pagination
              paginationMode="server"
              rowCount={totalRows}
              paginationModel={{ page, pageSize }}
              onPaginationModelChange={(model) => {
                setPage(model.page);
                setPageSize(model.pageSize);
              }}
              pageSizeOptions={[10, 25, 50, 100]}
              disableRowSelectionOnClick
              autoHeight
              sx={{
                '& .MuiDataGrid-cell': {
                  py: 1,
                },
              }}
            />
          </Paper>
        </Container>

        {/* Edit Wallet Dialog */}
        <EditWalletDialog
          open={formOpen}
          mode={formMode}
          partnerId={partnerId}
          wallet={selectedWallet}
          onClose={() => {
            setFormOpen(false);
            setSelectedWallet(undefined);
          }}
        />

        {/* Bulk Upload Dialog */}
        <BulkUploadWalletsDialog
          open={bulkUploadOpen}
          partnerId={partnerId}
          onClose={() => setBulkUploadOpen(false)}
        />

        {/* Delete Confirmation Dialog */}
        <DeleteWalletDialog
          open={deleteDialogOpen}
          wallet={walletToDelete}
          onClose={() => {
            setDeleteDialogOpen(false);
            setWalletToDelete(null);
          }}
          onConfirm={confirmDelete}
          isDeleting={deleteMutation.isPending}
        />
      </Box>
    </AppLayout>
  );
};