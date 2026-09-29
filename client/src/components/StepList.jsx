import { MathBlock, MathText } from './MathText.jsx';

// Steps arrive flat with a depth; headings are steps whose text starts with "### ".
export default function StepList({ steps, showDetail }) {
  let number = 0;
  const visible = steps.filter((s) => showDetail || s.depth === 0);

  return (
    <ol className="steps">
      {visible.map((s, i) => {
        if (s.text.startsWith('### ')) {
          return (
            <li key={i} className="step-heading" style={{ '--depth': s.depth }}>
              <MathText text={s.text.slice(4)} />
              {s.math && <MathBlock tex={s.math} />}
            </li>
          );
        }
        const top = s.depth === 0;
        if (top) number += 1;
        return (
          <li key={i} className={top ? 'step' : 'step sub'} style={{ '--depth': s.depth }}>
            {top && <span className="step-num">{number}</span>}
            <div className="step-body">
              {s.text && <MathText text={s.text} as="p" />}
              {s.math && <MathBlock tex={s.math} />}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
