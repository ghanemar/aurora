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
} from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { partnersService } from '../services/partners';
import { PartnerForm } from '../components/PartnerForm';
import type { Partner, PartnerCreate, PartnerUpdate } from '../types';

/**
 * Partners Page
 *
 * Features:
 * - List partners in MUI DataGrid
 * - Add/Edit/Delete partners
 * - Form validation
 * - Delete confirmation dialog
 * - Loading and error states
 */

export const PartnersPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedPartner, setSelectedPartner] = useState<Partner | undefined>();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [partnerToDelete, setPartnerToDelete] = useState<Partner | null>(null);

  // Fetch partners
  const {
    data: partnersData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['partners'],
    queryFn: () =>
      partnersService.getPartners({
        page: 1,
        page_size: 100,
      }),
    staleTime: 60 * 1000,
  });

  // Create partner mutation
  const createMutation = useMutation({
    mutationFn: (data: PartnerCreate) => partnersService.createPartner(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners'] });
      setFormOpen(false);
    },
  });

  // Update partner mutation
  const updateMutation = useMutation({
    mutationFn: ({
      partner_id,
      data,
    }: {
      partner_id: string;
      data: PartnerUpdate;
    }) => partnersService.updatePartner(partner_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners'] });
      setFormOpen(false);
    },
  });

  // Delete partner mutation
  const deleteMutation = useMutation({
    mutationFn: (partner_id: string) => partnersService.deletePartner(partner_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners'] });
      setDeleteDialogOpen(false);
      setPartnerToDelete(null);
    },
  });

  // Handlers
  const handleAdd = () => {
    setFormMode('create');
    setSelectedPartner(undefined);
    setFormOpen(true);
  };

  const handleEdit = (partner: Partner) => {
    setFormMode('edit');
    setSelectedPartner(partner);
    setFormOpen(true);
  };

  const handleDelete = (partner: Partner) => {
    setPartnerToDelete(partner);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (partnerToDelete) {
      deleteMutation.mutate(partnerToDelete.partner_id);
    }
  };

  const handleFormSubmit = (data: PartnerCreate | PartnerUpdate) => {
    if (formMode === 'create') {
      createMutation.mutate(data as PartnerCreate);
    } else if (selectedPartner) {
      updateMutation.mutate({
        partner_id: selectedPartner.partner_id,
        data: data as PartnerUpdate,
      });
    }
  };

  // DataGrid columns
  const columns: GridColDef<Partner>[] = [
    {
      field: 'partner_name',
      headerName: 'Partner Name',
      width: 200,
      flex: 1,
    },
    {
      field: 'legal_entity_name',
      headerName: 'Legal Entity',
      width: 200,
      flex: 1,
      valueGetter: (value) => value || '-',
    },
    {
      field: 'contact_email',
      headerName: 'Email',
      width: 250,
    },
    {
      field: 'contact_name',
      headerName: 'Contact Person',
      width: 180,
      valueGetter: (value) => value || '-',
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams<Partner>) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params: GridRenderCellParams<Partner>) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleEdit(params.row)}
            title="Edit Partner"
          >
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row)}
            title="Delete Partner"
            color="error"
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const partners = partnersData?.data || [];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" sx={{ bgcolor: 'background.paper' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/')} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, color: 'text.primary' }}>
            Partners
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
            disabled={createMutation.isPending}
          >
            Add Partner
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error loading partners: {error instanceof Error ? error.message : 'Unknown error'}
          </Alert>
        )}

        {(createMutation.isError || updateMutation.isError || deleteMutation.isError) && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Operation failed: {createMutation.error?.message || updateMutation.error?.message || deleteMutation.error?.message}
          </Alert>
        )}

        <Paper sx={{ p: 2 }}>
          <DataGrid
            rows={partners}
            columns={columns}
            loading={isLoading}
            getRowId={(row) => row.partner_id}
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

      {/* Partner Form Dialog */}
      <PartnerForm
        open={formOpen}
        mode={formMode}
        partner={selectedPartner}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete partner "{partnerToDelete?.partner_name}"?
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
