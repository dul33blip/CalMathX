"""Runs one example per operation. Usage: python smoke_test.py [-v]"""
import sys
import time

from main import handle

CASES = [
    ("evaluate", {"expr": "2^10 + sqrt(50)"}),
    ("evaluate", {"expr": "(x^2-1)/(x-1)"}),
    ("solve", {"equation": "x^2 - 5x + 6 = 0"}),
    ("solve", {"equation": "x^2 + 2x - 5 = 0"}),
    ("solve", {"equation": "x^3 - x = 0"}),
    ("solve", {"equation": "2^x = 8"}),
    ("derivative", {"expr": "x^3 ln(x)", "order": 2}),
    ("derivative", {"expr": "tan(x^2)", "point": "0"}),
    ("implicit", {"equation": "x^3 + y^3 = 6xy"}),
    ("limit", {"expr": "sin(x)/x", "point": "0"}),
    ("limit", {"expr": "(x^2-4)/(x-2)", "point": "2"}),
    ("limit", {"expr": "(3x^2+1)/(5x^2-x)", "point": "inf"}),
    ("limit", {"expr": "(1+1/x)^x", "point": "inf"}),
    ("limit", {"expr": "1/x", "point": "0"}),
    ("limit", {"expr": "x ln(x)", "point": "0", "dir": "+"}),
    ("limit", {"expr": "(1 - cos(x))/x^2", "point": ""}),  # empty point defaults to 0
    ("tangent", {"expr": "x^2 + 1", "point": "2"}),
    ("tangent", {"expr": "x^2 + y^2", "point": "1, 2"}),
    ("extrema", {"expr": "x^3 - 3x"}),
    ("extrema", {"expr": "x^3 - 3x", "lower": "0", "upper": "3"}),
    ("extrema", {"expr": "x^2 + y^2 - 2x + 4y"}),
    ("integral", {"expr": "sin(x)^2"}),
    ("integral", {"expr": "e^x cos(x)"}),
    ("integral", {"expr": "1/sqrt(4 - x^2)"}),
    ("integral", {"expr": "x^2 sqrt(1 - x^2)"}),
    ("integral", {"expr": "(3x+5)/(x^2+x-2)"}),
    ("integral", {"expr": "1/x^2", "lower": "1", "upper": "inf"}),
    ("integral", {"expr": "e^(-x^2)", "lower": "0", "upper": "1"}),
    ("area", {"expr": "x", "expr2": "x^2"}),
    ("volume", {"expr": "sqrt(x)", "lower": "0", "upper": "4", "method": "disk", "axis": "x"}),
    ("volume", {"expr": "x^2", "lower": "0", "upper": "2", "method": "shell", "axis": "y"}),
    ("arclength", {"expr": "x^(3/2)", "lower": "0", "upper": "4"}),
    ("taylor", {"expr": "e^x", "order": 4}),
    ("taylor", {"expr": "ln(x)", "center": "1", "order": 3}),
    ("convergence", {"term": "1/n^2"}),
    ("convergence", {"term": "(1/2)^n", "start": "0"}),
    ("convergence", {"term": "(-1)^n / n"}),
    ("convergence", {"term": "n!/10^n"}),
    ("convergence", {"term": "n/(n^3+1)"}),
    ("convergence", {"term": "1/(n ln(n))", "start": "2"}),
    ("convergence", {"term": "n/(n+1)"}),
    ("partial", {"expr": "x^2 y^3 + sin(xy)", "vars": "x"}),
    ("gradient", {"expr": "x^2 y + y z^2", "point": "1, 2, 3"}),
    ("directional", {"expr": "x^2 + y^2", "point": "1, 1", "direction": "3, 4"}),
    ("multiple", {"expr": "x y", "bounds": [{"var": "y", "lower": "0", "upper": "x"},
                                            {"var": "x", "lower": "0", "upper": "1"}]}),
    ("multiple", {"expr": "x^2 + y^2", "coords": "polar",
                  "bounds": [{"var": "r", "lower": "0", "upper": "2"}, {"var": "theta", "lower": "0", "upper": "2pi"}]}),
    ("multiple", {"expr": "1", "coords": "spherical",
                  "bounds": [{"var": "rho", "lower": "0", "upper": "1"}, {"var": "phi", "lower": "0", "upper": "pi"},
                             {"var": "theta", "lower": "0", "upper": "2pi"}]}),
    ("lagrange", {"expr": "x y", "constraint": "x + y = 10"}),
    ("divergence", {"field": "x^2, x y, z"}),
    ("curl", {"field": "y, -x, 0"}),
]

verbose = "-v" in sys.argv
failed = 0
for op, params in CASES:
    t = time.time()
    try:
        out = handle({"op": op, "params": params})
        dt = time.time() - t
        print(f"OK   {dt:5.2f}s {op:12} {list(params.values())[0]!s:28} -> {out['answer']}"
              + (f"  (~{out['approx']})" if out.get("approx") else ""))
        if verbose:
            for s in out["steps"]:
                print("        " + "  " * s["depth"] + s["text"], "|", s["math"] or "")
    except Exception as e:
        failed += 1
        print(f"FAIL        {op:12} {params} -> {type(e).__name__}: {e}")
print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
sys.exit(1 if failed else 0)
