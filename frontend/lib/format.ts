export function formatPrice(value: number): string {
  return `${new Intl.NumberFormat("vi-VN").format(value)} ₫`;
}
