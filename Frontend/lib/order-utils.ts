const orderPattern = /^VN-\d{5}$/;

export function formatOrderNumber(orderId: number | string, trackingId?: string | null) {
  if (trackingId && orderPattern.test(trackingId)) {
    return trackingId;
  }

  const normalizedOrderId = String(orderId);
  if (/^\d+$/.test(normalizedOrderId)) {
    return `VN-${normalizedOrderId.padStart(5, "0")}`;
  }

  return "VN-00000";
}
