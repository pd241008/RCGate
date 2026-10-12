/** Mirrors RC-Gate logit fusion when fusion_input is "logit". */

export function sigmoid(logit: number): number {
  return 1 / (1 + Math.exp(-logit));
}

export function expertLogit(weights: number[], bias: number, values: number[]): number {
  return weights.reduce((sum, weight, index) => sum + weight * values[index], bias);
}

export function fusedLogit(
  fusionWeights: number[],
  fusionBias: number,
  wCross: number,
  zCross: number,
  wEvid: number,
  zEvid: number,
): number {
  return fusionWeights[0] * (wCross * zCross) + fusionWeights[1] * (wEvid * zEvid) + fusionBias;
}

export function formatPercent(prob: number): string {
  return `${(prob * 100).toFixed(2)}%`;
}

export function formatSigned(value: number, digits = 4): string {
  const text = value.toFixed(digits);
  return value > 0 ? `+${text}` : text;
}
