import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Paper,
  Grid,
  Autocomplete,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Calculate as CalculateIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { partnersService } from '../services/partners';
import { commissionsService } from '../services/commissions';
import { CommissionResults } from '../components/CommissionResults';
import type { Partner, Period } from '../types';

/**
 * Commissions Page
 *
 * Features:
 * - Partner selection (autocomplete dropdown)
 * - Period/Epoch selection (autocomplete dropdown)
 * - Calculate button to trigger commission calculation
 * - Results display with summary and detailed breakdown
 * - Handles edge cases (no data, no agreement)
 */

export const CommissionsPage: React.FC = () => {
  const navigate = useNavigate();

  // State for selections
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<Period | null>(null);
  const [calculationTriggered, setCalculationTriggered] = useState(false);

  // Fetch partners for dropdown
  const {
    data: partnersData,
    isLoading: partnersLoading,
    isError: partnersError,
  } = useQuery({
    queryKey: ['partners'],
    queryFn: () =>
      partnersService.getPartners({
        page: 1,
        page_size: 100,
      }),
    staleTime: 60 * 1000,
  });

  // Fetch periods for dropdown
  const {
    data: periodsData,
    isLoading: periodsLoading,
    isError: periodsError,
  } = useQuery({
    queryKey: ['periods'],
    queryFn: () =>
      commissionsService.getPeriods({
        page: 1,
        page_size: 100,
      }),
    staleTime: 60 * 1000,
  });

  // Fetch commission breakdown (only when calculate is clicked)
  const {
    data: breakdown,
    isLoading: breakdownLoading,
    isError: breakdownError,
    error: breakdownErrorMsg,
  } = useQuery({
    queryKey: [
      'commission-breakdown',
      selectedPartner?.partner_id,
      selectedPeriod?.period_id,
    ],
    queryFn: () =>
      commissionsService.getCommissionBreakdown({
        partner_id: selectedPartner!.partner_id,
        period_id: selectedPeriod!.period_id,
      }),
    enabled: calculationTriggered && !!selectedPartner && !!selectedPeriod,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const partners = partnersData?.data || [];
  const periods = periodsData?.data || [];

  const handleCalculate = () => {
    if (selectedPartner && selectedPeriod) {
      setCalculationTriggered(true);
    }
  };

  const canCalculate = selectedPartner && selectedPeriod;
  const hasResults = calculationTriggered && breakdown;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" sx={{ bgcolor: 'background.paper' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/')} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, color: 'text.primary' }}>
            Commission Calculator
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Selection Panel */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Select Partner and Period
          </Typography>

          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* Partner Select */}
            <Grid size={{ xs: 12, md: 5 }}>
              <Autocomplete
                options={partners}
                getOptionLabel={(partner) => partner.partner_name}
                value={selectedPartner}
                onChange={(_, newValue) => {
                  setSelectedPartner(newValue);
                  setCalculationTriggered(false); // Reset calculation when partner changes
                }}
                loading={partnersLoading}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Partner"
                    placeholder="Select a partner"
                    error={partnersError}
                    helperText={partnersError ? 'Failed to load partners' : ''}
                    slotProps={{
                      input: {
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {partnersLoading ? (
                              <CircularProgress color="inherit" size={20} />
                            ) : null}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      },
                    }}
                  />
                )}
              />
            </Grid>

            {/* Period Select */}
            <Grid size={{ xs: 12, md: 5 }}>
              <Autocomplete
                options={periods}
                getOptionLabel={(period) =>
                  `${period.chain_id} - Epoch ${period.epoch_number ?? 'N/A'} (${new Date(
                    period.start_time
                  ).toLocaleDateString()})`
                }
                value={selectedPeriod}
                onChange={(_, newValue) => {
                  setSelectedPeriod(newValue);
                  setCalculationTriggered(false); // Reset calculation when period changes
                }}
                loading={periodsLoading}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Period / Epoch"
                    placeholder="Select a period"
                    error={periodsError}
                    helperText={periodsError ? 'Failed to load periods' : ''}
                    slotProps={{
                      input: {
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {periodsLoading ? (
                              <CircularProgress color="inherit" size={20} />
                            ) : null}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      },
                    }}
                  />
                )}
              />
            </Grid>

            {/* Calculate Button */}
            <Grid size={{ xs: 12, md: 2 }}>
              <Button
                variant="contained"
                fullWidth
                startIcon={<CalculateIcon />}
                onClick={handleCalculate}
                disabled={!canCalculate || breakdownLoading}
                sx={{ height: 56 }}
              >
                {breakdownLoading ? 'Calculating...' : 'Calculate'}
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Error States */}
        {breakdownError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to calculate commissions:{' '}
            {breakdownErrorMsg instanceof Error
              ? breakdownErrorMsg.message
              : 'Unknown error'}
          </Alert>
        )}

        {/* No Data State */}
        {calculationTriggered &&
          !breakdownLoading &&
          !breakdownError &&
          breakdown &&
          breakdown.lines.length === 0 && (
            <Alert severity="info" sx={{ mb: 3 }}>
              No commission data found for the selected partner and period. This
              could mean:
              <ul>
                <li>No active agreement exists for this partner</li>
                <li>No revenue data available for this period</li>
                <li>Agreement rules don't match any validators in this period</li>
              </ul>
            </Alert>
          )}

        {/* Results Display */}
        {hasResults && breakdown.lines.length > 0 && (
          <CommissionResults breakdown={breakdown} loading={breakdownLoading} />
        )}
      </Container>
    </Box>
  );
};
