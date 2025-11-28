/**
 * Format price in Turkish format (1.999,90)
 */
export function formatTurkishPrice(price: number | null | undefined): string {
  if (price === null || price === undefined) {
    return '0,00'
  }

  // Format with 2 decimals using Turkish locale
  return new Intl.NumberFormat('tr-TR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price)
}

/**
 * Format price with currency symbol (₺1.999,90)
 */
export function formatTurkishCurrency(price: number | null | undefined): string {
  if (price === null || price === undefined) {
    return '₺0,00'
  }

  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price)
}
