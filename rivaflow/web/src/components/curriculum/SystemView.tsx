import type { CurriculumSlot } from '../../types/curriculum';
import { COMPONENTS, POSITIONS, mappedCells, systemCount } from './constants';

interface SystemViewProps {
  slots: CurriculumSlot[];
}

/**
 * "Do I own a game?" — 4 positions × 4 components, counting only declared
 * a-game/b-game slots that reached grooved or better. The mapping from
 * syllabus requirement to cell is documented in `constants.ts`.
 */
export default function SystemView({ slots }: SystemViewProps) {
  const mapped = mappedCells();

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-base font-semibold" style={{ color: 'var(--text)' }}>
          Your game system
        </h2>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Declared A-game and B-game sequences at grooved or better. Syllabus-only slots
          are not counted here — this asks whether you own a game, not whether you covered
          the syllabus.
        </p>
      </div>

      <div className="overflow-x-auto -mx-1 px-1">
        <table className="w-full text-xs border-collapse" data-testid="system-grid">
          <thead>
            <tr>
              <th className="text-left font-medium py-2 pr-2" style={{ color: 'var(--muted)' }}>
                Position
              </th>
              {COMPONENTS.map((component) => (
                <th
                  key={component}
                  className="font-medium py-2 px-1 text-center align-bottom"
                  style={{ color: 'var(--muted)', minWidth: '68px' }}
                >
                  {component}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {POSITIONS.map((position) => (
              <tr key={position} style={{ borderTop: '1px solid var(--border)' }}>
                <th
                  scope="row"
                  className="text-left font-medium py-2 pr-2 whitespace-nowrap"
                  style={{ color: 'var(--text)' }}
                >
                  {position}
                </th>
                {COMPONENTS.map((component) => {
                  const isMapped = mapped.has(`${position}|${component}`);
                  const count = isMapped ? systemCount(slots, position, component) : 0;
                  const label = !isMapped ? '·' : count === 0 ? '—' : String(count);
                  const title = !isMapped
                    ? `${position} · ${component}: the AJJ purple syllabus has no requirement here. Nothing to count — this is not a zero.`
                    : count === 0
                      ? `${position} · ${component}: nothing grooved yet.`
                      : `${position} · ${component}: ${count} sequence${count === 1 ? '' : 's'} at grooved or better.`;
                  return (
                    <td
                      key={component}
                      className="text-center py-3 px-1"
                      data-testid={`system-cell-${position}-${component}`}
                      title={title}
                    >
                      <span
                        className="text-base font-semibold"
                        style={{
                          color:
                            !isMapped || count === 0 ? 'var(--muted)' : 'var(--text)',
                          opacity: isMapped ? 1 : 0.4,
                        }}
                      >
                        {label}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[11px]" style={{ color: 'var(--muted)' }}>
        <strong style={{ color: 'var(--text)' }}>—</strong> nothing grooved yet ·{' '}
        <strong style={{ color: 'var(--text)' }}>·</strong> the syllabus sets no requirement
        for that cell. Three cells are structurally empty: the AJJ purple syllabus tests
        almost no top-game defence and almost no troubleshooting. That gap is real, and it
        is yours to fill off-syllabus.
      </p>
    </div>
  );
}
