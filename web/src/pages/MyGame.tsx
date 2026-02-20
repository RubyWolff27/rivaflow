import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { ChevronRight, ChevronDown, Plus, Target, Star, Trash2, Edit3, Sparkles } from 'lucide-react';
import { EmptyState } from '../components/ui';
import { useToast } from '../contexts/ToastContext';
import { gamePlansApi, getErrorMessage } from '../api/client';
import { logger } from '../utils/logger';
import type { GamePlan, GamePlanNode } from '../types';

const NODE_TYPE_COLORS: Record<string, string> = {
  position: '#3B82F6',
  technique: '#8B5CF6',
  submission: '#EF4444',
  sweep: '#F59E0B',
  pass: '#10B981',
  escape: '#06B6D4',
};

const BELT_OPTIONS = [
  { value: 'white', label: 'White Belt', color: '#FFFFFF' },
  { value: 'blue', label: 'Blue Belt', color: '#3B82F6' },
  { value: 'purple', label: 'Purple Belt', color: '#8B5CF6' },
  { value: 'brown', label: 'Brown Belt', color: '#92400E' },
  { value: 'black', label: 'Black Belt', color: '#1F2937' },
];

const ARCHETYPE_OPTIONS = [
  { value: 'guard_player', label: 'Guard Player', desc: 'Bottom game focused' },
  { value: 'top_passer', label: 'Top Passer', desc: 'Passing and pressure' },
];

function ConfidenceDots({ level }: { level: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-2 h-2 rounded-full"
          style={{
            backgroundColor: i <= level ? 'var(--accent)' : 'var(--border)',
          }}
        />
      ))}
    </div>
  );
}

function NodeCard({
  node,
  planId,
  depth = 0,
  onUpdate,
  onDelete,
}: {
  node: GamePlanNode;
  planId: number;
  depth?: number;
  onUpdate: () => void;
  onDelete: (nodeId: number) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(node.name);
  const [editConfidence, setEditConfidence] = useState(node.confidence);
  const toast = useToast();
  const hasChildren = node.children && node.children.length > 0;
  const typeColor = NODE_TYPE_COLORS[node.node_type] || '#6B7280';

  const handleSave = async () => {
    try {
      await gamePlansApi.updateNode(planId, node.id, {
        name: editName,
        confidence: editConfidence,
      });
      setEditing(false);
      onUpdate();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const toggleFocus = async () => {
    try {
      await gamePlansApi.updateNode(planId, node.id, {
        is_focus: !node.is_focus,
      });
      onUpdate();
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  return (
    <div style={{ marginLeft: depth > 0 ? '1.25rem' : 0 }}>
      <div
        className="flex items-center gap-2 p-2 rounded-lg mb-1 group transition-colors"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        {hasChildren ? (
          <button onClick={() => setExpanded(!expanded)} className="p-0.5">
            {expanded ? (
              <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />
            ) : (
              <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
            )}
          </button>
        ) : (
          <div className="w-5" />
        )}

        <span
          className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded"
          style={{ backgroundColor: typeColor + '20', color: typeColor }}
        >
          {node.node_type}
        </span>

        {editing ? (
          <div className="flex-1 flex items-center gap-2">
            <input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="flex-1 text-sm px-2 py-1 rounded border"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            />
            <select
              value={editConfidence}
              onChange={(e) => setEditConfidence(Number(e.target.value))}
              className="text-xs px-1 py-1 rounded border"
              style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            >
              {[1, 2, 3, 4, 5].map((v) => (
                <option key={v} value={v}>
                  {v}/5
                </option>
              ))}
            </select>
            <button
              onClick={handleSave}
              className="text-xs px-2 py-1 rounded"
              style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
            >
              Save
            </button>
            <button
              onClick={() => setEditing(false)}
              className="text-xs px-2 py-1 rounded"
              style={{ color: 'var(--muted)' }}
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            <span className="flex-1 text-sm font-medium" style={{ color: 'var(--text)' }}>
              {node.name}
            </span>
            <ConfidenceDots level={node.confidence} />
            {node.is_focus && (
              <Target className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            )}
            {node.attempts > 0 && (
              <span className="text-[10px]" style={{ color: 'var(--muted)' }}>
                {node.successes}/{node.attempts}
              </span>
            )}
            <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
              <button onClick={toggleFocus} title="Toggle focus">
                <Star
                  className="w-3.5 h-3.5"
                  style={{ color: node.is_focus ? 'var(--accent)' : 'var(--muted)' }}
                />
              </button>
              <button onClick={() => setEditing(true)} title="Edit">
                <Edit3 className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
              </button>
              <button onClick={() => onDelete(node.id)} title="Delete">
                <Trash2 className="w-3.5 h-3.5" style={{ color: 'var(--error)' }} />
              </button>
            </div>
          </>
        )}
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <NodeCard
              key={child.id}
              node={child}
              planId={planId}
              depth={depth + 1}
              onUpdate={onUpdate}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PlanWizard({ onGenerate }: { onGenerate: () => void }) {
  const [belt, setBelt] = useState('white');
  const [archetype, setArchetype] = useState('guard_player');
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleGenerate = async () => {
    setLoading(true);
    try {
      await gamePlansApi.generate({ belt_level: belt, archetype });
      toast.success('Game plan generated!');
      onGenerate();
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="text-center">
        <Sparkles className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--accent)' }} />
        <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text)' }}>
          Build Your Game
        </h2>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Your game plan is a technique mind map — a visual tree of positions,
          submissions, sweeps, and escapes tailored to your belt level and style.
          Track proficiency and focus areas as you progress.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
            Belt Level
          </label>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
            {BELT_OPTIONS.map((b) => (
              <button
                key={b.value}
                onClick={() => setBelt(b.value)}
                className={`p-3 rounded-[14px] border-2 text-center transition-all ${
                  belt === b.value ? 'scale-105' : 'opacity-70'
                }`}
                style={{
                  borderColor: belt === b.value ? 'var(--accent)' : 'var(--border)',
                  backgroundColor: 'var(--surface)',
                }}
              >
                <div
                  className="w-8 h-3 mx-auto rounded mb-1"
                  style={{
                    backgroundColor: b.color,
                    border: b.value === 'white' ? '1px solid var(--border)' : 'none',
                  }}
                />
                <div className="text-[10px] font-medium" style={{ color: 'var(--text)' }}>
                  {b.label.split(' ')[0]}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
            Archetype
          </label>
          <div className="grid grid-cols-2 gap-3">
            {ARCHETYPE_OPTIONS.map((a) => (
              <button
                key={a.value}
                onClick={() => setArchetype(a.value)}
                className={`p-4 rounded-[14px] border-2 text-left transition-all ${
                  archetype === a.value ? 'scale-[1.02]' : 'opacity-70'
                }`}
                style={{
                  borderColor: archetype === a.value ? 'var(--accent)' : 'var(--border)',
                  backgroundColor: 'var(--surface)',
                }}
              >
                <div className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                  {a.label}
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                  {a.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full py-3 rounded-[14px] font-semibold text-white transition-opacity disabled:opacity-50"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          {loading ? 'Generating...' : 'Generate Game Plan'}
        </button>
      </div>
    </div>
  );
}

export default function MyGame() {
  usePageTitle('My Game');
  const [plan, setPlan] = useState<GamePlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingNode, setAddingNode] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeType, setNewNodeType] = useState('technique');
  const [newNodeParent, setNewNodeParent] = useState<number | undefined>();
  const toast = useToast();

  const loadPlan = async () => {
    try {
      const response = await gamePlansApi.getCurrent();
      setPlan(response.data.plan !== undefined ? (response.data.plan === null ? null : response.data) : response.data.id ? response.data : null);
    } catch (err) {
      logger.debug('No game plan available', err);
      setPlan(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlan();
  }, []);

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

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        <div className="h-64 rounded-[14px] animate-pulse" style={{ backgroundColor: 'var(--surfaceElev)' }} />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="py-8">
        <PlanWizard onGenerate={loadPlan} />
      </div>
    );
  }

  const focusNodes = plan.focus_nodes || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Target className="w-7 h-7" style={{ color: 'var(--accent)' }} />
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
              {plan.title || 'My Game'}
            </h1>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              {plan.belt_level} belt &middot; {plan.archetype?.replace('_', ' ')}
            </p>
          </div>
        </div>
        <button
          onClick={() => setAddingNode(!addingNode)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
          style={{ backgroundColor: 'var(--accent)' }}
        >
          <Plus className="w-4 h-4" />
          Add Node
        </button>
      </div>

      {/* Focus Nodes */}
      {focusNodes.length > 0 && (
        <div
          className="p-4 rounded-[14px]"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-xs font-semibold uppercase mb-2" style={{ color: 'var(--muted)' }}>
            Focus Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {focusNodes.map((n) => (
              <span
                key={n.id}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium"
                style={{
                  backgroundColor: (NODE_TYPE_COLORS[n.node_type] || '#6B7280') + '20',
                  color: NODE_TYPE_COLORS[n.node_type] || '#6B7280',
                }}
              >
                <Target className="w-3 h-3" />
                {n.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Add Node Form */}
      {addingNode && (
        <div
          className="p-4 rounded-[14px] space-y-3"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--accent)' }}
        >
          <div className="flex gap-2">
            <input
              value={newNodeName}
              onChange={(e) => setNewNodeName(e.target.value)}
              placeholder="Node name..."
              className="flex-1 px-3 py-2 rounded-lg text-sm border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
              }}
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleAddNode()}
            />
            <select
              value={newNodeType}
              onChange={(e) => setNewNodeType(e.target.value)}
              className="px-2 py-2 rounded-lg text-sm border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
              }}
            >
              {Object.keys(NODE_TYPE_COLORS).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          {plan.flat_nodes && plan.flat_nodes.length > 0 && (
            <select
              value={newNodeParent || ''}
              onChange={(e) => setNewNodeParent(e.target.value ? Number(e.target.value) : undefined)}
              className="w-full px-3 py-2 rounded-lg text-sm border"
              style={{
                borderColor: 'var(--border)',
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
              }}
            >
              <option value="">No parent (root level)</option>
              {plan.flat_nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name}
                </option>
              ))}
            </select>
          )}
          <div className="flex gap-2">
            <button
              onClick={handleAddNode}
              disabled={!newNodeName.trim()}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              Add
            </button>
            <button
              onClick={() => setAddingNode(false)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ color: 'var(--muted)' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Proficiency Legend */}
      <div
        className="flex flex-wrap items-center gap-4 px-4 py-2.5 rounded-[14px] text-xs"
        style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)', color: 'var(--muted)' }}
      >
        <span className="font-medium" style={{ color: 'var(--text)' }}>Proficiency:</span>
        <span className="flex items-center gap-1.5"><ConfidenceDots level={1} /> Learning</span>
        <span className="flex items-center gap-1.5"><ConfidenceDots level={3} /> Comfortable</span>
        <span className="flex items-center gap-1.5"><ConfidenceDots level={5} /> Mastered</span>
      </div>

      {/* Tree View */}
      <div
        className="p-4 rounded-[14px]"
        style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
      >
        {plan.nodes && plan.nodes.length > 0 ? (
          plan.nodes.map((node) => (
            <NodeCard
              key={node.id}
              node={node}
              planId={plan.id}
              onUpdate={loadPlan}
              onDelete={handleDeleteNode}
            />
          ))
        ) : (
          <EmptyState icon={Target} title="No Techniques Yet" description="Add your first node to start building your game plan." actionLabel="Add Node" />
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center">
        {Object.entries(NODE_TYPE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}
