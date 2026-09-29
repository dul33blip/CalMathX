"""Calculus 3: gradient, directional derivative, multiple integrals, divergence, curl."""
from sympy import (
    Symbol, sin, cos, sqrt, Matrix, diff, S, simplify, oo,
)

from common import Steps, SolverError, latex, parse, parse_symbol, tidy, result, approx
from derivatives import diff_steps, parse_point
from integrals import antiderivative_steps, definite_steps

X, Y, Z = Symbol("x"), Symbol("y"), Symbol("z")
r, theta, rho, phi = Symbol("r"), Symbol("theta"), Symbol("rho"), Symbol("phi")


def _vars(expr, requested=None):
    if requested:
        return [parse_symbol(v) for v in str(requested).replace(",", " ").split()]
    syms = sorted(expr.free_symbols, key=lambda s: s.name)
    order = {"x": 0, "y": 1, "z": 2}
    return sorted(syms, key=lambda s: (order.get(s.name, 3), s.name))


def _vec(parts):
    return r"\left\langle " + ", ".join(latex(p) for p in parts) + r" \right\rangle"


def gradient_steps(expr, vs, steps, detailed=True):
    grads = []
    for v in vs:
        steps.add(f"### Partial derivative with respect to ${latex(v)}$ (others held constant)")
        if detailed:
            raw = diff_steps(expr, v, steps, 1, partial=True)
        else:
            raw = diff(expr, v)
        g = tidy(raw)
        steps.add(f"$f_{{{latex(v)}}} = {latex(g)}$")
        grads.append(g)
    return grads


def gradient(p):
    expr = parse(p["expr"])
    vs = _vars(expr, p.get("vars"))
    steps = Steps()
    steps.add("The gradient is the vector of partial derivatives:",
              r"\nabla f = " + _vec([Symbol(f"f_{v.name}") for v in vs]))
    grads = gradient_steps(expr, vs, steps)
    steps.add("Assemble the gradient.", r"\nabla f = " + _vec(grads))
    if p.get("point"):
        pt = parse_point(p["point"], expr)
        vals = [tidy(g.subs(pt)) for g in grads]
        steps.add("Evaluate at the point.", r"\nabla f = " + _vec(vals))
        return result(_vec(vals), steps, None, {"expression": _vec(grads)})
    return result(r"\nabla f = " + _vec(grads), steps)


def directional(p):
    expr = parse(p["expr"])
    vs = _vars(expr, p.get("vars"))
    pt = parse_point(p["point"], expr)
    u = [parse(s) for s in str(p["direction"]).strip("()<>⟨⟩ ").split(",")]
    if len(u) != len(vs):
        raise SolverError(f"Direction needs {len(vs)} components.")
    steps = Steps()
    steps.add(r"The directional derivative in the direction of a unit vector $\mathbf{u}$ is",
              r"D_{\mathbf{u}} f = \nabla f \cdot \mathbf{u}")
    grads = gradient_steps(expr, vs, steps, detailed=False)
    vals = [tidy(g.subs(pt)) for g in grads]
    steps.add("Gradient at the point:", r"\nabla f = " + _vec(vals))
    mag = sqrt(sum(c ** 2 for c in u))
    unit = [tidy(c / mag) for c in u]
    if simplify(mag - 1) != 0:
        steps.add("Normalize the direction vector (divide by its length).",
                  rf"\|\mathbf{{v}}\| = {latex(mag)}, \qquad \mathbf{{u}} = {_vec(unit)}")
    val = tidy(sum(a * b for a, b in zip(vals, unit)))
    steps.add("Take the dot product.",
              r"D_{\mathbf{u}} f = " + " + ".join(rf"\left({latex(a)}\right)\left({latex(b)}\right)"
                                                  for a, b in zip(vals, unit)) + f" = {latex(val)}")
    return result(latex(val), steps, approx(val))


COORDS = {
    "polar": ({X: r * cos(theta), Y: r * sin(theta)}, r, r"x = r\cos\theta,\ y = r\sin\theta", r"dA = r\,dr\,d\theta"),
    "cylindrical": ({X: r * cos(theta), Y: r * sin(theta)}, r,
                    r"x = r\cos\theta,\ y = r\sin\theta,\ z = z", r"dV = r\,dz\,dr\,d\theta"),
    "spherical": ({X: rho * sin(phi) * cos(theta), Y: rho * sin(phi) * sin(theta), Z: rho * cos(phi)},
                  rho ** 2 * sin(phi), r"x = \rho\sin\phi\cos\theta,\ y = \rho\sin\phi\sin\theta,\ z = \rho\cos\phi",
                  r"dV = \rho^2\sin\phi\,d\rho\,d\phi\,d\theta"),
}


def multiple_integral(p):
    """bounds: list of {var, lower, upper}, innermost first."""
    expr = parse(p["expr"])
    bounds = [b for b in p.get("bounds", []) if str(b.get("var", "")).strip()]
    if not 2 <= len(bounds) <= 3:
        raise SolverError("Enter bounds for 2 or 3 variables (innermost integral first).")
    coords = p.get("coords") or "cartesian"
    steps = Steps()
    f = expr
    if coords in COORDS:
        sub, jac, eqs, dA = COORDS[coords]
        steps.add(f"### Convert to {coords} coordinates", f"{eqs}, \\qquad {dA}")
        if f.free_symbols & set(sub):
            f = tidy(f.subs(sub))
            steps.add("Substitute into the integrand and simplify.", f"f = {latex(f)}")
        before = f
        f = tidy(f * jac)
        steps.add(f"Multiply by the Jacobian ${latex(jac)}$ (the extra factor in {dA.split('=')[0].strip()}).",
                  rf"\left({latex(before)}\right) \cdot {latex(jac)} = {latex(f)}")

    parsed = [(parse_symbol(b["var"]), parse(b["lower"]), parse(b["upper"])) for b in bounds]
    integral_tex = "".join(rf"\int_{{{latex(a)}}}^{{{latex(b)}}}" for _, a, b in reversed(parsed))
    diffs = "".join(rf"\,d{latex(v)}" for v, _, _ in parsed)
    steps.add("Set up the iterated integral (work from the inside out):", f"{integral_tex} {latex(f)}{diffs}")

    current = f
    for i, (v, a, b) in enumerate(parsed, 1):
        steps.add(f"### Integral {i}: integrate with respect to ${latex(v)}$ "
                  f"from ${latex(a)}$ to ${latex(b)}$")
        F = antiderivative_steps(current, v, steps, 1, check=False)
        upper, lower = tidy(F.subs(v, b)), tidy(F.subs(v, a))
        current = tidy(upper - lower)
        steps.add("Evaluate at the bounds.",
                  rf"\Big[{latex(F)}\Big]_{{{latex(a)}}}^{{{latex(b)}}} = \left({latex(upper)}\right) - "
                  rf"\left({latex(lower)}\right) = {latex(current)}")
    steps.add("**Result:**", f"{integral_tex} {latex(f)}{diffs} = {latex(current)}")
    return result(latex(current), steps, approx(current))


def _field(p):
    comps = [parse(c) for c in str(p["field"]).strip("()<>⟨⟩ ").split(",")]
    if len(comps) not in (2, 3):
        raise SolverError("Enter the vector field as P, Q  or  P, Q, R (comma-separated).")
    return comps


def divergence(p):
    F = _field(p)
    vs = [X, Y, Z][:len(F)]
    steps = Steps()
    names = "PQR"
    steps.add("The divergence is the sum of each component's partial derivative in its own direction:",
              r"\nabla \cdot \mathbf{F} = " + " + ".join(
                  rf"\frac{{\partial {names[i]}}}{{\partial {latex(v)}}}" for i, v in enumerate(vs)))
    parts = []
    for i, (c, v) in enumerate(zip(F, vs)):
        d = tidy(diff(c, v))
        parts.append(d)
        steps.add(f"${names[i]} = {latex(c)}$:", rf"\frac{{\partial {names[i]}}}{{\partial {latex(v)}}} = {latex(d)}", 1)
    total = tidy(sum(parts))
    steps.add("Add them.", rf"\nabla \cdot \mathbf{{F}} = {latex(total)}")
    if p.get("point"):
        pt = _pt(p["point"], vs)
        val = tidy(total.subs(pt))
        steps.add("Evaluate at the point.", rf"\nabla \cdot \mathbf{{F}} = {latex(val)}")
        return result(latex(val), steps, approx(val), {"expression": latex(total)})
    return result(rf"\nabla \cdot \mathbf{{F}} = {latex(total)}", steps)


def curl(p):
    F = _field(p)
    if len(F) == 2:
        F = F + [S(0)]
    P, Q, R = F
    steps = Steps()
    steps.add("The curl is the determinant-style cross product $\\nabla \\times \\mathbf{F}$:",
              r"\nabla \times \mathbf{F} = \left\langle R_y - Q_z,\; P_z - R_x,\; Q_x - P_y \right\rangle")
    pairs = [("R_y", R, Y), ("Q_z", Q, Z), ("P_z", P, Z), ("R_x", R, X), ("Q_x", Q, X), ("P_y", P, Y)]
    vals = {}
    for name, c, v in pairs:
        vals[name] = tidy(diff(c, v))
        steps.add(f"${name}$:", rf"\frac{{\partial}}{{\partial {latex(v)}}}\left[{latex(c)}\right] = {latex(vals[name])}", 1)
    comps = [tidy(vals["R_y"] - vals["Q_z"]), tidy(vals["P_z"] - vals["R_x"]), tidy(vals["Q_x"] - vals["P_y"])]
    steps.add("Assemble the components.", r"\nabla \times \mathbf{F} = " + _vec(comps))
    if all(c == 0 for c in comps):
        steps.add("The curl is zero, so the field is **irrotational** (conservative on simply-connected domains).")
    if p.get("point"):
        pt = _pt(p["point"], [X, Y, Z])
        v = [tidy(c.subs(pt)) for c in comps]
        steps.add("Evaluate at the point.", r"\nabla \times \mathbf{F} = " + _vec(v))
        return result(_vec(v), steps, None, {"expression": _vec(comps)})
    return result(r"\nabla \times \mathbf{F} = " + _vec(comps), steps)


def _pt(text, vs):
    parts = [s.strip() for s in str(text).strip("() ").split(",") if s.strip()]
    if all("=" in s for s in parts):
        return {parse_symbol(s.split("=")[0]): parse(s.split("=")[1]) for s in parts}
    return dict(zip(vs, [parse(s) for s in parts]))
