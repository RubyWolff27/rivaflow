import { useEffect, useState } from 'react';
import { getLocalDateString } from '../../utils/date';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { suggestionsApi, readinessApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Card, CardSkeleton } from '../ui';

interface TriggeredRule {
  name: string;
  recommendation: string;
  explanation: string;
  priority: number;
}

/** Strip unresolved {placeholder} tokens from suggestion text. */
const sanitizeSuggestion = (text: string) =>
  text.replace(/\{[a-z_]+\}/gi, '').replace(/\s{2,}/g, ' ').trim();

const RULE_LABELS: Record<string, string> = {
  high_stress_low_energy: 'Stress / Low Energy',
  high_soreness: 'High Soreness',
  hotspot_active: 'Injury Hotspot',
  consecutive_gi: 'Consecutive Gi',
  consecutive_nogi: 'Consecutive No-Gi',
  green_light: 'All Clear',
  stale_technique: 'Stale Technique',
};

interface SuggestionData {
  suggestion: string;
  triggered_rules: TriggeredRule[];
  readiness?: { composite_score?: number };
}

export default function ReadinessRecommendation() {
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [compositeScore, setCompositeScore] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await suggestionsApi.getToday();
        if (!cancelled && res.data) {
          setSuggestion(res.data);
          if (res.data.readiness?.composite_score != null) {
            setCompositeScore(res.data.readiness.composite_score);
          }
        }
      } catch (err) {
        logger.debug('Suggestion not available, trying readiness fallback', err);
        // Fallback: try to get readiness score directly
        try {
          const today = getLocalDateString();
          const readRes = await readinessApi.getByDate(today);
          if (!cancelled && readRes.data?.composite_score != null) {
            setCompositeScore(readRes.data.composite_score);
          }
        } catch (err2) {
          logger.debug('No readiness data today', err2);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <CardSkeleton lines={2} />;

  // If no suggestion and no composite score, don't render anything
  if (!suggestion && compositeScore === null) return null;

  // Determine recommendation level
  const score = compositeScore ?? 0;
  let label: string;
  let bgColor: string;
  let textColor: string;

  if (score >= 16) {
    label = 'Train Hard';
    bgColor = 'var(--success-bg)';
    textColor = 'var(--success)';
  } else if (score >= 12) {
    label = 'Light Session';
    bgColor = 'var(--warning-bg)';
    textColor = 'var(--warning)';
  } else {
    label = 'Rest Day';
    bgColor = 'var(--danger-bg)';
    textColor = 'var(--danger)';
  }

  return (
    <Link to="/readiness">
      <Card className="cursor-pointer hover:border-[var(--accent)] transition-colors">
        <div className="flex items-start gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
            style={{ backgroundColor: bgColor }}
          >
            <Sparkles className="w-5 h-5" style={{ color: textColor }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
                What should I do today?
              </h3>
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded"
                style={{ backgroundColor: bgColor, color: textColor }}
              >
                {label}
              </span>
            </div>
            {suggestion?.suggestion ? (
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                {sanitizeSuggestion(suggestion.suggestion)}
              </p>
            ) : (
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Based on your readiness score of {score}/20
              </p>
            )}
            {suggestion?.triggered_rules && suggestion.triggered_rules.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {suggestion.triggered_rules.slice(0, 2).map((rule, i) => (
                  <span
                    key={i}
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)', border: '1px solid var(--border)' }}
                  >
                    {RULE_LABELS[rule.name] || rule.name.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
