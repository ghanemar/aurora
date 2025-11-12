import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Autocomplete,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Calculate as CalculateIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { partnersService } from '../services/partners';
import { sampleCommissionsService } from '../services/sampleCommissions';
import type { Partner, SampleEpoch } from '../types';
import { AppLayout } from '../components/AppLayout';

/**
 * Sample Commissions Page
 *
 * Features:
 * - Partner selection (autocomplete dropdown)
 * - Epoch range selection (start and end epoch dropdowns)
 * - Commission rate input (default 10%)
 * - Calculate button to trigger commission calculation
 * - Results display with summary and per-epoch breakdown
 */

export const SampleCommissionsPage: React.FC = () => {
  // State for selections
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);
  const [startEpoch, setStartEpoch] = useState<SampleEpoch | null>(null);
  const [endEpoch, setEndEpoch] = useState<SampleEpoch | null>(null);
  const [commissionRate, setCommissionRate] = useState<string>('0.10');
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

  // Fetch epochs for dropdown
  const {
    data: epochsData,
    isLoading: epochsLoading,
    isError: epochsError,
  } = useQuery({
    queryKey: ['sample-epochs'],
    queryFn: () => sampleCommissionsService.getEpochs(),
    staleTime: 60 * 1000,
  });

  // Fetch commission calculation (only when calculate is clicked)
  const {
    data: calculation,
    isLoading: calculationLoading,
    isError: calculationError,
    error: calculationErrorMsg,
  } = useQuery({
    queryKey: [
      'sample-commission-calculation',
      selectedPartner?.partner_id,
      startEpoch?.epoch,
      endEpoch?.epoch,
      commissionRate,
    ],
    queryFn: () =>
      sampleCommissionsService.calculatePartnerCommission({
        partner_id: selectedPartner!.partner_id,
        start_epoch: startEpoch!.epoch,
        end_epoch: endEpoch!.epoch,
        commission_rate: parseFloat(commissionRate),
      }),
    enabled:
      calculationTriggered &&
      !!selectedPartner &&
      !!startEpoch &&
      !!endEpoch &&
      !!commissionRate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const partners = partnersData?.data || [];
  const epochs = epochsData?.epochs || [];

  // Filter end epoch options based on start epoch
  const availableEndEpochs = startEpoch
    ? epochs.filter((e) => e.epoch >= startEpoch.epoch)
    : epochs;

  const handleCalculate = () => {
    if (selectedPartner && startEpoch && endEpoch && commissionRate) {
      // Validate epoch range
      if (endEpoch.epoch < startEpoch.epoch) {
        alert('End epoch must be greater than or equal to start epoch');
        return;
      }
      setCalculationTriggered(true);
    }
  };

  const canCalculate =
    selectedPartner && startEpoch && endEpoch && commissionRate && !calculationLoading;
  const hasResults = calculationTriggered && calculation;

  // Format lamports to SOL
  const lamportsToSOL = (lamports: number) => (lamports / 1e9).toFixed(2);

  return (
    <AppLayout>
      <Box>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h4" gutterBottom>
            Sample Data Commission Calculator
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Calculate partner commissions using GlobalStake sample data (Epochs 800-860)
          </Typography>

          {/* Selection Panel */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configure Calculation
            </Typography>

            <Grid container spacing={3} sx={{ mt: 1 }}>
              {/* Partner Select */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Autocomplete
                  options={partners}
                  getOptionLabel={(partner) => partner.partner_name}
                  value={selectedPartner}
                  onChange={(_, newValue) => {
                    setSelectedPartner(newValue);
                    setCalculationTriggered(false);
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

              {/* Commission Rate */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Commission Rate"
                  value={commissionRate}
                  onChange={(e) => {
                    setCommissionRate(e.target.value);
                    setCalculationTriggered(false);
                  }}
                  type="number"
                  inputProps={{
                    step: 0.01,
                    min: 0,
                    max: 1,
                  }}
                  helperText="Enter as decimal (0.10 = 10%)"
                />
              </Grid>

              {/* Start Epoch Select */}
              <Grid size={{ xs: 12, md: 5 }}>
                <Autocomplete
                  options={epochs}
                  getOptionLabel={(epoch) => `Epoch ${epoch.epoch}`}
                  value={startEpoch}
                  onChange={(_, newValue) => {
                    setStartEpoch(newValue);
                    // Reset end epoch if it's before the new start epoch
                    if (endEpoch && newValue && endEpoch.epoch < newValue.epoch) {
                      setEndEpoch(null);
                    }
                    setCalculationTriggered(false);
                  }}
                  loading={epochsLoading}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Start Epoch"
                      placeholder="Select start epoch"
                      error={epochsError}
                      helperText={epochsError ? 'Failed to load epochs' : ''}
                      slotProps={{
                        input: {
                          ...params.InputProps,
                          endAdornment: (
                            <>
                              {epochsLoading ? (
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

              {/* End Epoch Select */}
              <Grid size={{ xs: 12, md: 5 }}>
                <Autocomplete
                  options={availableEndEpochs}
                  getOptionLabel={(epoch) => `Epoch ${epoch.epoch}`}
                  value={endEpoch}
                  onChange={(_, newValue) => {
                    setEndEpoch(newValue);
                    setCalculationTriggered(false);
                  }}
                  loading={epochsLoading}
                  disabled={!startEpoch}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="End Epoch"
                      placeholder={
                        startEpoch ? 'Select end epoch' : 'Select start epoch first'
                      }
                      error={epochsError}
                      helperText={
                        epochsError
                          ? 'Failed to load epochs'
                          : startEpoch
                            ? `Must be >= ${startEpoch.epoch}`
                            : ''
                      }
                      slotProps={{
                        input: {
                          ...params.InputProps,
                          endAdornment: (
                            <>
                              {epochsLoading ? (
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
                  disabled={!canCalculate}
                  sx={{ height: 56 }}
                >
                  {calculationLoading ? 'Calculating...' : 'Calculate'}
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Error States */}
          {calculationError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              Failed to calculate commission:{' '}
              {calculationErrorMsg instanceof Error
                ? calculationErrorMsg.message
                : 'Unknown error'}
            </Alert>
          )}

          {/* Results Display */}
          {hasResults && (
            <>
              {/* Summary Card */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Commission Summary
                </Typography>

                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Partner
                    </Typography>
                    <Typography variant="h6">{calculation.partner_name}</Typography>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Epoch Range
                    </Typography>
                    <Typography variant="h6">
                      {calculation.start_epoch} - {calculation.end_epoch}
                      <Chip
                        label={`${calculation.epoch_count} epochs`}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Commission Rate
                    </Typography>
                    <Typography variant="h6">
                      {(parseFloat(calculation.commission_rate) * 100).toFixed(1)}%
                    </Typography>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Commission
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {lamportsToSOL(calculation.total_commission_lamports)} SOL
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Partner Stake
                  </Typography>
                  <Typography variant="body1">
                    {lamportsToSOL(calculation.total_partner_stake_lamports)} SOL
                  </Typography>

                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Total Partner Rewards
                  </Typography>
                  <Typography variant="body1">
                    {lamportsToSOL(calculation.total_partner_rewards_lamports)} SOL
                  </Typography>
                </Box>
              </Paper>

              {/* Per-Epoch Details */}
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Per-Epoch Breakdown
                </Typography>

                <Box sx={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #ddd' }}>
                        <th style={{ padding: '8px', textAlign: 'left' }}>Epoch</th>
                        <th style={{ padding: '8px', textAlign: 'right' }}>
                          Stake %
                        </th>
                        <th style={{ padding: '8px', textAlign: 'right' }}>
                          Partner Stake (SOL)
                        </th>
                        <th style={{ padding: '8px', textAlign: 'right' }}>
                          Partner Rewards (SOL)
                        </th>
                        <th style={{ padding: '8px', textAlign: 'right' }}>
                          Commission (SOL)
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {calculation.epoch_details.map((detail) => (
                        <tr
                          key={detail.epoch}
                          style={{ borderBottom: '1px solid #eee' }}
                        >
                          <td style={{ padding: '8px' }}>{detail.epoch}</td>
                          <td style={{ padding: '8px', textAlign: 'right' }}>
                            {(parseFloat(detail.stake_percentage) * 100).toFixed(2)}%
                          </td>
                          <td style={{ padding: '8px', textAlign: 'right' }}>
                            {lamportsToSOL(detail.partner_stake_lamports)}
                          </td>
                          <td style={{ padding: '8px', textAlign: 'right' }}>
                            {lamportsToSOL(detail.partner_rewards_lamports)}
                          </td>
                          <td
                            style={{
                              padding: '8px',
                              textAlign: 'right',
                              fontWeight: 'bold',
                            }}
                          >
                            {lamportsToSOL(detail.partner_commission_lamports)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Box>
              </Paper>
            </>
          )}
        </Container>
      </Box>
    </AppLayout>
  );
};
