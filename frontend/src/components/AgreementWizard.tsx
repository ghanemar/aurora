import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Autocomplete,
  IconButton,
  Paper,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import type {
  Partner,
  AgreementCreateWithRules,
  AgreementStatus,
  RevenueComponent,
  AttributionMethod,
  AgreementWithRules,
} from '../types';

/**
 * Agreement Wizard Component
 *
 * Multi-step wizard for creating and editing agreements with commission rules.
 * Step 1: Agreement details (partner, name, dates, status)
 * Step 2: Rules configuration (multiple rules with add/remove)
 */

interface AgreementWizardProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: AgreementCreateWithRules) => Promise<void>;
  partners: Partner[];
  initialData?: AgreementWithRules;
  isSubmitting?: boolean;
}

interface RuleFormData {
  rule_order: number | '';
  revenue_component: RevenueComponent | '';
  commission_rate_bps: number | '';
  attribution_method: AttributionMethod | '';
  validator_key?: string;
}

const REVENUE_COMPONENTS: RevenueComponent[] = [
  'EXEC_FEES',
  'MEV_TIPS',
  'VOTE_REWARDS',
  'COMMISSION',
];

const ATTRIBUTION_METHODS: AttributionMethod[] = [
  'CLIENT_REVENUE',
  'STAKE_WEIGHT',
  'FIXED_SHARE',
];

const AGREEMENT_STATUSES: AgreementStatus[] = ['DRAFT', 'ACTIVE', 'SUSPENDED', 'TERMINATED'];

const steps = ['Agreement Details', 'Commission Rules'];

export const AgreementWizard: React.FC<AgreementWizardProps> = ({
  open,
  onClose,
  onSubmit,
  partners,
  initialData,
  isSubmitting = false,
}) => {
  const [activeStep, setActiveStep] = useState(0);

  // Step 1: Agreement details
  const [partnerId, setPartnerId] = useState<string>(initialData?.partner_id || '');
  const [agreementName, setAgreementName] = useState(initialData?.agreement_name || '');
  const [effectiveFrom, setEffectiveFrom] = useState<string>(
    initialData?.effective_from ? new Date(initialData.effective_from).toISOString().split('T')[0] : ''
  );
  const [effectiveUntil, setEffectiveUntil] = useState<string>(
    initialData?.effective_until ? new Date(initialData.effective_until).toISOString().split('T')[0] : ''
  );
  const [status, setStatus] = useState<AgreementStatus>(initialData?.status || 'DRAFT');

  // Step 2: Rules
  const [rules, setRules] = useState<RuleFormData[]>(
    initialData?.rules.length
      ? initialData.rules.map((r, index) => ({
          rule_order: r.rule_order || index,
          revenue_component: r.revenue_component,
          commission_rate_bps: r.commission_rate_bps,
          attribution_method: r.attribution_method,
          validator_key: r.validator_key || undefined,
        }))
      : [
          {
            rule_order: 0,
            revenue_component: '',
            commission_rate_bps: '',
            attribution_method: '',
            validator_key: '',
          },
        ]
  );

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleNext = () => {
    if (activeStep === 0) {
      // Validate step 1
      const newErrors: Record<string, string> = {};

      if (!partnerId) newErrors.partnerId = 'Partner is required';
      if (!agreementName) newErrors.agreementName = 'Agreement name is required';
      if (!effectiveFrom) newErrors.effectiveFrom = 'Start date is required';
      if (effectiveUntil && effectiveFrom && new Date(effectiveUntil) <= new Date(effectiveFrom)) {
        newErrors.effectiveUntil = 'End date must be after start date';
      }

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        return;
      }

      setErrors({});
      setActiveStep(1);
    }
  };

  const handleBack = () => {
    setActiveStep(0);
    setErrors({});
  };

  const handleSubmit = async () => {
    // Validate step 2
    const newErrors: Record<string, string> = {};

    if (rules.length === 0) {
      newErrors.rules = 'At least one rule is required';
    }

    rules.forEach((rule, index) => {
      if (rule.rule_order === '' || rule.rule_order < 0) {
        newErrors[`rule_${index}_order`] = 'Rule order must be 0 or greater';
      }
      if (!rule.revenue_component) {
        newErrors[`rule_${index}_revenue_component`] = 'Revenue component is required';
      }
      if (rule.commission_rate_bps === '' || rule.commission_rate_bps < 0 || rule.commission_rate_bps > 10000) {
        newErrors[`rule_${index}_commission_rate_bps`] = 'Commission rate must be between 0 and 10000 bps';
      }
      if (!rule.attribution_method) {
        newErrors[`rule_${index}_attribution_method`] = 'Attribution method is required';
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});

    const data: AgreementCreateWithRules = {
      partner_id: partnerId,
      agreement_name: agreementName,
      effective_from: new Date(effectiveFrom).toISOString(),
      effective_until: effectiveUntil ? new Date(effectiveUntil).toISOString() : undefined,
      status,
      rules: rules.map((rule) => ({
        rule_order: Number(rule.rule_order),
        revenue_component: rule.revenue_component as RevenueComponent,
        commission_rate_bps: Number(rule.commission_rate_bps),
        attribution_method: rule.attribution_method as AttributionMethod,
        validator_key: rule.validator_key || undefined,
      })),
    };

    await onSubmit(data);
  };

  const addRule = () => {
    setRules([
      ...rules,
      {
        rule_order: rules.length,
        revenue_component: '',
        commission_rate_bps: '',
        attribution_method: '',
        validator_key: '',
      },
    ]);
  };

  const removeRule = (index: number) => {
    if (rules.length > 1) {
      setRules(rules.filter((_, i) => i !== index));
    }
  };

  const updateRule = (index: number, field: keyof RuleFormData, value: any) => {
    const newRules = [...rules];
    newRules[index] = { ...newRules[index], [field]: value };
    setRules(newRules);
  };

  const handleClose = () => {
    // Reset form
    setActiveStep(0);
    setPartnerId(initialData?.partner_id || '');
    setAgreementName(initialData?.agreement_name || '');
    setEffectiveFrom(initialData?.effective_from ? new Date(initialData.effective_from).toISOString().split('T')[0] : '');
    setEffectiveUntil(initialData?.effective_until ? new Date(initialData.effective_until).toISOString().split('T')[0] : '');
    setStatus(initialData?.status || 'DRAFT');
    setRules(
      initialData?.rules.length
        ? initialData.rules.map((r, index) => ({
            rule_order: r.rule_order || index,
            revenue_component: r.revenue_component,
            commission_rate_bps: r.commission_rate_bps,
            attribution_method: r.attribution_method,
            validator_key: r.validator_key || undefined,
          }))
        : [
            {
              rule_order: 0,
              revenue_component: '',
              commission_rate_bps: '',
              attribution_method: '',
              validator_key: '',
            },
          ]
    );
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {initialData ? 'Create New Agreement Version' : 'Add Agreement'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {activeStep === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Autocomplete
                options={partners}
                getOptionLabel={(option) => option.partner_name}
                value={partners.find((p) => p.partner_id === partnerId) || null}
                onChange={(_, newValue) => setPartnerId(newValue?.partner_id || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Partner"
                    required
                    error={!!errors.partnerId}
                    helperText={errors.partnerId}
                  />
                )}
              />

              <TextField
                fullWidth
                label="Agreement Name"
                required
                value={agreementName}
                onChange={(e) => setAgreementName(e.target.value)}
                error={!!errors.agreementName}
                helperText={errors.agreementName}
              />

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                  <TextField
                    fullWidth
                    label="Start Date"
                    type="date"
                    required
                    value={effectiveFrom}
                    onChange={(e) => setEffectiveFrom(e.target.value)}
                    error={!!errors.effectiveFrom}
                    helperText={errors.effectiveFrom}
                    InputLabelProps={{ shrink: true }}
                  />
                </Box>

                <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                  <TextField
                    fullWidth
                    label="End Date (Optional)"
                    type="date"
                    value={effectiveUntil}
                    onChange={(e) => setEffectiveUntil(e.target.value)}
                    error={!!errors.effectiveUntil}
                    helperText={errors.effectiveUntil || 'Leave empty for ongoing agreements'}
                    InputLabelProps={{ shrink: true }}
                  />
                </Box>
              </Box>

              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as AgreementStatus)}
                  label="Status"
                >
                  {AGREEMENT_STATUSES.map((s) => (
                    <MenuItem key={s} value={s}>
                      {s}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          )}

          {activeStep === 1 && (
            <Box>
              {errors.rules && (
                <Typography color="error" sx={{ mb: 2 }}>
                  {errors.rules}
                </Typography>
              )}

              {rules.map((rule, index) => (
                <Paper key={index} sx={{ p: 2, mb: 2, position: 'relative' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6">Rule {index + 1}</Typography>
                    {rules.length > 1 && (
                      <IconButton
                        onClick={() => removeRule(index)}
                        color="error"
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Rule Order"
                      required
                      type="number"
                      value={rule.rule_order}
                      onChange={(e) => updateRule(index, 'rule_order', e.target.value === '' ? '' : Number(e.target.value))}
                      error={!!errors[`rule_${index}_order`]}
                      helperText={errors[`rule_${index}_order`] || 'Execution order for this rule (0-based)'}
                      inputProps={{ min: 0 }}
                    />

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                        <FormControl fullWidth error={!!errors[`rule_${index}_revenue_component`]}>
                          <InputLabel>Revenue Component *</InputLabel>
                          <Select
                            value={rule.revenue_component}
                            onChange={(e) =>
                              updateRule(index, 'revenue_component', e.target.value)
                            }
                            label="Revenue Component *"
                          >
                            {REVENUE_COMPONENTS.map((rc) => (
                              <MenuItem key={rc} value={rc}>
                                {rc.replace('_', ' ')}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors[`rule_${index}_revenue_component`] && (
                            <FormHelperText>
                              {errors[`rule_${index}_revenue_component`]}
                            </FormHelperText>
                          )}
                        </FormControl>
                      </Box>

                      <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                        <TextField
                          fullWidth
                          label="Commission Rate (bps)"
                          required
                          type="number"
                          value={rule.commission_rate_bps}
                          onChange={(e) =>
                            updateRule(
                              index,
                              'commission_rate_bps',
                              e.target.value === '' ? '' : Number(e.target.value)
                            )
                          }
                          error={!!errors[`rule_${index}_commission_rate_bps`]}
                          helperText={
                            errors[`rule_${index}_commission_rate_bps`] ||
                            `0-10000 bps (e.g., 500 = 5%)`
                          }
                          inputProps={{ min: 0, max: 10000 }}
                        />
                      </Box>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                        <FormControl fullWidth error={!!errors[`rule_${index}_attribution_method`]}>
                          <InputLabel>Attribution Method *</InputLabel>
                          <Select
                            value={rule.attribution_method}
                            onChange={(e) =>
                              updateRule(index, 'attribution_method', e.target.value)
                            }
                            label="Attribution Method *"
                          >
                            {ATTRIBUTION_METHODS.map((am) => (
                              <MenuItem key={am} value={am}>
                                {am.replace('_', ' ')}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors[`rule_${index}_attribution_method`] && (
                            <FormHelperText>
                              {errors[`rule_${index}_attribution_method`]}
                            </FormHelperText>
                          )}
                        </FormControl>
                      </Box>

                      <Box sx={{ flex: '1 1 45%', minWidth: '200px' }}>
                        <TextField
                          fullWidth
                          label="Validator Key (Optional)"
                          value={rule.validator_key || ''}
                          onChange={(e) =>
                            updateRule(index, 'validator_key', e.target.value)
                          }
                          helperText="Specific validator key or leave empty for all validators"
                        />
                      </Box>
                    </Box>
                  </Box>
                </Paper>
              ))}

              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={addRule}
                fullWidth
                sx={{ mt: 2 }}
              >
                Add Rule
              </Button>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={isSubmitting}>
          Cancel
        </Button>
        {activeStep === 1 && (
          <Button onClick={handleBack} disabled={isSubmitting}>
            Back
          </Button>
        )}
        {activeStep === 0 ? (
          <Button onClick={handleNext} variant="contained">
            Next
          </Button>
        ) : (
          <Button onClick={handleSubmit} variant="contained" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
