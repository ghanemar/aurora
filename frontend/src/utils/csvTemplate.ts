/**
 * CSV Template Generator
 *
 * Generate and download CSV templates for wallet upload
 */

/**
 * Generate wallet CSV template with example rows
 */
export function generateWalletTemplate(): Blob {
  const headers = 'chain_id,wallet_address,introduced_date,notes\n';
  const example1 =
    'solana-mainnet,ExampleSolanaAddress1234567890ABC,2024-01-15,Commission wallet for Q1 campaign\n';

  const csv = headers + example1;
  return new Blob([csv], { type: 'text/csv;charset=utf-8;' });
}

/**
 * Trigger download of wallet CSV template
 */
export function downloadWalletTemplate(filename = 'wallet_template.csv'): void {
  const blob = generateWalletTemplate();
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Download wallet export CSV
 */
export function downloadWalletExport(
  blob: Blob,
  filename = 'partner_wallets_export.csv'
): void {
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
