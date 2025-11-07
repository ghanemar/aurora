import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  AppBar,
  Toolbar,
  Button,
  Paper,
  Alert,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  Breadcrumbs,
  Link as MuiLink,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  usePartnerWallets,
  useDeleteWallet,
  useExportWallets,
} from '../hooks/usePartnerWallets';
import { partnersService } from '../services/partners';
import { downloadWalletTemplate, downloadWalletExport } from '../utils/csvTemplate';
import type { PartnerWallet } from '../types';

// Import dialogs (to be created next)
import { EditWalletDialog } from '../components/EditWalletDialog';
import { BulkUploadWalletsDialog } from '../components/BulkUploadWalletsDialog';
import { DeleteWalletDialog } from '../components/DeleteWalletDialog';

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
  const navigate = useNavigate();
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

  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // Fetch partner details for breadcrumb
  const { data: partner } = useQuery({
    queryKey: ['partner', partnerId],
    queryFn: () => partnersService.getPartner(partnerId!),
    enabled: !!partnerId,
  });

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

  // Export mutation
  const exportMutation = useExportWallets(partnerId!);

  // Handlers
  const handleAdd = () => {
    setFormMode('create');
    setSelectedWallet(undefined);
    setFormOpen(true);
  };

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

  const handleBulkUpload = () => {
    setBulkUploadOpen(true);
  };

  const handleExport = async () => {
    try {
      const blob = await exportMutation.mutateAsync({
        chain_id: chainFilter,
        is_active: activeFilter,
      });
      downloadWalletExport(blob, `${partner?.partner_name || 'partner'}_wallets.csv`);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleDownloadTemplate = () => {
    downloadWalletTemplate();
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
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
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" sx={{ bgcolor: 'background.paper' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/partners')} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ color: 'text.primary' }}>
              Partner Wallets
            </Typography>
            {partner && (
              <Breadcrumbs aria-label="breadcrumb" sx={{ mt: 0.5 }}>
                <MuiLink
                  component={RouterLink}
                  to="/partners"
                  underline="hover"
                  color="inherit"
                  sx={{ fontSize: '0.875rem' }}
                >
                  Partners
                </MuiLink>
                <Typography color="text.primary" sx={{ fontSize: '0.875rem' }}>
                  {partner.partner_name}
                </Typography>
                <Typography color="text.primary" sx={{ fontSize: '0.875rem' }}>
                  Wallets
                </Typography>
              </Breadcrumbs>
            )}
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
            sx={{ mr: 1 }}
          >
            Add Wallet
          </Button>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={handleBulkUpload}
            sx={{ mr: 1 }}
          >
            Bulk Upload
          </Button>
          <IconButton onClick={handleMenuOpen}>
            <MoreIcon />
          </IconButton>
          <Menu
            anchorEl={menuAnchor}
            open={Boolean(menuAnchor)}
            onClose={handleMenuClose}
          >
            <MenuItem
              onClick={() => {
                handleExport();
                handleMenuClose();
              }}
            >
              <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
              Export CSV
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleDownloadTemplate();
                handleMenuClose();
              }}
            >
              <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
              Download Template
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

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

        {exportMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Export failed: {exportMutation.error?.message}
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
  );
};
