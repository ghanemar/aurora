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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  ContentCopy as CopyIcon,
  CheckCircle as ActivateIcon,
} from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agreementsService } from '../services/agreements';
import { partnersService } from '../services/partners';
import { AgreementWizard } from '../components/AgreementWizard';
import type {
  Agreement,
  AgreementStatus,
  AgreementWithRules,
  AgreementCreateWithRules,
} from '../types';

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

  // State for dialogs
  const [wizardOpen, setWizardOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // State for selected agreements
  const [agreementToDelete, setAgreementToDelete] = useState<Agreement | null>(null);
  const [selectedAgreement, setSelectedAgreement] = useState<AgreementWithRules | null>(null);
  const [initialWizardData, setInitialWizardData] = useState<AgreementWithRules | undefined>(undefined);

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
    queryKey: ['agreements'],
    queryFn: () =>
      agreementsService.getAgreements({
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

  // Create agreement mutation
  const createMutation = useMutation({
    mutationFn: (data: AgreementCreateWithRules) => agreementsService.createAgreementWithRules(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agreements'] });
      setWizardOpen(false);
      setInitialWizardData(undefined);
    },
  });

  // Activate agreement mutation
  const activateMutation = useMutation({
    mutationFn: (agreement_id: string) => agreementsService.activateAgreement(agreement_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agreements'] });
    },
  });

  // Handlers
  const handleAddNew = () => {
    setInitialWizardData(undefined);
    setWizardOpen(true);
  };

  const handleView = async (agreement: Agreement) => {
    const fullAgreement = await agreementsService.getAgreement(agreement.agreement_id);
    setSelectedAgreement(fullAgreement);
    setViewDialogOpen(true);
  };

  const handleCreateVersion = () => {
    if (selectedAgreement) {
      setInitialWizardData(selectedAgreement);
      setViewDialogOpen(false);
      setWizardOpen(true);
    }
  };

  const handleActivate = (agreement: Agreement) => {
    if (window.confirm(`Activate agreement "${agreement.agreement_name}"? This will make it active and start commission calculations.`)) {
      activateMutation.mutate(agreement.agreement_id);
    }
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

  const handleWizardSubmit = async (data: AgreementCreateWithRules) => {
    await createMutation.mutateAsync(data);
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
            onClick={() => handleView(params.row)}
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
            onClick={handleAddNew}
          >
            Add Agreement
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

      {/* Agreement Wizard */}
      {partnersData && (
        <AgreementWizard
          open={wizardOpen}
          onClose={() => {
            setWizardOpen(false);
            setInitialWizardData(undefined);
          }}
          onSubmit={handleWizardSubmit}
          partners={partnersData.data}
          initialData={initialWizardData}
          isSubmitting={createMutation.isPending}
        />
      )}

      {/* View Agreement Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Agreement Details</DialogTitle>
        <DialogContent>
          {selectedAgreement && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Agreement Information
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                    <Typography variant="body2" color="text.secondary">
                      Partner
                    </Typography>
                    <Typography variant="body1">
                      {getPartnerName(selectedAgreement.partner_id)}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                    <Chip
                      label={selectedAgreement.status}
                      color={getStatusColor(selectedAgreement.status)}
                      size="small"
                    />
                  </Box>
                  <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                    <Typography variant="body2" color="text.secondary">
                      Start Date
                    </Typography>
                    <Typography variant="body1">
                      {formatDate(selectedAgreement.effective_from)}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                    <Typography variant="body2" color="text.secondary">
                      End Date
                    </Typography>
                    <Typography variant="body1">
                      {selectedAgreement.effective_until
                        ? formatDate(selectedAgreement.effective_until)
                        : 'Ongoing'}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 100%' }}>
                    <Typography variant="body2" color="text.secondary">
                      Version
                    </Typography>
                    <Typography variant="body1">
                      {selectedAgreement.current_version}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Typography variant="h6" gutterBottom>
                Commission Rules
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rule Order</TableCell>
                      <TableCell>Revenue Component</TableCell>
                      <TableCell>Commission Rate</TableCell>
                      <TableCell>Attribution Method</TableCell>
                      <TableCell>Validator Key</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedAgreement.rules && selectedAgreement.rules.length > 0 ? (
                      selectedAgreement.rules.map((rule) => (
                        <TableRow key={rule.rule_id}>
                          <TableCell>{rule.rule_order}</TableCell>
                          <TableCell>{rule.revenue_component.replace(/_/g, ' ')}</TableCell>
                          <TableCell>
                            {rule.commission_rate_bps} bps (
                            {(rule.commission_rate_bps / 100).toFixed(2)}%)
                          </TableCell>
                          <TableCell>{rule.attribution_method.replace(/_/g, ' ')}</TableCell>
                          <TableCell>
                            {rule.validator_key || 'All validators'}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          No rules defined for this agreement
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {selectedAgreement?.status === 'DRAFT' && (
            <Button
              onClick={() => {
                if (selectedAgreement) {
                  handleActivate(selectedAgreement as Agreement);
                  setViewDialogOpen(false);
                }
              }}
              variant="contained"
              color="success"
              startIcon={<ActivateIcon />}
            >
              Activate Agreement
            </Button>
          )}
          <Button
            onClick={handleCreateVersion}
            variant="contained"
            startIcon={<CopyIcon />}
          >
            Create New Version
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create mutation error */}
      {createMutation.isError && (
        <Alert
          severity="error"
          sx={{ position: 'fixed', bottom: 16, right: 16, maxWidth: 400 }}
          onClose={() => createMutation.reset()}
        >
          Failed to create agreement: {createMutation.error?.message}
        </Alert>
      )}

      {/* Activate mutation error */}
      {activateMutation.isError && (
        <Alert
          severity="error"
          sx={{ position: 'fixed', bottom: 16, right: 16, maxWidth: 400 }}
          onClose={() => activateMutation.reset()}
        >
          Failed to activate agreement: {activateMutation.error?.message}
        </Alert>
      )}

      {/* Activate mutation success */}
      {activateMutation.isSuccess && (
        <Alert
          severity="success"
          sx={{ position: 'fixed', bottom: 16, right: 16, maxWidth: 400 }}
          onClose={() => activateMutation.reset()}
        >
          Agreement activated successfully!
        </Alert>
      )}
    </Box>
  );
};
