import { useState } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { ROADMAPS } from '../data/roadmaps/crossSleeve';
import RoadmapView from '../components/roadmap/RoadmapView';
import ErrorBoundary from '../components/ErrorBoundary';

/**
 * Roadmaps live on their own route, NOT as a tab on the Purple Belt page.
 *
 * That separation is the point: coaches sign off the AJJ syllabus against their
 * own document, so anything of Ruby's own invention sitting next to it — even
 * clearly labelled — risks being read as one of their requirements. The
 * syllabus page stays theirs. This page is his.
 */
export default function Roadmaps() {
  usePageTitle('Roadmaps');
  const [activeId, setActiveId] = useState(ROADMAPS[0].id);
  const active = ROADMAPS.find((r) => r.id === activeId) ?? ROADMAPS[0];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
          Roadmaps
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Your own systems, mapped as decisions. Separate from the Academy&rsquo;s syllabus by design.
        </p>
      </div>

      {ROADMAPS.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {ROADMAPS.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => setActiveId(r.id)}
              className="px-3 py-1.5 rounded-lg text-sm"
              style={{
                backgroundColor: r.id === activeId ? 'var(--surfaceElev)' : 'transparent',
                color: r.id === activeId ? 'var(--text)' : 'var(--muted)',
                border: '1px solid var(--border)',
              }}
            >
              {r.title}
            </button>
          ))}
        </div>
      )}

      <ErrorBoundary compact>
        <RoadmapView roadmap={active} />
      </ErrorBoundary>
    </div>
  );
}
