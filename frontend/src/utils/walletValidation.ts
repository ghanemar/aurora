/**
 * Wallet Validation Utilities
 *
 * Chain-specific wallet address validation and CSV parsing
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Validate Solana wallet address
 * - Base58 encoding
 * - 32-44 characters typical length
 */
export function validateSolanaAddress(address: string): ValidationResult {
  // Base58 character set
  const base58Regex = /^[1-9A-HJ-NP-Za-km-z]+$/;

  if (!address || address.length === 0) {
    return { isValid: false, error: 'Address cannot be empty' };
  }

  if (address.length < 32 || address.length > 44) {
    return {
      isValid: false,
      error: 'Solana address must be 32-44 characters long',
    };
  }

  if (!base58Regex.test(address)) {
    return {
      isValid: false,
      error: 'Solana address must contain only Base58 characters',
    };
  }

  return { isValid: true };
}

/**
 * Validate Ethereum wallet address
 * - Starts with 0x
 * - Followed by 40 hexadecimal characters
 */
export function validateEthereumAddress(address: string): ValidationResult {
  if (!address || address.length === 0) {
    return { isValid: false, error: 'Address cannot be empty' };
  }

  if (!address.startsWith('0x')) {
    return {
      isValid: false,
      error: 'Ethereum address must start with 0x',
    };
  }

  if (address.length !== 42) {
    return {
      isValid: false,
      error: 'Ethereum address must be 42 characters long (0x + 40 hex chars)',
    };
  }

  const hexRegex = /^0x[0-9A-Fa-f]{40}$/;
  if (!hexRegex.test(address)) {
    return {
      isValid: false,
      error: 'Ethereum address must contain only hexadecimal characters after 0x',
    };
  }

  return { isValid: true };
}

/**
 * Validate wallet address based on chain
 */
export function validateWalletAddress(
  address: string,
  chainId: string
): ValidationResult {
  const normalizedChain = chainId.toLowerCase();

  switch (normalizedChain) {
    case 'solana':
      return validateSolanaAddress(address);
    case 'ethereum':
    case 'eth':
      return validateEthereumAddress(address);
    default:
      // For unknown chains, just check non-empty
      if (!address || address.trim().length === 0) {
        return { isValid: false, error: 'Address cannot be empty' };
      }
      return { isValid: true };
  }
}

/**
 * Parse and validate CSV data for wallet upload
 */
export interface WalletCSVRow {
  row: number;
  chain_id: string;
  wallet_address: string;
  introduced_date: string;
  notes?: string;
}

export interface CSVParseResult {
  rows: WalletCSVRow[];
  errors: Array<{ row: number; error: string }>;
}

export async function parseWalletCSV(file: File): Promise<CSVParseResult> {
  const text = await file.text();
  const lines = text.split('\n').filter((line) => line.trim().length > 0);

  if (lines.length === 0) {
    return {
      rows: [],
      errors: [{ row: 0, error: 'CSV file is empty' }],
    };
  }

  // Parse header
  const header = lines[0].split(',').map((h) => h.trim().toLowerCase());
  const requiredHeaders = ['chain_id', 'wallet_address', 'introduced_date'];
  const missingHeaders = requiredHeaders.filter(
    (h) => !header.includes(h)
  );

  if (missingHeaders.length > 0) {
    return {
      rows: [],
      errors: [
        {
          row: 0,
          error: `Missing required columns: ${missingHeaders.join(', ')}`,
        },
      ],
    };
  }

  // Get column indices
  const chainIdx = header.indexOf('chain_id');
  const addressIdx = header.indexOf('wallet_address');
  const dateIdx = header.indexOf('introduced_date');
  const notesIdx = header.indexOf('notes');

  const rows: WalletCSVRow[] = [];
  const errors: Array<{ row: number; error: string }> = [];

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const columns = line.split(',').map((c) => c.trim());

    // Check required fields
    const chainId = columns[chainIdx];
    const address = columns[addressIdx];
    const date = columns[dateIdx];
    const notes = notesIdx >= 0 ? columns[notesIdx] : undefined;

    if (!chainId || !address || !date) {
      errors.push({
        row: i + 1,
        error: 'Missing required field(s): chain_id, wallet_address, or introduced_date',
      });
      continue;
    }

    // Validate wallet address format
    const validation = validateWalletAddress(address, chainId);
    if (!validation.isValid) {
      errors.push({
        row: i + 1,
        error: `Invalid wallet address: ${validation.error}`,
      });
      continue;
    }

    // Validate date format (YYYY-MM-DD)
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(date)) {
      errors.push({
        row: i + 1,
        error: 'Invalid date format. Expected YYYY-MM-DD',
      });
      continue;
    }

    // Check if date is in the future
    const parsedDate = new Date(date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (parsedDate > today) {
      errors.push({
        row: i + 1,
        error: 'Introduced date cannot be in the future',
      });
      continue;
    }

    rows.push({
      row: i + 1,
      chain_id: chainId,
      wallet_address: address,
      introduced_date: date,
      notes: notes && notes.length > 0 ? notes : undefined,
    });
  }

  return { rows, errors };
}

/**
 * Validate introduced date
 */
export function validateIntroducedDate(dateString: string): ValidationResult {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

  if (!dateRegex.test(dateString)) {
    return {
      isValid: false,
      error: 'Date must be in YYYY-MM-DD format',
    };
  }

  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    return {
      isValid: false,
      error: 'Invalid date',
    };
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (date > today) {
    return {
      isValid: false,
      error: 'Date cannot be in the future',
    };
  }

  return { isValid: true };
}
