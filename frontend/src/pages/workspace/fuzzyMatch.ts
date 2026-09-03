// Subsequence match: every character of `query` must appear in `target`, in order.
// Score rewards contiguous runs and early matches so tighter matches sort first.
export function fuzzyMatch(query: string, target: string): number | null {
  if (query === "") return 0;
  const q = query.toLowerCase();
  const t = target.toLowerCase();
  let qi = 0;
  let score = 0;
  let lastMatchIndex = -1;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) {
      score += lastMatchIndex === ti - 1 ? 3 : 1;
      if (ti === 0) score += 2;
      lastMatchIndex = ti;
      qi++;
    }
  }
  if (qi < q.length) return null;
  return score - t.length * 0.01;
}
