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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  IconButton,
  Chip,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agreementsService } from '../services/agreements';
import { partnersService } from '../services/partners';
import type { Agreement, AgreementCreate, Partner, AgreementStatus } from '../types';

/**
 * Agreements Page
 *
 * Features:
 * - List agreements in MUI DataGrid
 * - Filter by partner
 * - Add/Edit/Delete agreements
 * - View agreement rules
 * - Status management
 */

export const AgreementsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [partnerFilter, setPartnerFilter] = useState<string>('');
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agreementToDelete, setAgreementToDelete] = useState<Agreement | null>(null);

  // Fetch partners for filter dropdown
  const { data: partnersData } = useQuery({
    queryKey: ['partners'],
    queryFn: () => partnersService.getPartners({ page: 1, page_size: 100 }),
    staleTime: 60 * 1000,
  });

  // Fetch agreements
  const {
    data: agreementsData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['agreements', partnerFilter],
    queryFn: () =>
      agreementsService.getAgreements({
        partner_id: partnerFilter || undefined,
        page: 1,
        page_size: 100,
      }),
    staleTime: 60 * 1000,
  });

  // Delete agreement mutation
  const deleteMutation = useMutation({
    mutationFn: (agreement_id: string) => agreementsService.deleteAgreement(agreement_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agreements'] });
      setDeleteDialogOpen(false);
      setAgreementToDelete(null);
    },
  });

  // Handlers
  const handleAdd = () => {
    setFormOpen(true);
  };

  const handleDelete = (agreement: Agreement) => {
    setAgreementToDelete(agreement);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (agreementToDelete) {
      deleteMutation.mutate(agreementToDelete.agreement_id);
    }
  };

  // Get partner name from ID
  const getPartnerName = (partnerId: string): string => {
    const partner = partnersData?.data.find((p) => p.partner_id === partnerId);
    return partner?.partner_name || 'Unknown';
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  // Get status color
  const getStatusColor = (status: AgreementStatus): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'ACTIVE':
        return 'success';
      case 'DRAFT':
        return 'warning';
      case 'SUSPENDED':
      case 'TERMINATED':
        return 'error';
      default:
        return 'default';
    }
  };

  // DataGrid columns
  const columns: GridColDef<Agreement>[] = [
    {
      field: 'agreement_name',
      headerName: 'Agreement Name',
      width: 250,
      flex: 1,
    },
    {
      field: 'partner_id',
      headerName: 'Partner',
      width: 200,
      valueGetter: (value) => getPartnerName(value),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams<Agreement>) => (
        <Chip
          label={params.value}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'effective_from',
      headerName: 'Start Date',
      width: 120,
      valueGetter: (value) => formatDate(value),
    },
    {
      field: 'effective_until',
      headerName: 'End Date',
      width: 120,
      valueGetter: (value) => (value ? formatDate(value) : 'Ongoing'),
    },
    {
      field: 'current_version',
      headerName: 'Version',
      width: 100,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams<Agreement>) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => alert('View details coming soon')}
            title="View Details"
          >
            <ViewIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row)}
            title="Delete Agreement"
            color="error"
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const agreements = agreementsData?.data || [];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" sx={{ bgcolor: 'background.paper' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/')} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, color: 'text.primary' }}>
            Agreements
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
            disabled
          >
            Add Agreement (Coming Soon)
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error loading agreements: {error instanceof Error ? error.message : 'Unknown error'}
          </Alert>
        )}

        {deleteMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Delete failed: {deleteMutation.error?.message}
          </Alert>
        )}

        <Paper sx={{ p: 2 }}>
          <DataGrid
            rows={agreements}
            columns={columns}
            loading={isLoading}
            getRowId={(row) => row.agreement_id}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25, page: 0 },
              },
            }}
            pageSizeOptions={[25, 50, 100]}
            disableRowSelectionOnClick
            autoHeight
            sx={{
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
            }}
          />
        </Paper>
      </Container>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete agreement "{agreementToDelete?.agreement_name}"?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
