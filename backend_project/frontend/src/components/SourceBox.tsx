import type { SourceEvidence } from '../types';

interface SourceBoxProps {
  source?: SourceEvidence | null;
}

export function SourceBox({ source }: SourceBoxProps) {
  if (!source) return null;
  return (
    <details className="source-box">
      <summary>
        Источник: <strong>{source.title}</strong> ({source.doc_type})
        {source.score ? ` — релевантность ${Math.round(source.score * 100)}%` : ''}
      </summary>
      <blockquote className="source-fragment">{source.fragment}</blockquote>
      <div className="muted">doc_id: {source.doc_id}</div>
    </details>
  );
}
