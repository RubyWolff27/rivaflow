import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Target, Swords, ShieldAlert, BookOpen, AlertTriangle, ChevronRight,
  ChevronDown, Plus, Star, Trash2, Sparkles,
} from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { analyticsApi, sessionsApi, gamePlansApi, getErrorMessage } from '../api/client';
import { useToast } from '../contexts/ToastContext';
import { logger } from '../utils/logger';
import { CardSkeleton, Chip, EmptyState } from '../components/ui';
import type { Session, GamePlan, GamePlanNode } from '../types';
import type { TechniquesData } from '../components/analytics/reportTypes';

const CATEGORY_COLORS: Record<string, string> = {
  submission: '#EF4444',
  position: '#3B82F6',
  sweep: '#F59E0B',
  pass: '#10B981',
  takedown: '#8B5CF6',
  escape: '#06B6D4',
  defense: '#6366F1',
  movement: '#EC4899',
  concept: '#64748B',
};

const NODE_TYPE_COLORS: Record<string, string> = {
  position: '#3B82F6',
  technique: '#8B5CF6',
  submission: '#EF4444',
  sweep: '#F59E0B',
  pass: '#10B981',
  escape: '#06B6D4',
};

const BELT_OPTIONS = [
  { value: 'white', label: 'White', color: '#E5E7EB' },
  { value: 'blue', label: 'Blue', color: '#3B82F6' },
  { value: 'purple', label: 'Purple', color: '#8B5CF6' },
  { value: 'brown', label: 'Brown', color: '#92400E' },
  { value: 'black', label: 'Black', color: '#1F2937' },
];

const ARCHETYPE_OPTIONS = [
  { value: 'guard_player', label: 'Guard Player', desc: 'Bottom game focused' },
  { value: 'top_passer', label: 'Top Passer', desc: 'Passing and pressure' },
];

const NODE_TYPES = ['position', 'technique', 'submission', 'sweep', 'pass', 'escape'];

// --- Sub-components ---

function ConfidenceDots({ level }: { level: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: i <= level ? 'var(--accent)' : 'var(--border)' }}
        />
      ))}
    </div>
  );
}

function TreeNode({
  node,
  depth,
  onDelete,
}: {
  node: GamePlanNode;
  depth: number;
  onDelete: (id: number) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  const color = NODE_TYPE_COLORS[node.node_type] || 'var(--muted)';

  return (
    <div style={{ paddingLeft: depth > 0 ? 16 : 0 }}>
      <div
        className="flex items-center gap-2 py-1.5 px-2 rounded-lg group"
        style={{ backgroundColor: depth === 0 ? 'var(--surfaceElev)' : 'transparent' }}
      >
        {hasChildren ? (
          <button onClick={() => setExpanded(!expanded)} className="p-0.5">
            {expanded ? (
              <ChevronDown className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
            )}
          </button>
        ) : (
          <span className="w-4" />
        )}

        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />

        <span className="text-sm flex-1" style={{ color: 'var(--text)' }}>
          {node.name}
        </span>

        <span
          className="text-[10px] px-1.5 py-0.5 rounded"
          style={{ backgroundColor: color + '20', color }}
        >
          {node.node_type}
        </span>

        {node.is_focus && (
          <Star className="w-3 h-3" style={{ color: '#F59E0B', fill: '#F59E0B' }} />
        )}

        <ConfidenceDots level={node.confidence} />

        {node.attempts > 0 && (
          <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
            {node.successes}/{node.attempts}
          </span>
        )}

        <button
          onClick={() => onDelete(node.id)}
          className="opacity-0 group-hover:opacity-100 p-0.5 transition-opacity"
          title="Delete node"
        >
          <Trash2 className="w-3 h-3" style={{ color: 'var(--muted)' }} />
        </button>
      </div>

      {expanded && hasChildren && (
        <div className="ml-2 border-l" style={{ borderColor: 'var(--border)' }}>
          {node.children!.map((child) => (
            <TreeNode key={child.id} node={child} depth={depth + 1} onDelete={onDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon, label, value, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div
      className="p-4 rounded-[14px]"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span style={{ color: 'var(--muted)' }}>{icon}</span>
        <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
          {label}
        </span>
      </div>
      <p className="text-2xl font-semibold" style={{ color: color || 'var(--text)' }}>
        {value}
      </p>
    </div>
  );
}

// --- Main Component ---

export default function MyGame() {
  usePageTitle('My Game');
  const navigate = useNavigate();
  const toast = useToast();

  // Stats data
  const [techData, setTechData] = useState<TechniquesData | null>(null);
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  // Game plan tree
  const [plan, setPlan] = useState<GamePlan | null>(null);
  const [planLoading, setPlanLoading] = useState(true);

  // Wizard state
  const [selectedBelt, setSelectedBelt] = useState('white');
  const [selectedArchetype, setSelectedArchetype] = useState('guard_player');
  const [generating, setGenerating] = useState(false);

  // Add node state
  const [addingNode, setAddingNode] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeType, setNewNodeType] = useState('technique');
  const [newNodeParent, setNewNodeParent] = useState<number | undefined>(undefined);

  // Load stats data
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [techRes, sessRes] = await Promise.all([
          analyticsApi.techniqueBreakdown(),
          sessionsApi.list(20),
        ]);
        if (!cancelled) {
          setTechData(techRes.data);
          const sessions = (sessRes.data || []).filter(
            (s: Session) => (s.techniques && s.techniques.length > 0) || s.notes
          );
          setRecentSessions(sessions.slice(0, 8));
        }
      } catch (err) {
        logger.debug('My Game data load error', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  // Load game plan
  const loadPlan = async () => {
    setPlanLoading(true);
    try {
      const res = await gamePlansApi.getCurrent();
      const data = res.data;
      setPlan(data?.plan !== undefined ? data.plan : data?.id ? data : null);
    } catch (err) {
      logger.debug('No game plan available', err);
      setPlan(null);
    } finally {
      setPlanLoading(false);
    }
  };

  useEffect(() => {
    loadPlan();
  }, []);

  // Actions
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await gamePlansApi.generate({
        belt_level: selectedBelt,
        archetype: selectedArchetype,
      });
      toast.success('Game plan generated!');
      loadPlan();
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteNode = async (nodeId: number) => {
    if (!plan) return;
    try {
      await gamePlansApi.deleteNode(plan.id, nodeId);
      toast.success('Node deleted');
      loadPlan();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleAddNode = async () => {
    if (!plan || !newNodeName.trim()) return;
    try {
      await gamePlansApi.addNode(plan.id, {
        name: newNodeName.trim(),
        node_type: newNodeType,
        parent_id: newNodeParent,
      });
      setNewNodeName('');
      setAddingNode(false);
      toast.success('Node added');
      loadPlan();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  // Loading
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
          <CardSkeleton lines={1} />
        </div>
        <CardSkeleton lines={4} />
      </div>
    );
  }

  const hasData = techData && (techData.summary?.total_unique_techniques_used ?? 0) > 0;
  const subStats = techData?.submission_stats;

  if (!hasData && recentSessions.length === 0 && !plan && !planLoading) {
    return (
      <div className="py-8">
        <EmptyState
          icon={Target}
          title="Build Your Game"
          description="Log sessions with techniques, submissions, and notes to see your training data come to life here. The more you log, the more your game reveals itself."
          actionLabel="Log a Session"
          actionPath="/log"
        />
      </div>
    );
  }

  const subRatio = subStats
    ? subStats.total_submissions_for + subStats.total_submissions_against > 0
      ? (subStats.total_submissions_for / (subStats.total_submissions_for + subStats.total_submissions_against) * 100).toFixed(0)
      : null
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Target className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>My Game</h1>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Built from your actual training data
          </p>
        </div>
      </div>

      {/* Stats Row */}
      {hasData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard
            icon={<BookOpen className="w-4 h-4" />}
            label="Techniques"
            value={techData?.summary?.total_unique_techniques_used ?? 0}
          />
          <StatCard
            icon={<Swords className="w-4 h-4" />}
            label="Subs For"
            value={subStats?.total_submissions_for ?? 0}
            color="var(--accent)"
          />
          <StatCard
            icon={<ShieldAlert className="w-4 h-4" />}
            label="Subs Against"
            value={subStats?.total_submissions_against ?? 0}
          />
          <StatCard
            icon={<AlertTriangle className="w-4 h-4" />}
            label="Stale (30d)"
            value={techData?.summary?.stale_count ?? 0}
            color={techData?.summary?.stale_count ? '#F59E0B' : undefined}
          />
        </div>
      )}

      {/* Sub Ratio Bar */}
      {subStats && (subStats.total_submissions_for + subStats.total_submissions_against) > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase" style={{ color: 'var(--muted)' }}>
              Submission Ratio
            </span>
            <span className="text-sm font-bold" style={{ color: 'var(--accent)' }}>
              {subRatio}% yours
            </span>
          </div>
          <div className="w-full h-3 rounded-full overflow-hidden flex" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-full rounded-l-full transition-all"
              style={{ width: `${subRatio}%`, backgroundColor: 'var(--accent)' }}
            />
            <div
              className="h-full rounded-r-full"
              style={{
                width: `${100 - Number(subRatio)}%`,
                backgroundColor: 'var(--muted)',
                opacity: 0.3,
              }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {subStats.total_submissions_for} for
            </span>
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
              {subStats.total_submissions_against} against
            </span>
          </div>
        </div>
      )}

      {/* ═══════════════ GAME PLAN TREE ═══════════════ */}
      <div
        className="p-4 rounded-[14px]"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Technique Mind Map
            </h3>
          </div>
          {plan && (
            <button
              onClick={() => setAddingNode(!addingNode)}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg transition-colors"
              style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
            >
              <Plus className="w-3 h-3" />
              Add Node
            </button>
          )}
        </div>

        {planLoading ? (
          <div className="space-y-2">
            <div className="h-6 rounded animate-pulse" style={{ backgroundColor: 'var(--surfaceElev)' }} />
            <div className="h-6 rounded animate-pulse ml-4" style={{ backgroundColor: 'var(--surfaceElev)' }} />
            <div className="h-6 rounded animate-pulse ml-4" style={{ backgroundColor: 'var(--surfaceElev)' }} />
          </div>
        ) : !plan ? (
          /* ── Wizard: Create Game Plan ── */
          <div>
            <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
              A technique mind map — a visual tree of positions, submissions, sweeps, and escapes
              tailored to your belt level and style. Track proficiency and focus areas as you progress.
            </p>

            <div className="space-y-4">
              {/* Belt Selection */}
              <div>
                <label className="text-xs font-medium uppercase mb-2 block" style={{ color: 'var(--muted)' }}>
                  Belt Level
                </label>
                <div className="flex gap-2">
                  {BELT_OPTIONS.map((belt) => (
                    <button
                      key={belt.value}
                      onClick={() => setSelectedBelt(belt.value)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                      style={{
                        border: `2px solid ${selectedBelt === belt.value ? belt.color : 'var(--border)'}`,
                        backgroundColor: selectedBelt === belt.value ? belt.color + '20' : 'transparent',
                        color: selectedBelt === belt.value ? belt.color : 'var(--muted)',
                      }}
                    >
                      {belt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Archetype Selection */}
              <div>
                <label className="text-xs font-medium uppercase mb-2 block" style={{ color: 'var(--muted)' }}>
                  Style
                </label>
                <div className="flex gap-2">
                  {ARCHETYPE_OPTIONS.map((arch) => (
                    <button
                      key={arch.value}
                      onClick={() => setSelectedArchetype(arch.value)}
                      className="px-3 py-2 rounded-lg text-left transition-all"
                      style={{
                        border: `2px solid ${selectedArchetype === arch.value ? 'var(--accent)' : 'var(--border)'}`,
                        backgroundColor: selectedArchetype === arch.value ? 'var(--accent)' + '10' : 'transparent',
                      }}
                    >
                      <div className="text-sm font-medium" style={{ color: 'var(--text)' }}>{arch.label}</div>
                      <div className="text-[10px]" style={{ color: 'var(--muted)' }}>{arch.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors"
                style={{
                  backgroundColor: generating ? 'var(--surfaceElev)' : 'var(--accent)',
                  color: generating ? 'var(--muted)' : '#fff',
                }}
              >
                {generating ? 'Generating...' : 'Generate Game Plan'}
              </button>
            </div>
          </div>
        ) : (
          /* ── Game Plan Tree ── */
          <div className="space-y-3">
            {/* Plan title */}
            {plan.title && (
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                  {plan.title}
                </span>
              </div>
            )}

            {/* Focus Areas */}
            {plan.focus_nodes && plan.focus_nodes.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1.5 mb-2">
                  <Star className="w-3.5 h-3.5" style={{ color: '#F59E0B' }} />
                  <span className="text-xs font-semibold uppercase" style={{ color: 'var(--muted)' }}>
                    Focus Areas
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {plan.focus_nodes.map((fn) => (
                    <span
                      key={fn.id}
                      className="text-xs px-2 py-1 rounded-lg"
                      style={{ backgroundColor: '#F59E0B20', color: '#F59E0B' }}
                    >
                      {fn.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Add Node Form */}
            {addingNode && (
              <div
                className="p-3 rounded-lg mb-3 space-y-2"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <input
                  type="text"
                  value={newNodeName}
                  onChange={(e) => setNewNodeName(e.target.value)}
                  placeholder="Node name..."
                  className="w-full px-3 py-1.5 text-sm rounded-lg"
                  style={{
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                  }}
                />
                <div className="flex gap-2">
                  <select
                    value={newNodeType}
                    onChange={(e) => setNewNodeType(e.target.value)}
                    className="flex-1 px-2 py-1.5 text-xs rounded-lg"
                    style={{
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border)',
                      color: 'var(--text)',
                    }}
                  >
                    {NODE_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <select
                    value={newNodeParent ?? ''}
                    onChange={(e) => setNewNodeParent(e.target.value ? Number(e.target.value) : undefined)}
                    className="flex-1 px-2 py-1.5 text-xs rounded-lg"
                    style={{
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border)',
                      color: 'var(--text)',
                    }}
                  >
                    <option value="">Root (no parent)</option>
                    {plan.flat_nodes?.map((fn) => (
                      <option key={fn.id} value={fn.id}>{fn.name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleAddNode}
                    className="px-3 py-1.5 text-xs rounded-lg font-medium"
                    style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
                  >
                    Add
                  </button>
                  <button
                    onClick={() => { setAddingNode(false); setNewNodeName(''); }}
                    className="px-3 py-1.5 text-xs rounded-lg"
                    style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Tree Nodes */}
            {plan.nodes && plan.nodes.length > 0 ? (
              <div className="space-y-0.5">
                {plan.nodes.map((node) => (
                  <TreeNode key={node.id} node={node} depth={0} onDelete={handleDeleteNode} />
                ))}
              </div>
            ) : (
              <p className="text-sm py-4 text-center" style={{ color: 'var(--muted)' }}>
                No nodes yet. Click &quot;Add Node&quot; to start building your tree.
              </p>
            )}

            {/* Node Type Legend */}
            <div className="flex flex-wrap gap-3 pt-3 border-t" style={{ borderColor: 'var(--border)' }}>
              {NODE_TYPES.map((type) => (
                <div key={type} className="flex items-center gap-1.5">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: NODE_TYPE_COLORS[type] || 'var(--muted)' }}
                  />
                  <span className="text-[10px]" style={{ color: 'var(--muted)' }}>{type}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Top Submissions */}
      {techData?.top_submissions && techData.top_submissions.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Top Submissions
          </h3>
          <div className="space-y-2">
            {techData.top_submissions.slice(0, 6).map((sub, i) => {
              const maxCount = techData.top_submissions![0].count;
              const pct = maxCount > 0 ? (sub.count / maxCount) * 100 : 0;
              return (
                <div key={sub.name} className="flex items-center gap-3">
                  <span className="text-xs font-bold w-5 text-right" style={{ color: 'var(--muted)' }}>
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{sub.name}</span>
                      <span className="text-sm font-semibold" style={{ color: 'var(--accent)' }}>
                        {sub.count}
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${pct}%`, backgroundColor: 'var(--accent)' }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      {techData?.category_breakdown && techData.category_breakdown.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Technique Categories
          </h3>
          <div className="space-y-3">
            {[...techData.category_breakdown]
              .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
              .map((cat) => {
                const maxCount = Math.max(...techData.category_breakdown!.map(c => c.count ?? 0));
                const pct = maxCount > 0 ? ((cat.count ?? 0) / maxCount) * 100 : 0;
                const color = CATEGORY_COLORS[cat.category ?? ''] || 'var(--accent)';
                return (
                  <div key={cat.category}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-sm capitalize" style={{ color: 'var(--text)' }}>
                          {cat.category}
                        </span>
                      </div>
                      <span className="text-xs" style={{ color: 'var(--muted)' }}>{cat.count}</span>
                    </div>
                    <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Recent Training Notes */}
      {recentSessions.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Recent Training Notes
          </h3>
          <div className="space-y-3">
            {recentSessions.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/sessions/${s.id}`)}
                className="w-full text-left p-3 rounded-lg transition-colors hover:brightness-110"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                    {new Date(s.session_date).toLocaleDateString('en-AU', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                    {' '}&middot; {s.class_type}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                </div>
                {s.notes && (
                  <p className="text-sm line-clamp-2 mb-1.5" style={{ color: 'var(--text)' }}>
                    {s.notes}
                  </p>
                )}
                {s.techniques && s.techniques.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {s.techniques.slice(0, 4).map((t) => (
                      <span
                        key={t}
                        className="text-[10px] px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: 'var(--accent)' + '15',
                          color: 'var(--accent)',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                    {s.techniques.length > 4 && (
                      <span className="text-[10px] px-2 py-0.5" style={{ color: 'var(--muted)' }}>
                        +{s.techniques.length - 4} more
                      </span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stale Techniques */}
      {techData?.stale_techniques && techData.stale_techniques.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4" style={{ color: '#F59E0B' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              Stale Techniques
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: '#F59E0B20', color: '#F59E0B' }}>
              Not trained in 30+ days
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {techData.stale_techniques.slice(0, 15).map((tech) => (
              <Chip key={tech.id ?? tech.name}>{tech.name ?? 'Unknown'}</Chip>
            ))}
            {techData.stale_techniques.length > 15 && (
              <Chip>+{techData.stale_techniques.length - 15} more</Chip>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
