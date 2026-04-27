export const DISCLAIMER = "본 분석은 개인 참고용이며, 투자 판단과 책임은 니네한테 있다.";

export const QUICK_CAPITALS = [
  { label: "1,000만", value: 10_000_000 },
  { label: "500만", value: 5_000_000 },
  { label: "300만", value: 3_000_000 },
  { label: "100만", value: 1_000_000 },
  { label: "50만", value: 500_000 },
  { label: "10만", value: 100_000 }
];

export const RISK_PROFILES = [
  { label: "소극적", value: "conservative", description: "1%" },
  { label: "균형적", value: "balanced", description: "1.5%" },
  { label: "공격적", value: "aggressive", description: "2%" }
] as const;

export const EXAMPLE_TICKERS = ["NVDA", "TSLA", "HIMS"];
