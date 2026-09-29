// Every calculator mode: its inputs, and example problems users can click to try.
// Field types: expr (math, with live preview) | text | number | select | bounds (multiple integral)

export const GROUPS = [
  { id: 'general', label: 'Algebra', ops: ['evaluate', 'solve'] },
  { id: 'calc1', label: 'Calculus 1', ops: ['derivative', 'limit', 'implicit', 'tangent', 'extrema'] },
  { id: 'calc2', label: 'Calculus 2', ops: ['integral', 'area', 'volume', 'arclength', 'taylor', 'convergence'] },
  { id: 'calc3', label: 'Calculus 3', ops: ['partial', 'gradient', 'directional', 'multiple', 'lagrange', 'divergence', 'curl'] },
];

const point = (label = 'Evaluate at (optional)', placeholder = 'e.g. 2') => ({
  name: 'point', label, type: 'text', placeholder, optional: true,
});

export const OPS = {
  evaluate: {
    title: 'Evaluate / Simplify',
    blurb: 'Arithmetic, exact values, and simplifying/factoring algebraic expressions.',
    fields: [{ name: 'expr', label: 'Expression', type: 'expr', placeholder: 'e.g. (x^2 - 1)/(x - 1)' }],
    examples: [{ expr: '2^10 + sqrt(50)' }, { expr: '(x^2-1)/(x-1)' }, { expr: 'sin(pi/6) + cos(pi/3)' }, { expr: '(x+2)^3' }],
  },
  solve: {
    title: 'Solve Equation',
    blurb: 'Linear, quadratic (factoring or quadratic formula), polynomial, rational and more.',
    fields: [
      { name: 'equation', label: 'Equation', type: 'expr', placeholder: 'e.g. x^2 - 5x + 6 = 0' },
      { name: 'var', label: 'Solve for', type: 'text', placeholder: 'x', optional: true, small: true },
    ],
    examples: [{ equation: 'x^2 - 5x + 6 = 0' }, { equation: '2x^2 + 3x = 7' }, { equation: 'x^3 = 4x' }, { equation: '1/x + 1/(x+1) = 1' }, { equation: 'e^(2x) = 5' }],
  },
  derivative: {
    title: 'Derivative',
    blurb: 'Power, product, quotient and chain rules shown step by step. Higher-order too.',
    fields: [
      { name: 'expr', label: 'f(x) =', type: 'expr', placeholder: 'e.g. x^2 sin(3x)' },
      { name: 'var', label: 'With respect to', type: 'text', placeholder: 'x', optional: true, small: true },
      { name: 'order', label: 'Order', type: 'number', placeholder: '1', optional: true, small: true, min: 1, max: 10 },
      point(),
    ],
    examples: [{ expr: 'x^2 sin(3x)' }, { expr: '(x^2+1)/(x-3)' }, { expr: 'e^(x^2) ln(x)' }, { expr: 'sqrt(1 + cos(x)^2)' }, { expr: 'x^x' }, { expr: 'x^4 - 3x^2', order: 2 }],
  },
  limit: {
    title: 'Limit',
    blurb: "Direct substitution, factor & cancel, dominant terms, L'Hôpital's rule, one-sided limits.",
    fields: [
      { name: 'expr', label: 'f(x) =', type: 'expr', placeholder: 'e.g. sin(x)/x' },
      { name: 'point', label: 'x approaches', type: 'text', placeholder: '0  (use inf for ∞)', optional: true, small: true },
      { name: 'dir', label: 'Side', type: 'select', options: [['both', 'Both sides'], ['+', 'From the right (+)'], ['-', 'From the left (−)']], small: true },
      { name: 'var', label: 'Variable', type: 'text', placeholder: 'x', optional: true, small: true },
    ],
    examples: [{ expr: 'sin(x)/x', point: '0' }, { expr: '(x^2-4)/(x-2)', point: '2' }, { expr: '(3x^2+1)/(5x^2-x)', point: 'inf' }, { expr: '(1+1/x)^x', point: 'inf' }, { expr: 'x ln(x)', point: '0', dir: '+' }, { expr: '(e^x - 1 - x)/x^2', point: '0' }],
  },
  implicit: {
    title: 'Implicit Differentiation',
    blurb: 'Find dy/dx for an equation relating x and y.',
    fields: [
      { name: 'equation', label: 'Equation', type: 'expr', placeholder: 'e.g. x^2 + y^2 = 25' },
      point('At point (optional)', 'e.g. 3, 4'),
    ],
    examples: [{ equation: 'x^2 + y^2 = 25', point: '3, 4' }, { equation: 'x^3 + y^3 = 6xy' }, { equation: 'sin(xy) = x' }],
  },
  tangent: {
    title: 'Tangent Line / Plane',
    blurb: 'Tangent line to y = f(x), or tangent plane to z = f(x, y).',
    fields: [
      { name: 'expr', label: 'f =', type: 'expr', placeholder: 'e.g. x^2 + 1   or   x^2 + y^2' },
      point('At x = a  (or point a, b)', 'e.g. 2   or   1, 2'),
    ].map((f) => (f.name === 'point' ? { ...f, optional: false } : f)),
    examples: [{ expr: 'x^2 + 1', point: '2' }, { expr: 'sin(x)', point: 'pi/4' }, { expr: 'x^2 + y^2', point: '1, 2' }],
  },
  extrema: {
    title: 'Critical Points & Extrema',
    blurb: 'Local max/min with the second derivative test; absolute extrema on [a, b]; 2-variable D-test.',
    fields: [
      { name: 'expr', label: 'f =', type: 'expr', placeholder: 'e.g. x^3 - 3x   or   x^2 + y^2 - 2x' },
      { name: 'lower', label: 'Interval start (optional)', type: 'text', placeholder: 'a', optional: true, small: true },
      { name: 'upper', label: 'Interval end (optional)', type: 'text', placeholder: 'b', optional: true, small: true },
    ],
    examples: [{ expr: 'x^3 - 3x' }, { expr: 'x^3 - 3x', lower: '0', upper: '3' }, { expr: 'x^4 - 4x^3' }, { expr: 'x^3 + y^3 - 3xy' }],
  },
  integral: {
    title: 'Integral',
    blurb: 'u-substitution, integration by parts, partial fractions, trig substitution, improper integrals.',
    fields: [
      { name: 'expr', label: '∫', type: 'expr', placeholder: 'e.g. x e^x' },
      { name: 'var', label: 'd', type: 'text', placeholder: 'x', optional: true, small: true },
      { name: 'lower', label: 'Lower bound (optional)', type: 'text', placeholder: 'a', optional: true, small: true },
      { name: 'upper', label: 'Upper bound (optional)', type: 'text', placeholder: 'b  (inf for ∞)', optional: true, small: true },
    ],
    examples: [{ expr: 'x e^x' }, { expr: '2x cos(x^2)' }, { expr: '(3x+5)/(x^2+x-2)' }, { expr: 'sin(x)^2' }, { expr: 'x^2 sqrt(1 - x^2)' }, { expr: 'x^2', lower: '0', upper: '3' }, { expr: '1/x^2', lower: '1', upper: 'inf' }],
  },
  area: {
    title: 'Area Between Curves',
    blurb: 'Finds intersection points, decides which curve is on top, and integrates.',
    fields: [
      { name: 'expr', label: 'f(x) =', type: 'expr', placeholder: 'e.g. x' },
      { name: 'expr2', label: 'g(x) =', type: 'expr', placeholder: 'e.g. x^2  (blank = x-axis)', optional: true },
      { name: 'lower', label: 'From (optional)', type: 'text', placeholder: 'auto', optional: true, small: true },
      { name: 'upper', label: 'To (optional)', type: 'text', placeholder: 'auto', optional: true, small: true },
    ],
    examples: [{ expr: 'x', expr2: 'x^2' }, { expr: '4 - x^2', expr2: '0' }, { expr: 'sin(x)', expr2: '0', lower: '0', upper: 'pi' }],
  },
  volume: {
    title: 'Volume of Revolution',
    blurb: 'Disk/washer method about the x-axis, or shell method about the y-axis.',
    fields: [
      { name: 'expr', label: 'Outer f(x) =', type: 'expr', placeholder: 'e.g. sqrt(x)' },
      { name: 'expr2', label: 'Inner g(x) = (optional)', type: 'expr', placeholder: 'blank = 0', optional: true },
      { name: 'lower', label: 'From x =', type: 'text', placeholder: 'a', small: true },
      { name: 'upper', label: 'To x =', type: 'text', placeholder: 'b', small: true },
      { name: 'method', label: 'Method', type: 'select', options: [['disk', 'Disk / washer (about x-axis)'], ['shell', 'Shell (about y-axis)']] },
    ],
    examples: [{ expr: 'sqrt(x)', lower: '0', upper: '4', method: 'disk' }, { expr: 'x', expr2: 'x^2', lower: '0', upper: '1', method: 'disk' }, { expr: 'x^2', lower: '0', upper: '2', method: 'shell' }],
  },
  arclength: {
    title: 'Arc Length',
    blurb: 'L = ∫ √(1 + (f′)²) dx.',
    fields: [
      { name: 'expr', label: 'f(x) =', type: 'expr', placeholder: 'e.g. x^(3/2)' },
      { name: 'lower', label: 'From x =', type: 'text', placeholder: 'a', small: true },
      { name: 'upper', label: 'To x =', type: 'text', placeholder: 'b', small: true },
    ],
    examples: [{ expr: 'x^(3/2)', lower: '0', upper: '4' }, { expr: 'ln(cos(x))', lower: '0', upper: 'pi/4' }],
  },
  taylor: {
    title: 'Taylor / Maclaurin Polynomial',
    blurb: 'Builds the polynomial term by term from derivatives at the center.',
    fields: [
      { name: 'expr', label: 'f(x) =', type: 'expr', placeholder: 'e.g. e^x' },
      { name: 'center', label: 'Center a', type: 'text', placeholder: '0', optional: true, small: true },
      { name: 'order', label: 'Degree n', type: 'number', placeholder: '5', optional: true, small: true, min: 0, max: 15 },
    ],
    examples: [{ expr: 'e^x', order: 4 }, { expr: 'sin(x)', order: 7 }, { expr: 'ln(x)', center: '1', order: 3 }, { expr: '1/(1-x)', order: 5 }],
  },
  convergence: {
    title: 'Series Convergence',
    blurb: 'Divergence, geometric, p-series, ratio, limit comparison, integral and alternating series tests.',
    fields: [
      { name: 'term', label: 'aₙ =', type: 'expr', placeholder: 'e.g. 1/n^2' },
      { name: 'start', label: 'Start at n =', type: 'text', placeholder: '1', optional: true, small: true },
    ],
    examples: [{ term: '1/n^2' }, { term: '(2/3)^n', start: '0' }, { term: '(-1)^n / n' }, { term: 'n!/10^n' }, { term: 'n/(n^3+1)' }, { term: '1/(n ln(n))', start: '2' }, { term: 'n/(n+1)' }],
  },
  partial: {
    title: 'Partial Derivative',
    blurb: 'Treat the other variables as constants. Use xy for the mixed partial f_xy.',
    fields: [
      { name: 'expr', label: 'f =', type: 'expr', placeholder: 'e.g. x^2 y^3 + sin(xy)' },
      { name: 'vars', label: 'With respect to', type: 'text', placeholder: 'x   (or xy, yy, …)', small: true },
      point('At point (optional)', 'e.g. x=1, y=2'),
    ],
    examples: [{ expr: 'x^2 y^3 + sin(xy)', vars: 'x' }, { expr: 'x^2 y^3 + sin(xy)', vars: 'xy' }, { expr: 'e^(x y) ln(y)', vars: 'y' }],
  },
  gradient: {
    title: 'Gradient',
    blurb: '∇f: the vector of all partial derivatives.',
    fields: [
      { name: 'expr', label: 'f =', type: 'expr', placeholder: 'e.g. x^2 y + y z^2' },
      point('At point (optional)', 'e.g. 1, 2, 3'),
    ],
    examples: [{ expr: 'x^2 y + y z^2', point: '1, 2, 3' }, { expr: 'x e^(xy)' }],
  },
  directional: {
    title: 'Directional Derivative',
    blurb: 'D_u f = ∇f · u (the direction is normalized for you).',
    fields: [
      { name: 'expr', label: 'f =', type: 'expr', placeholder: 'e.g. x^2 + y^2' },
      { name: 'point', label: 'At point', type: 'text', placeholder: 'e.g. 1, 1', small: true },
      { name: 'direction', label: 'Direction vector', type: 'text', placeholder: 'e.g. 3, 4', small: true },
    ],
    examples: [{ expr: 'x^2 + y^2', point: '1, 1', direction: '3, 4' }, { expr: 'x y z', point: '1, 2, 3', direction: '1, 1, 1' }],
  },
  multiple: {
    title: 'Double / Triple Integral',
    blurb: 'Iterated integrals in Cartesian, polar, cylindrical or spherical coordinates.',
    fields: [
      { name: 'expr', label: 'Integrand f =', type: 'expr', placeholder: 'e.g. x y  (in x, y, z; converted for you)' },
      { name: 'coords', label: 'Coordinates', type: 'select', options: [['cartesian', 'Cartesian'], ['polar', 'Polar (r, θ)'], ['cylindrical', 'Cylindrical (r, θ, z)'], ['spherical', 'Spherical (ρ, φ, θ)']] },
      { name: 'bounds', label: 'Bounds (innermost integral first)', type: 'bounds' },
    ],
    examples: [
      { expr: 'x y', coords: 'cartesian', bounds: [{ var: 'y', lower: '0', upper: 'x' }, { var: 'x', lower: '0', upper: '1' }, { var: '', lower: '', upper: '' }] },
      { expr: 'x^2 + y^2', coords: 'polar', bounds: [{ var: 'r', lower: '0', upper: '2' }, { var: 'theta', lower: '0', upper: '2pi' }, { var: '', lower: '', upper: '' }] },
      { expr: 'x + y + z', coords: 'cartesian', bounds: [{ var: 'z', lower: '0', upper: '1' }, { var: 'y', lower: '0', upper: '1' }, { var: 'x', lower: '0', upper: '1' }] },
      { expr: '1', coords: 'spherical', bounds: [{ var: 'rho', lower: '0', upper: '1' }, { var: 'phi', lower: '0', upper: 'pi' }, { var: 'theta', lower: '0', upper: '2pi' }] },
    ],
  },
  lagrange: {
    title: 'Lagrange Multipliers',
    blurb: 'Optimize f subject to a constraint g = c using ∇f = λ∇g.',
    fields: [
      { name: 'expr', label: 'Optimize f =', type: 'expr', placeholder: 'e.g. x y' },
      { name: 'constraint', label: 'Subject to', type: 'expr', placeholder: 'e.g. x + y = 10' },
    ],
    examples: [{ expr: 'x y', constraint: 'x + y = 10' }, { expr: 'x^2 + y^2', constraint: 'x y = 1' }, { expr: 'x + 2y', constraint: 'x^2 + y^2 = 5' }],
  },
  divergence: {
    title: 'Divergence',
    blurb: '∇ · F for a vector field F = ⟨P, Q, R⟩.',
    fields: [
      { name: 'field', label: 'F = ⟨P, Q, R⟩', type: 'text', placeholder: 'e.g. x^2, x y, z' },
      point('At point (optional)', 'e.g. 1, 2, 3'),
    ],
    examples: [{ field: 'x^2, x y, z' }, { field: 'x y z, y^2, z x', point: '1, 1, 1' }],
  },
  curl: {
    title: 'Curl',
    blurb: '∇ × F for a vector field F = ⟨P, Q, R⟩.',
    fields: [
      { name: 'field', label: 'F = ⟨P, Q, R⟩', type: 'text', placeholder: 'e.g. y, -x, 0' },
      point('At point (optional)', 'e.g. 1, 2, 3'),
    ],
    examples: [{ field: 'y, -x, 0' }, { field: 'x y, y z, z x' }, { field: '2x y, x^2 + 2y z, y^2' }],
  },
};

export const DEFAULT_BOUNDS = {
  cartesian: [{ var: 'y', lower: '', upper: '' }, { var: 'x', lower: '', upper: '' }, { var: '', lower: '', upper: '' }],
  polar: [{ var: 'r', lower: '', upper: '' }, { var: 'theta', lower: '', upper: '' }, { var: '', lower: '', upper: '' }],
  cylindrical: [{ var: 'z', lower: '', upper: '' }, { var: 'r', lower: '', upper: '' }, { var: 'theta', lower: '', upper: '' }],
  spherical: [{ var: 'rho', lower: '', upper: '' }, { var: 'phi', lower: '', upper: '' }, { var: 'theta', lower: '', upper: '' }],
};

export function emptyParams(op) {
  const p = {};
  for (const f of OPS[op].fields) {
    if (f.type === 'select') p[f.name] = f.options[0][0];
    else if (f.type === 'bounds') p[f.name] = DEFAULT_BOUNDS.cartesian.map((b) => ({ ...b }));
    else p[f.name] = '';
  }
  return p;
}
