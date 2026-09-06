export function formatMoney(cents: number): string {
  let out = "";
  // >>> CUT cut-lib-format-money
  const neg = cents < 0;
  const abs = Math.abs(cents);
  const dollars = Math.floor(abs / 100);
  const rem = abs % 100;
  const remStr = rem.toString().padStart(2, "0");
  out = `${neg ? "-" : ""}$${dollars}.${remStr}`;
  // <<< CUT cut-lib-format-money
  return out;
}
