import React, { useState, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  AppBar,
  Toolbar,
  Button,
  Paper,
  Alert,
  MenuItem,
  TextField,
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
import { validatorsService } from '../services/validators';
import { ValidatorForm } from '../components/ValidatorForm';
import type { Validator, ValidatorCreate, ValidatorUpdate } from '../types';
import YAML from 'yaml';

/**
 * Validators Page
 *
 * Features:
 * - List validators in MUI DataGrid
 * - Filter by chain
 * - Add/Edit/Delete validators
 * - Form validation
 * - Delete confirmation dialog
 * - Loading and error states
 */

interface ChainConfig {
  chain_id: string;
  name: string;
}

export const ValidatorsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [chainFilter, setChainFilter] = useState<string>('');
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedValidator, setSelectedValidator] = useState<Validator | undefined>();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [validatorToDelete, setValidatorToDelete] = useState<Validator | null>(null);

  // Fetch chains configuration
  const { data: chains = [] } = useQuery({
    queryKey: ['chains-config'],
    queryFn: async (): Promise<ChainConfig[]> => {
      try {
        const response = await fetch('/config/chains.yaml');
        if (!response.ok) throw new Error('Failed to fetch chains');
        const text = await response.text();
        const config = YAML.parse(text);
        return config.chains;
      } catch (error) {
        return [
          { chain_id: 'solana-mainnet', name: 'Solana Mainnet' },
          { chain_id: 'solana-testnet', name: 'Solana Testnet' },
        ];
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  // Fetch validators
  const {
    data: validatorsData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['validators', chainFilter],
    queryFn: () =>
      validatorsService.getValidators({
        chain_id: chainFilter || undefined,
        page: 1,
        page_size: 100,
      }),
    staleTime: 60 * 1000,
  });

  // Create validator mutation
  const createMutation = useMutation({
    mutationFn: (data: ValidatorCreate) => validatorsService.createValidator(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validators'] });
      setFormOpen(false);
    },
  });

  // Update validator mutation
  const updateMutation = useMutation({
    mutationFn: ({
      validator_key,
      chain_id,
      data,
    }: {
      validator_key: string;
      chain_id: string;
      data: ValidatorUpdate;
    }) => validatorsService.updateValidator(validator_key, chain_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validators'] });
      setFormOpen(false);
    },
  });

  // Delete validator mutation
  const deleteMutation = useMutation({
    mutationFn: ({
      validator_key,
      chain_id,
    }: {
      validator_key: string;
      chain_id: string;
    }) => validatorsService.deleteValidator(validator_key, chain_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['validators'] });
      setDeleteDialogOpen(false);
      setValidatorToDelete(null);
    },
  });

  // Handlers
  const handleAdd = () => {
    setFormMode('create');
    setSelectedValidator(undefined);
    setFormOpen(true);
  };

  const handleEdit = (validator: Validator) => {
    setFormMode('edit');
    setSelectedValidator(validator);
    setFormOpen(true);
  };

  const handleDelete = (validator: Validator) => {
    setValidatorToDelete(validator);
    setDeleteDialogOpen(true);
  };

  const handleFormSubmit = async (data: ValidatorCreate | ValidatorUpdate) => {
    if (formMode === 'create') {
      await createMutation.mutateAsync(data as ValidatorCreate);
    } else if (selectedValidator) {
      await updateMutation.mutateAsync({
        validator_key: selectedValidator.validator_key,
        chain_id: selectedValidator.chain_id,
        data: data as ValidatorUpdate,
      });
    }
  };

  const handleDeleteConfirm = async () => {
    if (validatorToDelete) {
      await deleteMutation.mutateAsync({
        validator_key: validatorToDelete.validator_key,
        chain_id: validatorToDelete.chain_id,
      });
    }
  };

  // Find chain name by ID
  const getChainName = (chainId: string) => {
    const chain = chains.find((c) => c.chain_id === chainId);
    return chain?.name || chainId;
  };

  // DataGrid columns
  const columns: GridColDef<Validator>[] = useMemo(
    () => [
      {
        field: 'validator_key',
        headerName: 'Validator Key',
        flex: 2,
        minWidth: 200,
      },
      {
        field: 'chain_id',
        headerName: 'Chain',
        flex: 1,
        minWidth: 150,
        renderCell: (params: GridRenderCellParams<Validator>) => {
          const chainName = getChainName(params.row.chain_id);
          return <Chip label={chainName} size="small" color="primary" />;
        },
      },
      {
        field: 'description',
        headerName: 'Description',
        flex: 2,
        minWidth: 200,
        renderCell: (params: GridRenderCellParams<Validator>) => (
          <Typography variant="body2" noWrap>
            {params.row.description || '—'}
          </Typography>
        ),
      },
      {
        field: 'is_active',
        headerName: 'Status',
        flex: 0.5,
        minWidth: 100,
        renderCell: (params: GridRenderCellParams<Validator>) => (
          <Chip
            label={params.row.is_active ? 'Active' : 'Inactive'}
            size="small"
            color={params.row.is_active ? 'success' : 'default'}
          />
        ),
      },
      {
        field: 'actions',
        headerName: 'Actions',
        flex: 0.8,
        minWidth: 120,
        sortable: false,
        filterable: false,
        renderCell: (params: GridRenderCellParams<Validator>) => (
          <Box>
            <IconButton
              size="small"
              onClick={() => handleEdit(params.row)}
              color="primary"
              title="Edit"
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleDelete(params.row)}
              color="error"
              title="Delete"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        ),
      },
    ],
    [chains]
  );

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* AppBar */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <BackIcon />
          </IconButton>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            GLOBALSTAKE
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h4" fontWeight={700}>
            Validators
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
            sx={{ textTransform: 'none' }}
          >
            Add Validator
          </Button>
        </Box>

        {/* Filter */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <TextField
            select
            label="Filter by Chain"
            value={chainFilter}
            onChange={(e) => setChainFilter(e.target.value)}
            sx={{ minWidth: 250 }}
            size="small"
          >
            <MenuItem value="">All Chains</MenuItem>
            {chains.map((chain) => (
              <MenuItem key={chain.chain_id} value={chain.chain_id}>
                {chain.name}
              </MenuItem>
            ))}
          </TextField>
        </Paper>

        {/* Error State */}
        {isError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to load validators: {(error as Error)?.message || 'Unknown error'}
          </Alert>
        )}

        {/* DataGrid */}
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={validatorsData?.data || []}
            columns={columns}
            loading={isLoading}
            getRowId={(row) => `${row.validator_key}-${row.chain_id}`}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{
              pagination: { paginationModel: { pageSize: 25 } },
            }}
            disableRowSelectionOnClick
            sx={{
              border: 'none',
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
            }}
          />
        </Paper>
      </Container>

      {/* Validator Form Dialog */}
      <ValidatorForm
        open={formOpen}
        mode={formMode}
        validator={selectedValidator}
        chains={chains}
        onClose={() => setFormOpen(false)}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this validator?
          </DialogContentText>
          {validatorToDelete && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Key:</strong> {validatorToDelete.validator_key}
              </Typography>
              <Typography variant="body2">
                <strong>Chain:</strong> {getChainName(validatorToDelete.chain_id)}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
