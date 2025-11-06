import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  FormControlLabel,
  Checkbox,
  Paper,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useBulkUploadWallets } from '../hooks/usePartnerWallets';
import { parseWalletCSV } from '../utils/walletValidation';
import { downloadWalletTemplate } from '../utils/csvTemplate';
import type { BulkUploadResult } from '../types';

/**
 * Bulk Upload Wallets Dialog Component
 *
 * Features:
 * - CSV file upload (drag & drop or click)
 * - Client-side CSV validation
 * - Upload progress
 * - Results display (success, skipped, errors)
 * - Template download
 */

interface BulkUploadWalletsDialogProps {
  open: boolean;
  partnerId: string;
  onClose: () => void;
}

export const BulkUploadWalletsDialog: React.FC<BulkUploadWalletsDialogProps> = ({
  open,
  partnerId,
  onClose,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [validationErrors, setValidationErrors] = useState<
    Array<{ row: number; error: string }>
  >([]);
  const [uploadResult, setUploadResult] = useState<BulkUploadResult | null>(null);

  const uploadMutation = useBulkUploadWallets(partnerId);

  const handleFileSelect = async (file: File | null) => {
    setSelectedFile(file);
    setValidationErrors([]);
    setUploadResult(null);

    if (file) {
      // Client-side validation
      try {
        const result = await parseWalletCSV(file);
        if (result.errors.length > 0) {
          setValidationErrors(result.errors);
        }
      } catch (error) {
        console.error('CSV parse error:', error);
        setValidationErrors([{
          row: 0,
          error: 'Failed to parse CSV file. Please check the format.',
        }]);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    handleFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'text/csv') {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        skipDuplicates,
      });
      setUploadResult(result);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setValidationErrors([]);
    setUploadResult(null);
    uploadMutation.reset();
    onClose();
  };

  const handleDownloadTemplate = () => {
    downloadWalletTemplate();
  };

  const canUpload =
    selectedFile &&
    validationErrors.length === 0 &&
    !uploadMutation.isPending &&
    !uploadResult;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Bulk Upload Wallets</DialogTitle>
      <DialogContent>
        {/* Template Download */}
        <Alert severity="info" sx={{ mb: 2 }} icon={<DownloadIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="body2">
              Download the CSV template to get started
            </Typography>
            <Button
              size="small"
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
            >
              Download Template
            </Button>
          </Box>
        </Alert>

        {/* File Upload Area */}
        {!uploadResult && (
          <>
            <Paper
              variant="outlined"
              sx={{
                p: 4,
                textAlign: 'center',
                border: '2px dashed',
                borderColor: selectedFile ? 'primary.main' : 'divider',
                bgcolor: selectedFile ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                },
              }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => document.getElementById('csv-file-input')?.click()}
            >
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {selectedFile ? selectedFile.name : 'Drag & Drop CSV File'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to browse
              </Typography>
              <input
                id="csv-file-input"
                type="file"
                accept=".csv"
                hidden
                onChange={handleFileChange}
              />
            </Paper>

            {/* Options */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={skipDuplicates}
                  onChange={(e) => setSkipDuplicates(e.target.checked)}
                />
              }
              label="Skip duplicate wallets (already assigned to another partner)"
              sx={{ mt: 2 }}
            />

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
              <Alert severity="error" sx={{ mt: 2 }} icon={<ErrorIcon />}>
                <Typography variant="subtitle2" gutterBottom>
                  CSV Validation Errors ({validationErrors.length}):
                </Typography>
                <List dense>
                  {validationErrors.slice(0, 10).map((error, idx) => (
                    <ListItem key={idx} disablePadding>
                      <ListItemText
                        primary={`Row ${error.row}: ${error.error}`}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                  {validationErrors.length > 10 && (
                    <ListItem disablePadding>
                      <ListItemText
                        primary={`... and ${validationErrors.length - 10} more errors`}
                        primaryTypographyProps={{ variant: 'body2', fontStyle: 'italic' }}
                      />
                    </ListItem>
                  )}
                </List>
              </Alert>
            )}

            {/* Upload Progress */}
            {uploadMutation.isPending && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Uploading...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            {/* Upload Error */}
            {uploadMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Upload failed: {uploadMutation.error?.message}
              </Alert>
            )}
          </>
        )}

        {/* Upload Results */}
        {uploadResult && (
          <Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip
                icon={<SuccessIcon />}
                label={`${uploadResult.success} Created`}
                color="success"
                variant="outlined"
              />
              <Chip
                icon={<WarningIcon />}
                label={`${uploadResult.skipped} Skipped`}
                color="warning"
                variant="outlined"
              />
              <Chip
                icon={<ErrorIcon />}
                label={`${uploadResult.errors.length} Errors`}
                color="error"
                variant="outlined"
              />
            </Box>

            {/* Skipped Wallets */}
            {uploadResult.skipped > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Skipped Wallets:
                </Typography>
                <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto', p: 1 }}>
                  <List dense>
                    {uploadResult.errors
                      .filter((e) => e.existing_partner)
                      .map((error, idx) => (
                        <ListItem key={idx} disablePadding>
                          <ListItemText
                            primary={`Row ${error.row}: ${error.wallet_address || 'N/A'}`}
                            secondary={`Already assigned to: ${error.existing_partner}`}
                            primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                  </List>
                </Paper>
              </Box>
            )}

            {/* Error Details */}
            {uploadResult.errors.filter((e) => !e.existing_partner).length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Errors:
                </Typography>
                <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto', p: 1 }}>
                  <List dense>
                    {uploadResult.errors
                      .filter((e) => !e.existing_partner)
                      .map((error, idx) => (
                        <ListItem key={idx} disablePadding>
                          <ListItemText
                            primary={`Row ${error.row}: ${error.error}`}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                  </List>
                </Paper>
              </Box>
            )}

            <Alert severity="success" sx={{ mt: 2 }}>
              Successfully uploaded {uploadResult.success} wallet(s)
            </Alert>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>
          {uploadResult ? 'Close' : 'Cancel'}
        </Button>
        {!uploadResult && (
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!canUpload}
            startIcon={<UploadIcon />}
          >
            Upload
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
