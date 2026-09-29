# CalMathX (CMX)

A step-by-step math solver for algebra and **Calculus 1, 2 and 3**. Every answer shows the full worked solution, the way you'd write it on paper.

**Stack:** MongoDB · Express · React (Vite) · Node, plus a Python/SymPy math engine.

## What it solves

| Area | Problem types |
|---|---|
| Algebra | Evaluate / simplify, solve equations (factoring, quadratic formula, rational equations) |
| Calculus 1 | Derivatives (sum/product/quotient/chain rules, log differentiation, higher order), limits (substitution, factor & cancel, dominant terms, L'Hôpital, 0·∞, 1^∞, one-sided), implicit differentiation, tangent lines, critical points & extrema |
| Calculus 2 | Integrals (u-sub, parts, partial fractions, trig identities/substitution, improper), area between curves, volumes (disk/washer/shell), arc length, Taylor/Maclaurin polynomials, series convergence (divergence, geometric, p-series, ratio, limit comparison, integral, alternating series tests) |
| Calculus 3 | Partial derivatives (incl. mixed), gradient, directional derivative, double/triple integrals (Cartesian, polar, cylindrical, spherical), tangent planes, 2-variable extrema (D-test), Lagrange multipliers, divergence, curl |

## Setup

Requirements: Node 18+, Python 3.10+, and optionally MongoDB (for saving history).

Run every command from inside the `calmathx` folder (the one containing this README):

```bash
cd C:\Users\arool\Content\calmathx
npm run dev            # API on :5000, web app on http://localhost:5173
```

First time on a new machine, before `npm run dev`:

```bash
npm run setup          # installs root, server and client packages + SymPy
copy server\.env.example server\.env
```

Production build (the Express server serves the built React app):

```bash
npm run build
npm start              # http://localhost:5000
```

## Input tips

- Powers: `x^2`, `e^(2x)`; multiplication can be implicit: `2x`, `x y`, `3sin(x)`
- Functions: `sin cos tan sec csc cot`, `arcsin arctan …`, `ln`, `log`, `sqrt`, `abs`, `|x|`
- Constants: `pi`, `e`, `inf` (∞)
- The preview under each input shows how your input was understood.

## How it works

```
React (client/)  ──/api──▶  Express (server/index.js)  ──JSON lines──▶  Python worker (server/solver/main.py)
                                 │                                          SymPy + step generators
                                 └── MongoDB (history of solved problems)
```

- `server/solverBridge.js` keeps one Python process alive (SymPy is slow to import) and restarts it if a problem runs past `SOLVE_TIMEOUT_MS`.
- The step generators live in `server/solver/`: `derivatives.py` walks the expression tree applying differentiation rules; `integrals.py` explains SymPy's integration rule tree (`manualintegrate`); `limits.py`, `series.py`, `algebra.py`, `applications.py` and `multivar.py` cover the rest.
- If MongoDB is unreachable, everything still works; only history is disabled.

## Tests

```bash
npm test               # runs one example per operation through the solver
python server/solver/smoke_test.py -v   # also prints every step
```
