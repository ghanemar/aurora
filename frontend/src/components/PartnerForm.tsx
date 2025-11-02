import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';
import type { Partner, PartnerCreate, PartnerUpdate } from '../types';

/**
 * Partner Form Component
 *
 * Features:
 * - Add/Edit partner
 * - Form validation (required fields, email format)
 * - Error handling
 * - Loading state
 */

interface PartnerFormProps {
  open: boolean;
  mode: 'create' | 'edit';
  partner?: Partner;
  onClose: () => void;
  onSubmit: (data: PartnerCreate | PartnerUpdate) => void;
  isSubmitting?: boolean;
}

export const PartnerForm: React.FC<PartnerFormProps> = ({
  open,
  mode,
  partner,
  onClose,
  onSubmit,
  isSubmitting = false,
}) => {
  const [partnerName, setPartnerName] = useState('');
  const [legalEntityName, setLegalEntityName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactName, setContactName] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{
    partnerName?: string;
    contactEmail?: string;
  }>({});

  // Initialize form with partner data in edit mode
  useEffect(() => {
    if (mode === 'edit' && partner) {
      setPartnerName(partner.partner_name);
      setLegalEntityName(partner.legal_entity_name || '');
      setContactEmail(partner.contact_email);
      setContactName(partner.contact_name || '');
    } else {
      // Reset form in create mode
      setPartnerName('');
      setLegalEntityName('');
      setContactEmail('');
      setContactName('');
    }
    setFieldErrors({});
  }, [mode, partner, open]);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    const errors: { partnerName?: string; contactEmail?: string } = {};

    if (!partnerName.trim()) {
      errors.partnerName = 'Partner name is required';
    }

    if (!contactEmail.trim()) {
      errors.contactEmail = 'Email is required';
    } else if (!validateEmail(contactEmail.trim())) {
      errors.contactEmail = 'Invalid email format';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) {
      return;
    }

    if (mode === 'create') {
      const data: PartnerCreate = {
        partner_name: partnerName.trim(),
        legal_entity_name: legalEntityName.trim() || undefined,
        contact_email: contactEmail.trim(),
        contact_name: contactName.trim() || undefined,
      };
      onSubmit(data);
    } else {
      const data: PartnerUpdate = {
        partner_name: partnerName.trim(),
        legal_entity_name: legalEntityName.trim() || undefined,
        contact_email: contactEmail.trim(),
        contact_name: contactName.trim() || undefined,
      };
      onSubmit(data);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFieldErrors({});
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Add New Partner' : 'Edit Partner'}
      </DialogTitle>

      <DialogContent>
        {/* Partner Name */}
        <TextField
          label="Partner Name"
          fullWidth
          margin="normal"
          value={partnerName}
          onChange={(e) => {
            setPartnerName(e.target.value);
            setFieldErrors((prev) => ({ ...prev, partnerName: undefined }));
          }}
          disabled={isSubmitting}
          required
          error={!!fieldErrors.partnerName}
          helperText={fieldErrors.partnerName || 'Display name for the partner'}
          autoFocus
        />

        {/* Legal Entity Name */}
        <TextField
          label="Legal Entity Name"
          fullWidth
          margin="normal"
          value={legalEntityName}
          onChange={(e) => setLegalEntityName(e.target.value)}
          disabled={isSubmitting}
          helperText="Legal business name (optional)"
        />

        {/* Contact Email */}
        <TextField
          label="Contact Email"
          fullWidth
          margin="normal"
          value={contactEmail}
          onChange={(e) => {
            setContactEmail(e.target.value);
            setFieldErrors((prev) => ({ ...prev, contactEmail: undefined }));
          }}
          disabled={isSubmitting}
          required
          error={!!fieldErrors.contactEmail}
          helperText={fieldErrors.contactEmail || 'Primary contact email'}
          type="email"
        />

        {/* Contact Name */}
        <TextField
          label="Contact Person"
          fullWidth
          margin="normal"
          value={contactName}
          onChange={(e) => setContactName(e.target.value)}
          disabled={isSubmitting}
          helperText="Contact person name (optional)"
        />
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isSubmitting}
        >
          {mode === 'create' ? 'Add Partner' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
