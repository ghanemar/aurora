import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import type { CommissionLine, CommissionBreakdown } from '../types';

/**
 * Commission Results Component
 *
 * Displays commission calculation results with:
 * - Summary card showing total and component breakdown
 * - DataGrid with validator-level commission lines
 * - Currency formatting (lamports → SOL)
 * - Commission rate display (bps → %)
 */

interface CommissionResultsProps {
  breakdown: CommissionBreakdown;
  loading?: boolean;
}

/**
 * Format native amount (lamports) to SOL with 9 decimal precision
 */
const formatSol = (lamports: string): string => {
  const sol = Number(lamports) / 1_000_000_000;
  return sol.toFixed(9);
};

/**
 * Format commission rate from basis points to percentage
 */
const formatRate = (bps: number): string => {
  return `${(bps / 100).toFixed(2)}%`;
};

export const CommissionResults: React.FC<CommissionResultsProps> = ({
  breakdown,
  loading = false,
}) => {
  // DataGrid columns for commission lines
  const columns: GridColDef<CommissionLine>[] = [
    {
      field: 'validator_key',
      headerName: 'Validator',
      width: 250,
      flex: 1,
    },
    {
      field: 'chain_id',
      headerName: 'Chain',
      width: 100,
    },
    {
      field: 'revenue_component',
      headerName: 'Component',
      width: 130,
    },
    {
      field: 'base_amount_native',
      headerName: 'Base Amount (SOL)',
      width: 180,
      type: 'number',
      valueGetter: (value) => formatSol(value),
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'commission_rate_bps',
      headerName: 'Rate',
      width: 100,
      type: 'number',
      valueGetter: (value) => formatRate(value),
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'commission_native',
      headerName: 'Commission (SOL)',
      width: 180,
      type: 'number',
      valueGetter: (value) => formatSol(value),
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'attribution_method',
      headerName: 'Attribution',
      width: 150,
    },
  ];

  // Add unique IDs for DataGrid rows
  const rowsWithIds = breakdown.lines.map((line, index) => ({
    ...line,
    id: `${line.validator_key}-${line.revenue_component}-${index}`,
  }));

  return (
    <Box>
      {/* Summary Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Commission Summary
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Total Commission
              </Typography>
              <Typography variant="h5" color="primary">
                {formatSol(breakdown.total_commission)} SOL
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Execution Fees
              </Typography>
              <Typography variant="h6">
                {formatSol(breakdown.exec_fees_commission)} SOL
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="body2" color="text.secondary">
                MEV
              </Typography>
              <Typography variant="h6">
                {formatSol(breakdown.mev_commission)} SOL
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Rewards
              </Typography>
              <Typography variant="h6">
                {formatSol(breakdown.rewards_commission)} SOL
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Commission Lines DataGrid */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ px: 1 }}>
          Commission Lines
        </Typography>
        <DataGrid
          rows={rowsWithIds}
          columns={columns}
          loading={loading}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 25, page: 0 },
            },
            sorting: {
              sortModel: [{ field: 'validator_key', sort: 'asc' }],
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
    </Box>
  );
};
