export function formatKRW(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0
  }).format(value);
}

export function formatKRWInput(value: number | string) {
  const parsed = typeof value === "number" ? value : parseNumberInput(value);
  if (!parsed || Number.isNaN(parsed)) return "";
  return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 0 }).format(parsed);
}

export function parseNumberInput(value: string) {
  const text = value.trim();
  if (!text) return 0;
  const normalized = text.replace(/,/g, "");
  const decimalMatch = normalized.match(/\d+(\.\d+)?/);
  if ((normalized.includes("억") || normalized.toLowerCase().includes("eok")) && decimalMatch) {
    return Math.round(Number(decimalMatch[0]) * 100_000_000);
  }
  if ((normalized.includes("만") || normalized.toLowerCase().includes("man")) && decimalMatch) {
    return Math.round(Number(decimalMatch[0]) * 10_000);
  }
  const digits = normalized.replace(/[^\d]/g, "");
  return digits ? Number(digits) : 0;
}

export function formatPrice(value?: number | null, currency = "USD") {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  if (currency === "KRW") return formatKRW(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: value > 1000 ? 0 : 2,
    maximumFractionDigits: value > 1000 ? 0 : 2
  }).format(value);
}

export function formatNumber(value?: number | null, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: digits }).format(value);
}

export function formatPercent(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${value > 0 ? "+" : ""}${formatNumber(value, 2)}%`;
}

export function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function toneForChange(value?: number | null) {
  if (!value) return "text-subText";
  return value > 0 ? "text-up" : "text-down";
}

export function toneForRisk(score?: number | null) {
  if (score === null || score === undefined) return "text-subText";
  if (score >= 70) return "text-danger";
  if (score >= 45) return "text-warning";
  return "text-safe";
}
