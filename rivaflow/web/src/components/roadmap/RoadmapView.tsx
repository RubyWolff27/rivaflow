import { useMemo, useState } from 'react';
import { ChevronRight, CornerDownRight, GitBranch, Home } from 'lucide-react';
import type { Roadmap, RoadmapNode, RoadmapStage } from '../../types/roadmap';

/** Poster-spine labels. Colour is carried by the token set, not new hexes. */
const STAGE_LABEL: Record<RoadmapStage, string> = {
  entry: 'Entry',
  sweep: 'Sweep',
  back: 'Back take',
  submission: 'Submission',
  drill: 'Games & drills',
  principle: 'Principle',
};

function findPath(root: RoadmapNode, targetId: string): RoadmapNode[] | null {
  if (root.id === targetId) return [root];
  for (const child of root.children ?? []) {
    const sub = findPath(child, targetId);
    if (sub) return [root, ...sub];
  }
  return null;
}

/**
 * Children of a reaction are the choices it unlocks. A reaction is never a
 * destination you navigate INTO — it is a heading you read, with its choices
 * listed beneath. So when we render a node's children we flatten one level of
 * reactions into (heading, choices) groups.
 */
type Group = { reaction: RoadmapNode | null; choices: RoadmapNode[] };

function groupChildren(node: RoadmapNode): Group[] {
  const groups: Group[] = [];
  const loose: RoadmapNode[] = [];
  for (const child of node.children ?? []) {
    if (child.kind === 'reaction') {
      groups.push({ reaction: child, choices: child.children ?? [] });
    } else {
      loose.push(child);
    }
  }
  // Free choices first: things you can simply decide read before things that
  // depend on what they give you.
  return loose.length ? [{ reaction: null, choices: loose }, ...groups] : groups;
}

function CueList({ cues }: { cues: string[] }) {
  return (
    <ul className="mt-2 space-y-1">
      {cues.map((cue) => (
        <li key={cue} className="flex items-start gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
          <CornerDownRight className="w-3 h-3 mt-0.5 shrink-0" />
          <span>{cue}</span>
        </li>
      ))}
    </ul>
  );
}

function ChoiceCard({ node, onOpen }: { node: RoadmapNode; onOpen: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = (node.children?.length ?? 0) > 0;
  const hasCues = (node.cues?.length ?? 0) > 0;

  return (
    <div
      className="rounded-[14px] p-3 sm:p-4"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
      data-testid={`roadmap-choice-${node.id}`}
    >
      <div className="flex items-center justify-between gap-3">
        {/* Always navigable, children or not. A node with nothing beyond it
            still deserves its own screen saying so — a tap that silently does
            nothing is worse than an honest dead end. */}
        <button
          type="button"
          className="flex-1 min-w-0 text-left"
          onClick={() => onOpen(node.id)}
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
              {node.label}
            </span>
            {node.stage && (
              <span
                className="shrink-0 px-1.5 py-0.5 rounded-full text-[10px] uppercase tracking-wide"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--muted)' }}
              >
                {STAGE_LABEL[node.stage]}
              </span>
            )}
          </div>
        </button>

        {hasCues && (
          <button
            type="button"
            className="shrink-0 text-[11px] px-2 py-1 rounded-lg"
            style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded ? 'Hide' : 'Cues'}
          </button>
        )}
        <ChevronRight
          className="w-4 h-4 shrink-0"
          style={{ color: 'var(--muted)', opacity: hasChildren ? 1 : 0.35 }}
        />
      </div>

      {expanded && hasCues && <CueList cues={node.cues!} />}
    </div>
  );
}

/**
 * A reaction heading. Deliberately NOT a button: you do not choose what your
 * opponent does. Grey, not accent — a read is not a reward.
 */
function ReactionHeader({ node }: { node: RoadmapNode }) {
  return (
    <div
      className="flex items-center gap-2 mt-4 mb-2 px-1"
      data-testid={`roadmap-reaction-${node.id}`}
    >
      <GitBranch className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--muted)' }} />
      <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
        {node.label}
      </span>
    </div>
  );
}

export default function RoadmapView({ roadmap }: { roadmap: Roadmap }) {
  const [currentId, setCurrentId] = useState(roadmap.root.id);

  const path = useMemo(
    () => findPath(roadmap.root, currentId) ?? [roadmap.root],
    [roadmap.root, currentId]
  );
  const current = path[path.length - 1];
  const groups = useMemo(() => groupChildren(current), [current]);

  return (
    <div className="space-y-4">
      {/* Breadcrumb — the whole context mechanism. Cheaper than a pannable
          canvas and the only thing that survives a phone screen. */}
      <nav
        className="flex items-center gap-1 flex-wrap text-xs sticky top-0 z-10 py-2"
        style={{ backgroundColor: 'var(--bg, transparent)', color: 'var(--muted)' }}
        aria-label="Roadmap path"
      >
        {path.map((node, i) => (
          <span key={node.id} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="w-3 h-3" />}
            <button
              type="button"
              onClick={() => setCurrentId(node.id)}
              className="hover:underline"
              style={{ color: i === path.length - 1 ? 'var(--text)' : 'var(--muted)' }}
            >
              {i === 0 ? <Home className="w-3.5 h-3.5" /> : node.label}
            </button>
          </span>
        ))}
      </nav>

      <div>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
          {current.id === roadmap.root.id ? roadmap.title : current.label}
        </h2>
        <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
          {current.id === roadmap.root.id ? roadmap.subtitle : STAGE_LABEL[current.stage ?? 'entry']}
        </p>
      </div>

      {current.cues && current.cues.length > 0 && (
        <div
          className="rounded-[14px] p-3"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <CueList cues={current.cues} />
        </div>
      )}

      {groups.length === 0 ? (
        <div
          className="rounded-[14px] p-4 text-sm"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--muted)' }}
        >
          Nothing mapped beyond here yet — this branch is honestly empty rather than padded.
        </div>
      ) : (
        groups.map((group, gi) => (
          <div key={group.reaction?.id ?? `loose-${gi}`}>
            {group.reaction && <ReactionHeader node={group.reaction} />}
            <div className="space-y-2">
              {group.choices.map((choice) => (
                <ChoiceCard key={choice.id} node={choice} onOpen={setCurrentId} />
              ))}
            </div>
          </div>
        ))
      )}

      {current.id === roadmap.root.id && roadmap.principles && (
        <div
          className="rounded-[14px] p-4 mt-6"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>
            Principles
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {roadmap.principles.map((p) => (
              <div key={p.label} className="text-xs">
                <span className="font-semibold" style={{ color: 'var(--text)' }}>{p.label}</span>
                <span style={{ color: 'var(--muted)' }}> — {p.detail}</span>
              </div>
            ))}
          </div>
          <p className="text-[11px] mt-3" style={{ color: 'var(--muted)' }}>
            {roadmap.provenance}
          </p>
        </div>
      )}
    </div>
  );
}
