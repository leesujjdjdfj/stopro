export function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function rewardRiskLabel(ratio?: number | null) {
  if (ratio === null || ratio === undefined) return "계산 불가";
  if (ratio >= 2) return "양호";
  if (ratio >= 1.5) return "보통 이상";
  if (ratio >= 1) return "애매함";
  return "불리함";
}
