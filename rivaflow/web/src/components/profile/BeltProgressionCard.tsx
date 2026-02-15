import { Award, Plus, Trash2, Edit2 } from 'lucide-react';
import { BELT_GRADES } from '../../constants/belts';
import { getLocalDateString } from '../../utils/date';
import type { Profile, Grading, Friend } from '../../types';

const BELT_COLORS: Record<string, string> = {
  white: '#F3F4F6',
  blue: '#3B82F6',
  purple: '#8B5CF6',
  brown: '#78350F',
  black: '#1F2937',
};

function parseBeltGrade(gradeStr: string) {
  if (!gradeStr) return { beltColor: '#9CA3AF', beltName: 'White', stripes: 0 };

  const lower = gradeStr.toLowerCase();
  const beltBase = lower.split(' ')[0]; // Extract base belt color
  const stripeMatch = gradeStr.match(/\((\d+) stripe/i);
  const stripes = stripeMatch ? parseInt(stripeMatch[1]) : 0;

  return {
    beltColor: BELT_COLORS[beltBase] || '#9CA3AF',
    beltName: beltBase.charAt(0).toUpperCase() + beltBase.slice(1),
    stripes,
    fullGrade: gradeStr,
  };
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

export interface BeltProgressionCardProps {
  profile: Profile | null;
  gradings: Grading[];
  instructors: Friend[];
  gradingForm: {
    grade: string;
    date_graded: string;
    professor: string;
    instructor_id: number | null;
    notes: string;
    photo_url: string;
  };
  onGradingFormChange: (form: BeltProgressionCardProps['gradingForm']) => void;
  showAddGrading: boolean;
  editingGrading: Grading | null;
  onOpenAddGrading: () => void;
  onAddGrading: (e: React.FormEvent) => void;
  onEditGrading: (grading: Grading) => void;
  onUpdateGrading: (e: React.FormEvent) => void;
  onCancelEdit: () => void;
  onDeleteGrading: (id: number) => void;
  onCloseAddGrading: () => void;
  // Photo
  gradingPhotoPreview: string | null;
  uploadingGradingPhoto: boolean;
  onGradingPhotoUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDeleteGradingPhoto: () => void;
}

export default function BeltProgressionCard({
  profile,
  gradings,
  instructors,
  gradingForm,
  onGradingFormChange,
  showAddGrading,
  editingGrading,
  onOpenAddGrading,
  onAddGrading,
  onEditGrading,
  onUpdateGrading,
  onCancelEdit,
  onDeleteGrading,
  onCloseAddGrading,
  gradingPhotoPreview,
  uploadingGradingPhoto,
  onGradingPhotoUpload,
  onDeleteGradingPhoto,
}: BeltProgressionCardProps) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Award className="w-6 h-6 text-[var(--accent)]" />
          <h2 className="text-xl font-semibold">Belt Progression</h2>
        </div>
        <button
          onClick={onOpenAddGrading}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Grading
        </button>
      </div>

      {/* Current Grade Display */}
      {profile?.current_grade && (() => {
        const { beltColor, beltName, stripes } = parseBeltGrade(profile.current_grade);
        return (
          <div className="mb-6 p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
            <p className="text-sm text-[var(--muted)] mb-3">Current Grade</p>
            <div className="flex items-center gap-4">
              <div
                className="w-16 h-10 rounded border-2 flex-shrink-0"
                style={{ backgroundColor: beltColor, borderColor: 'var(--border)' }}
              />
              <div>
                <p className="text-2xl font-bold text-[var(--accent)]">{beltName} Belt</p>
                <div className="flex items-center gap-1 mt-1">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={i}
                      className="w-2.5 h-2.5 rounded-full transition-colors"
                      style={{
                        backgroundColor: i < stripes ? beltColor : 'var(--border)',
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Add/Edit Grading Form */}
      {(showAddGrading || editingGrading) && (
        <form onSubmit={editingGrading ? onUpdateGrading : onAddGrading} className="mb-6 p-4 bg-[var(--surfaceElev)] rounded-lg space-y-4">
          <h3 className="font-semibold text-lg">{editingGrading ? 'Edit Grading' : 'Add New Grading'}</h3>

          <div>
            <label className="label">Belt / Grade</label>
            <select
              className="input"
              value={gradingForm.grade}
              onChange={(e) => onGradingFormChange({ ...gradingForm, grade: e.target.value })}
              required
            >
              <option value="">Select your grade</option>
              {BELT_GRADES.map((grade) => (
                <option key={grade} value={grade}>
                  {grade}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Date Graded</label>
            <input
              type="date"
              className="input"
              value={gradingForm.date_graded}
              onChange={(e) => onGradingFormChange({ ...gradingForm, date_graded: e.target.value })}
              max={getLocalDateString()}
              required
            />
          </div>

          <div>
            <label className="label">Professor / Instructor (optional)</label>
            <select
              className="input"
              value={gradingForm.instructor_id ?? ''}
              onChange={(e) => {
                const instructorId = e.target.value ? parseInt(e.target.value) : null;
                const instructor = instructors.find(i => i.id === instructorId);
                onGradingFormChange({
                  ...gradingForm,
                  instructor_id: instructorId,
                  professor: instructor?.name ?? '',
                });
              }}
            >
              <option value="">Select instructor...</option>
              {instructors.map((instructor) => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name ?? 'Unknown'}
                  {instructor.belt_rank && ` (${instructor.belt_rank} belt)`}
                  {instructor.instructor_certification && ` - ${instructor.instructor_certification}`}
                </option>
              ))}
            </select>
            <p className="text-xs text-[var(--muted)] mt-1">
              Select from your instructor list. <a href="/friends" className="text-[var(--accent)] hover:underline">Add instructors in Friends</a>
            </p>
          </div>

          <div>
            <label className="label">Grading Photo (optional)</label>
            {gradingPhotoPreview || gradingForm.photo_url ? (
              <div className="mb-3">
                <img
                  src={gradingPhotoPreview || gradingForm.photo_url}
                  alt="Grading"
                  className="w-full max-w-sm rounded-lg border border-[var(--border)]"
                />
                <button
                  type="button"
                  onClick={onDeleteGradingPhoto}
                  className="mt-2 text-sm text-red-600 hover:text-red-700"
                >
                  Remove Photo
                </button>
              </div>
            ) : null}
            <label className="btn-secondary cursor-pointer inline-flex items-center gap-2">
              <input
                type="file"
                className="hidden"
                accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                onChange={onGradingPhotoUpload}
                disabled={uploadingGradingPhoto}
              />
              {uploadingGradingPhoto ? 'Uploading...' : gradingForm.photo_url ? 'Change Photo' : 'Upload Photo'}
            </label>
            <p className="text-xs text-[var(--muted)] mt-1">
              Upload a photo of your belt certificate or grading (max 5MB)
            </p>
          </div>

          <div>
            <label className="label">Notes (optional)</label>
            <textarea
              className="input"
              value={gradingForm.notes}
              onChange={(e) => onGradingFormChange({ ...gradingForm, notes: e.target.value })}
              rows={2}
              placeholder="e.g., Focused on passing game, competition preparation"
            />
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">
              {editingGrading ? 'Update Grading' : 'Save Grading'}
            </button>
            <button
              type="button"
              onClick={editingGrading ? onCancelEdit : onCloseAddGrading}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Grading History */}
      {gradings.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-[var(--muted)] uppercase">History</h3>
          {gradings.map((grading) => {
            const { beltColor, stripes } = parseBeltGrade(grading.grade);
            return (
              <div
                key={grading.id}
                className="flex items-start justify-between p-3 bg-[var(--surfaceElev)] rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className="w-12 h-7 rounded border-2 flex-shrink-0"
                      style={{ backgroundColor: beltColor, borderColor: 'var(--border)' }}
                    />
                    <div>
                      <p className="font-semibold text-[var(--text)]">{grading.grade}</p>
                      <div className="flex items-center gap-1">
                        {[...Array(4)].map((_, i) => (
                          <div
                            key={i}
                            className="w-2 h-2 rounded-full"
                            style={{
                              backgroundColor: i < stripes ? beltColor : 'var(--border)',
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-[var(--muted)]">
                    {formatDate(grading.date_graded)}
                  </p>
                {grading.professor && (
                  <p className="text-sm text-[var(--muted)]">
                    Professor: {grading.professor}
                  </p>
                )}
                {grading.notes && (
                  <p className="text-sm text-[var(--muted)] mt-1 italic">
                    {grading.notes}
                  </p>
                )}
                {grading.photo_url && (
                  <div className="mt-2">
                    <img
                      src={grading.photo_url}
                      alt={`${grading.grade} certificate`}
                      className="rounded-lg border border-[var(--border)] max-w-xs cursor-pointer hover:opacity-90"
                      onClick={() => window.open(grading.photo_url, '_blank')}
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => onEditGrading(grading)}
                  className="text-[var(--accent)] hover:opacity-80"
                  title="Edit grading"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDeleteGrading(grading.id)}
                  className="text-[var(--error)] hover:opacity-80"
                  title="Delete grading"
                  aria-label="Delete grading"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
          })}
        </div>
      ) : (
        <p className="text-[var(--muted)] text-center py-6">
          No gradings recorded yet. Click "Add Grading" to track your belt progression.
        </p>
      )}
    </div>
  );
}
