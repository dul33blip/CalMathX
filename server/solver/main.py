"""CalMathX solver worker.

Reads one JSON request per line on stdin: {"id": ..., "op": "...", "params": {...}}
Writes one JSON response per line on stdout: {"id": ..., "ok": true, "data": {...}}
                                          or {"id": ..., "ok": false, "error": "..."}
"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import algebra  # noqa: E402
import applications  # noqa: E402
import derivatives  # noqa: E402
import graphs  # noqa: E402
import integrals  # noqa: E402
import limits  # noqa: E402
import multivar  # noqa: E402
import series  # noqa: E402
from common import SolverError, latex, parse, parse_equation  # noqa: E402
from plotting import attach, plot_op  # noqa: E402


def preview(p):
    text = p.get("text", "")
    if "=" in text:
        eq = parse_equation(text)
        return {"latex": f"{latex(eq.lhs)} = {latex(eq.rhs)}"}
    return {"latex": latex(parse(text))}


OPS = {
    "preview": preview,
    "plot": plot_op,
    "evaluate": algebra.evaluate,
    "solve": algebra.solve_equation,
    "derivative": derivatives.derivative,
    "implicit": derivatives.implicit,
    "limit": limits.limit_op,
    "tangent": applications.tangent,
    "extrema": applications.extrema,
    "integral": integrals.integral,
    "area": applications.area,
    "volume": applications.volume,
    "arclength": applications.arc_length,
    "taylor": series.taylor,
    "convergence": series.convergence,
    "partial": derivatives.partial,
    "gradient": multivar.gradient,
    "directional": multivar.directional,
    "multiple": multivar.multiple_integral,
    "lagrange": applications.lagrange,
    "divergence": multivar.divergence,
    "curl": multivar.curl,
}


def handle(req):
    op = req.get("op")
    if op not in OPS:
        raise SolverError(f"Unknown operation '{op}'.")
    params = req.get("params") or {}
    res = OPS[op](params)
    if op in graphs.GRAPHS:
        attach(res, lambda: graphs.GRAPHS[op](params))
    return res


def main():
    out = sys.stdout
    out.write(json.dumps({"ready": True}) + "\n")
    out.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = {}
        try:
            req = json.loads(line)
            resp = {"id": req.get("id"), "ok": True, "data": handle(req)}
        except SolverError as e:
            resp = {"id": req.get("id"), "ok": False, "error": str(e)}
        except KeyError as e:
            resp = {"id": req.get("id"), "ok": False, "error": f"Missing input: {e.args[0]}"}
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            resp = {"id": req.get("id"), "ok": False,
                    "error": f"Couldn't solve this problem ({type(e).__name__}). Check the input and try again."}
        out.write(json.dumps(resp, default=str) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
