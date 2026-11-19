// Black-Litterman math for the BL page (mirrors bl_inputs.py). Plain functions, no dependencies.
const BL = (() => {
  const mv = (A, x) => A.map(r => r.reduce((s, a, j) => s + a * x[j], 0));
  const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
  const scale = (A, k) => A.map(r => r.map(v => v * k));
  const add = (A, B) => A.map((r, i) => r.map((v, j) => v + B[i][j]));
  function inv(M) {
    const n = M.length, A = M.map((r, i) => [...r, ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))]);
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      [A[c], A[p]] = [A[p], A[c]];
      const d = A[c][c]; for (let j = 0; j < 2 * n; j++) A[c][j] /= d;
      for (let r = 0; r < n; r++) if (r !== c) { const f = A[r][c]; for (let j = 0; j < 2 * n; j++) A[r][j] -= f * A[c][j]; }
    }
    return A.map(r => r.slice(n));
  }
  const prior = (S, w, delta) => mv(S, w).map(v => v * delta);
  // views: [{p: number[], q: number, c: confidence 0..1}]
  function posterior(Pi, S, views, tau) {
    if (!views.length) return Pi.slice();
    const tS = scale(S, tau), tSi = inv(tS);
    let A = tSi.map(r => r.slice()); const b = mv(tSi, Pi);
    for (const v of views) {
      const c = Math.min(Math.max(v.c, 0.01), 0.99);
      const om = (1 - c) / c * dot(v.p, mv(tS, v.p));
      for (let i = 0; i < Pi.length; i++) {
        b[i] += v.p[i] * v.q / om;
        for (let j = 0; j < Pi.length; j++) A[i][j] += v.p[i] * v.p[j] / om;
      }
    }
    return mv(inv(A), b);
  }
  function maxEig(S) { let x = S.map(() => 1); for (let k = 0; k < 100; k++) { const y = mv(S, x); const n = Math.hypot(...y); x = y.map(v => v / n); } return dot(x, mv(S, x)); }
  function project(w, cap) {
    w = w.map(v => Math.min(Math.max(v, 0), cap));
    for (let it = 0; it < 50 && w.reduce((a, b) => a + b, 0) > 1 + 1e-12; it++) {
      const u = [...w].sort((a, b) => b - a); let css = 0, k = 0, th = 0;
      for (let i = 0; i < u.length; i++) { css += u[i]; const t = (css - 1) / (i + 1); if (u[i] - t > 0) { k = i; th = t; } }
      w = w.map(v => Math.min(Math.max(v - th, 0), cap));
    }
    return w;
  }
  // max mu'w - delta/2 w'Sw, 0 <= w <= cap, sum w <= 1
  function solve(mu, S, delta, cap = 1, iters = 5000) {
    let w = mu.map(() => 0.5 / mu.length); const step = 1 / (delta * maxEig(S));
    for (let k = 0; k < iters; k++) { const g = mv(S, w); w = project(w.map((v, i) => v + step * (mu[i] - delta * g[i])), cap); }
    return w;
  }
  const vol = (w, S) => Math.sqrt(Math.max(dot(w, mv(S, w)), 0));
  return { prior, posterior, solve, vol, mv, dot };
})();
if (typeof module !== "undefined") module.exports = BL;
