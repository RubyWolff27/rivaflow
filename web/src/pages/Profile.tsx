import { useState, useEffect } from 'react';
import { getLocalDateString } from '../utils/date';
import { usePageTitle } from '../hooks/usePageTitle';
import { profileApi, gradingsApi, friendsApi, adminApi, gymsApi, whoopApi, getErrorMessage } from '../api/client';
import { logger } from '../utils/logger';
import { validateImageFile } from '../utils/validation';
import type { Profile as ProfileType, Grading, Friend, WhoopConnectionStatus } from '../types';
import { User, Crown, Star, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { useTier } from '../hooks/useTier';
import { CardSkeleton } from '../components/ui';
import PersonalInformationForm from '../components/profile/PersonalInformationForm';
import WeeklyGoalsForm from '../components/profile/WeeklyGoalsForm';
import ConnectedDevicesSection from '../components/profile/ConnectedDevicesSection';
import BeltProgressionCard from '../components/profile/BeltProgressionCard';


function mapProfileToFormData(data?: ProfileType | null) {
  return {
    first_name: data?.first_name ?? '',
    last_name: data?.last_name ?? '',
    date_of_birth: data?.date_of_birth ?? '',
    sex: data?.sex ?? '',
    city: data?.city ?? '',
    state: data?.state ?? '',
    default_gym: data?.default_gym ?? '',
    default_location: data?.default_location ?? '',
    current_professor: data?.current_professor ?? '',
    current_instructor_id: data?.current_instructor_id ?? null as number | null,
    primary_training_type: data?.primary_training_type ?? 'gi',
    height_cm: data?.height_cm?.toString() ?? '',
    target_weight_kg: data?.target_weight_kg?.toString() ?? '',
    target_weight_date: data?.target_weight_date ?? '',
    weekly_sessions_target: data?.weekly_sessions_target ?? 3,
    weekly_hours_target: data?.weekly_hours_target ?? 4.5,
    weekly_rolls_target: data?.weekly_rolls_target ?? 15,
    weekly_bjj_sessions_target: data?.weekly_bjj_sessions_target ?? 3,
    weekly_sc_sessions_target: data?.weekly_sc_sessions_target ?? 1,
    weekly_mobility_sessions_target: data?.weekly_mobility_sessions_target ?? 0,
    show_streak_on_dashboard: data?.show_streak_on_dashboard ?? true,
    show_weekly_goals: data?.show_weekly_goals ?? true,
    activity_visibility: (data?.activity_visibility ?? 'friends') as 'friends' | 'private',
    avatar_url: data?.avatar_url ?? '',
    timezone: data?.timezone ?? '',
    primary_gym_id: data?.primary_gym_id ?? null as number | null,
  };
}

export default function Profile() {
  usePageTitle('Profile');
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [gradings, setGradings] = useState<Grading[]>([]);
  const [instructors, setInstructors] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showAddGrading, setShowAddGrading] = useState(false);
  const [editingGrading, setEditingGrading] = useState<Grading | null>(null);
  const [isCustomGym, setIsCustomGym] = useState(false);
  const [gymVerificationPending, setGymVerificationPending] = useState(false);
  const [gradingToDelete, setGradingToDelete] = useState<number | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const toast = useToast();
  const tierInfo = useTier();

  const [formData, setFormData] = useState(mapProfileToFormData());

  const [gradingForm, setGradingForm] = useState({
    grade: '',
    date_graded: getLocalDateString(),
    professor: '',
    instructor_id: null as number | null,
    notes: '',
    photo_url: '',
  });
  const [uploadingGradingPhoto, setUploadingGradingPhoto] = useState(false);
  const [gradingPhotoPreview, setGradingPhotoPreview] = useState<string | null>(null);
  const [gymHeadCoach, setGymHeadCoach] = useState<string | null>(null);

  // WHOOP integration state
  const [whoopStatus, setWhoopStatus] = useState<WhoopConnectionStatus | null>(null);
  const [whoopLoading, setWhoopLoading] = useState(false);
  const [whoopSyncing, setWhoopSyncing] = useState(false);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [whoopNeedsReauth, setWhoopNeedsReauth] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      await loadData();
      if (cancelled) return;
      // Load WHOOP status (best-effort, don't fail the page)
      try {
        const whoopRes = await whoopApi.getStatus();
        if (cancelled) return;
        setWhoopStatus(whoopRes.data);
        if (whoopRes.data?.connected) {
          try {
            const scopeRes = await whoopApi.checkScopes();
            if (!cancelled && scopeRes.data?.needs_reauth) {
              setWhoopNeedsReauth(true);
            }
          } catch {
            // Scope check not available — that's fine
          }
        }
      } catch {
        // Feature flag off or not available — that's fine
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  // Fetch gym head coach when gym is selected
  useEffect(() => {
    const controller = new AbortController();
    const fetchGymHeadCoach = async () => {
      if (!formData.default_gym) {
        if (!controller.signal.aborted) setGymHeadCoach(null);
        return;
      }

      try {
        const response = await gymsApi.search(formData.default_gym, false);
        if (controller.signal.aborted) return;
        const data = response.data;

        if (data && data.length > 0) {
          const gym = data.find((g: { name: string; head_coach?: string }) => g.name === formData.default_gym);
          if (gym && gym.head_coach) {
            setGymHeadCoach(gym.head_coach);
          } else {
            setGymHeadCoach(null);
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          logger.error('Error fetching gym details:', error);
          setGymHeadCoach(null);
        }
      }
    };

    fetchGymHeadCoach();
    return () => { controller.abort(); };
  }, [formData.default_gym]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileRes, gradingsRes, instructorsRes] = await Promise.all([
        profileApi.get(),
        gradingsApi.list(),
        friendsApi.listInstructors(),
      ]);
      setProfile(profileRes.data ?? null);
      setGradings(gradingsRes.data ?? []);
      setInstructors(instructorsRes.data ?? []);
      setFormData(mapProfileToFormData(profileRes.data));
    } catch (error) {
      logger.error('Error loading data:', error);
      toast.error('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const refreshProfile = async () => {
    try {
      const profileRes = await profileApi.get();
      setProfile(profileRes.data ?? null);
      setFormData(mapProfileToFormData(profileRes.data));
    } catch (error) {
      logger.error('Error refreshing profile:', error);
      toast.error('Failed to refresh profile');
    }
  };

  const refreshGradings = async () => {
    try {
      const gradingsRes = await gradingsApi.list();
      setGradings(gradingsRes.data ?? []);
    } catch (error) {
      logger.error('Error refreshing gradings:', error);
      toast.error('Failed to refresh gradings');
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validationError = validateImageFile(file);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Upload file
    setUploadingPhoto(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await profileApi.uploadPhoto(formData);

      // Update local state with new avatar URL
      setFormData(prev => ({ ...prev, avatar_url: response.data.avatar_url }));

      toast.success('Profile photo uploaded successfully!');
      await refreshProfile();
    } catch (error: unknown) {
      logger.error('Error uploading photo:', error);
      toast.error(getErrorMessage(error));
      setPhotoPreview(null);
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleDeletePhoto = async () => {
    try {
      await profileApi.deletePhoto();
      setFormData(prev => ({ ...prev, avatar_url: '' }));
      setPhotoPreview(null);
      toast.success('Profile photo deleted successfully!');
      await refreshProfile();
    } catch (error: unknown) {
      logger.error('Error deleting photo:', error);
      toast.error(getErrorMessage(error));
    }
  };

  const handleGradingPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validationError = validateImageFile(file);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = () => {
      setGradingPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Upload file
    setUploadingGradingPhoto(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await gradingsApi.uploadPhoto(formData);

      // Update grading form with new photo URL
      setGradingForm(prev => ({ ...prev, photo_url: response.data.photo_url }));

      toast.success('Photo uploaded successfully!');
    } catch (error: unknown) {
      logger.error('Error uploading grading photo:', error);
      toast.error(getErrorMessage(error));
      setGradingPhotoPreview(null);
    } finally {
      setUploadingGradingPhoto(false);
    }
  };

  const handleDeleteGradingPhoto = () => {
    setGradingForm(prev => ({ ...prev, photo_url: '' }));
    setGradingPhotoPreview(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      await profileApi.update({
        first_name: formData.first_name || undefined,
        last_name: formData.last_name || undefined,
        date_of_birth: formData.date_of_birth || undefined,
        sex: (formData.sex || undefined) as 'male' | 'female' | 'other' | 'prefer_not_to_say' | undefined,
        city: formData.city || undefined,
        state: formData.state || undefined,
        default_gym: formData.default_gym || undefined,
        default_location: formData.default_location || undefined,
        current_professor: formData.current_professor || undefined,
        current_instructor_id: formData.current_instructor_id || undefined,
        primary_training_type: formData.primary_training_type || undefined,
        height_cm: formData.height_cm ? parseInt(formData.height_cm) : undefined,
        target_weight_kg: formData.target_weight_kg ? parseFloat(formData.target_weight_kg) : undefined,
        target_weight_date: formData.target_weight_date || undefined,
        avatar_url: formData.avatar_url || undefined,
        timezone: formData.timezone || undefined,
        primary_gym_id: formData.primary_gym_id || undefined,
      });
      setSuccess(true);
      await loadData();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      logger.error('Error updating profile:', error);
      toast.error('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleGoalsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      // Auto-calculate total sessions as sum of activity-specific goals
      const totalSessions = formData.weekly_bjj_sessions_target +
                          formData.weekly_sc_sessions_target +
                          formData.weekly_mobility_sessions_target;

      await profileApi.update({
        weekly_sessions_target: totalSessions,
        weekly_hours_target: formData.weekly_hours_target,
        weekly_rolls_target: formData.weekly_rolls_target,
        weekly_bjj_sessions_target: formData.weekly_bjj_sessions_target,
        weekly_sc_sessions_target: formData.weekly_sc_sessions_target,
        weekly_mobility_sessions_target: formData.weekly_mobility_sessions_target,
        show_streak_on_dashboard: formData.show_streak_on_dashboard,
        show_weekly_goals: formData.show_weekly_goals,
        activity_visibility: formData.activity_visibility,
      });
      setSuccess(true);
      await loadData();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      logger.error('Error updating goals:', error);
      toast.error('Failed to update goals. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleOpenAddGrading = () => {
    setGradingForm({
      grade: '',
      date_graded: getLocalDateString(),
      professor: profile?.current_professor ?? '',
      instructor_id: profile?.current_instructor_id ?? null,
      notes: '',
      photo_url: '',
    });
    setGradingPhotoPreview(null);
    setShowAddGrading(true);
    setEditingGrading(null);
  };

  const handleAddGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gradingForm.grade || !gradingForm.date_graded) {
      toast.error('Please select a grade and date.');
      return;
    }

    try {
      await gradingsApi.create({
        grade: gradingForm.grade,
        date_graded: gradingForm.date_graded,
        professor: gradingForm.professor || undefined,
        instructor_id: gradingForm.instructor_id || undefined,
        notes: gradingForm.notes || undefined,
        photo_url: gradingForm.photo_url || undefined,
      });
      setGradingForm({
        grade: '',
        date_graded: getLocalDateString(),
        professor: '',
        instructor_id: null,
        notes: '',
        photo_url: '',
      });
      setGradingPhotoPreview(null);
      setShowAddGrading(false);
      await refreshGradings();
      toast.success('Grading added successfully');
    } catch (error) {
      logger.error('Error adding grading:', error);
      toast.error('Failed to add grading. Please try again.');
    }
  };

  const handleEditGrading = (grading: Grading) => {
    setEditingGrading(grading);
    setGradingForm({
      grade: grading.grade ?? '',
      date_graded: grading.date_graded ?? getLocalDateString(),
      professor: grading.professor ?? '',
      instructor_id: grading.instructor_id ?? null,
      notes: grading.notes ?? '',
      photo_url: grading.photo_url ?? '',
    });
    setGradingPhotoPreview(grading.photo_url ?? null);
    setShowAddGrading(false);
  };

  const handleUpdateGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGrading) return;

    if (!gradingForm.grade || !gradingForm.date_graded) {
      toast.error('Please select a grade and date.');
      return;
    }

    try {
      await gradingsApi.update(editingGrading.id, {
        grade: gradingForm.grade,
        date_graded: gradingForm.date_graded,
        professor: gradingForm.professor || undefined,
        instructor_id: gradingForm.instructor_id || undefined,
        notes: gradingForm.notes || undefined,
        photo_url: gradingForm.photo_url || undefined,
      });
      setGradingForm({
        grade: '',
        date_graded: getLocalDateString(),
        professor: '',
        instructor_id: null,
        notes: '',
        photo_url: '',
      });
      setGradingPhotoPreview(null);
      setEditingGrading(null);
      await refreshGradings();
      toast.success('Grading updated successfully');
    } catch (error) {
      logger.error('Error updating grading:', error);
      toast.error('Failed to update grading. Please try again.');
    }
  };

  const handleCancelEdit = () => {
    setEditingGrading(null);
    setGradingForm({
      grade: '',
      date_graded: getLocalDateString(),
      professor: '',
      instructor_id: null,
      notes: '',
      photo_url: '',
    });
    setGradingPhotoPreview(null);
  };

  const handleDeleteGrading = async () => {
    if (!gradingToDelete) return;

    try {
      await gradingsApi.delete(gradingToDelete);
      await refreshGradings();
      toast.success('Grading deleted successfully');
    } catch (error) {
      logger.error('Error deleting grading:', error);
      toast.error('Failed to delete grading.');
    } finally {
      setGradingToDelete(null);
    }
  };

  // Handle WHOOP OAuth redirect params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const whoopParam = params.get('whoop');
    if (whoopParam === 'connected') {
      toast.success('WHOOP connected successfully!');
      // Refresh status
      whoopApi.getStatus().then(r => setWhoopStatus(r.data)).catch(() => {});
      // Clean URL
      window.history.replaceState({}, '', '/profile');
    } else if (whoopParam === 'error') {
      const reason = params.get('reason') || 'unknown';
      toast.error(`WHOOP connection failed: ${reason}`);
      window.history.replaceState({}, '', '/profile');
    }
  }, []);

  const handleWhoopConnect = async () => {
    setWhoopLoading(true);
    try {
      const res = await whoopApi.getAuthorizeUrl();
      window.open(res.data.authorization_url, '_blank');
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setWhoopLoading(false);
    }
  };

  const handleWhoopSync = async () => {
    setWhoopSyncing(true);
    try {
      const res = await whoopApi.sync();
      const { total_fetched, auto_sessions_created } = res.data;
      const msg = auto_sessions_created
        ? `Synced ${total_fetched} workouts — ${auto_sessions_created} session(s) auto-created`
        : `Synced ${total_fetched} workouts from WHOOP`;
      toast.success(msg);
      const statusRes = await whoopApi.getStatus();
      setWhoopStatus(statusRes.data);
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setWhoopSyncing(false);
    }
  };

  const handleWhoopDisconnect = async () => {
    try {
      await whoopApi.disconnect();
      setWhoopStatus({ connected: false });
      toast.success('WHOOP disconnected');
    } catch (error: unknown) {
      toast.error(getErrorMessage(error));
    } finally {
      setShowDisconnectConfirm(false);
    }
  };

  const handleSetAutoCreate = async (value: boolean) => {
    if (!whoopStatus) return;
    try {
      await whoopApi.setAutoCreate(value);
      setWhoopStatus({ ...whoopStatus, auto_create_sessions: value });
      toast.success(value ? 'Auto-create enabled' : 'Auto-create disabled');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleSetAutoFillReadiness = async (value: boolean) => {
    if (!whoopStatus) return;
    try {
      await whoopApi.setAutoFillReadiness(value);
      setWhoopStatus({ ...whoopStatus, auto_fill_readiness: value });
      toast.success(value ? 'Auto-fill enabled' : 'Auto-fill disabled');
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleCreateGym = async (gymName: string) => {
    try {
      // Submit custom gym for verification
      await adminApi.createGym({
        name: gymName,
        country: formData.state === 'NSW' || formData.state === 'VIC' || formData.state === 'QLD'
          ? 'Australia'
          : 'Unknown',
        city: formData.city || undefined,
        state: formData.state || undefined,
        verified: false, // Pending verification
      });
      setGymVerificationPending(true);
      setTimeout(() => setGymVerificationPending(false), 5000);
    } catch (error) {
      logger.error('Error submitting gym:', error);
      toast.error('Failed to submit gym');
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={3} />
        <CardSkeleton lines={5} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <User className="w-8 h-8 text-[var(--accent)]" />
        <h1 className="text-3xl font-bold">Profile</h1>
      </div>

      {/* Subscription Tier */}
      <div className="card bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {tierInfo.isPremium ? (
              <Crown className="w-6 h-6 text-[var(--accent)]" />
            ) : (
              <Star className="w-6 h-6 text-[var(--muted)]" />
            )}
            <div>
              <h2 className="text-lg font-semibold">Subscription Tier</h2>
              <p className="text-2xl font-bold text-[var(--accent)]">{tierInfo.displayName}</p>
              {tierInfo.isBeta && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 mt-1">
                  Beta User
                </span>
              )}
            </div>
          </div>
          {!tierInfo.isPremium && (
            <button className="btn-primary">
              Upgrade
            </button>
          )}
        </div>
        <div className="mt-3 text-sm text-[var(--muted)]">
          {tierInfo.isPremium ? (
            <p>You have access to all premium features. Thank you for your support!</p>
          ) : (
            <p>Upgrade to premium to unlock advanced analytics, unlimited sessions, and more.</p>
          )}
        </div>
      </div>

      {/* Profile Form */}
      <PersonalInformationForm
        formData={formData}
        onChange={(data) => setFormData(prev => ({ ...prev, ...data }))}
        profile={profile}
        instructors={instructors}
        saving={saving}
        success={success}
        onSubmit={handleSubmit}
        photoPreview={photoPreview}
        uploadingPhoto={uploadingPhoto}
        onPhotoUpload={handlePhotoUpload}
        onDeletePhoto={handleDeletePhoto}
        isCustomGym={isCustomGym}
        onCustomGymChange={setIsCustomGym}
        gymVerificationPending={gymVerificationPending}
        onGymVerificationPending={setGymVerificationPending}
        gymHeadCoach={gymHeadCoach}
        onCreateGym={handleCreateGym}
        onGymSelected={(gym) => {
          setFormData(prev => ({ ...prev, primary_gym_id: gym.id }));
        }}
      />

      {/* Weekly Goals Section */}
      <WeeklyGoalsForm
        formData={formData}
        onChange={(data) => setFormData(prev => ({ ...prev, ...data }))}
        saving={saving}
        onSubmit={handleGoalsSubmit}
      />

      {/* Connected Devices */}
      {whoopStatus !== null && (
        <ConnectedDevicesSection
          whoopStatus={whoopStatus}
          whoopLoading={whoopLoading}
          whoopSyncing={whoopSyncing}
          whoopNeedsReauth={whoopNeedsReauth}
          onConnect={handleWhoopConnect}
          onSync={handleWhoopSync}
          onSetAutoCreate={handleSetAutoCreate}
          onSetAutoFillReadiness={handleSetAutoFillReadiness}
          showDisconnectConfirm={showDisconnectConfirm}
          onShowDisconnectConfirm={setShowDisconnectConfirm}
          onDisconnect={handleWhoopDisconnect}
        />
      )}

      {/* Coach Settings Link */}
      <Link to="/coach-settings" className="card block hover:border-[var(--accent)] transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-[var(--accent)]" />
            <div>
              <h2 className="text-lg font-semibold">Grapple AI Coach Settings</h2>
              <p className="text-sm text-[var(--muted)]">
                Personalize how Grapple coaches you — training mode, style, injuries, and more
              </p>
            </div>
          </div>
          <span className="text-[var(--muted)]">&rarr;</span>
        </div>
      </Link>

      {/* Belt Progression Section */}
      <BeltProgressionCard
        profile={profile}
        gradings={gradings}
        instructors={instructors}
        gradingForm={gradingForm}
        onGradingFormChange={setGradingForm}
        showAddGrading={showAddGrading}
        editingGrading={editingGrading}
        onOpenAddGrading={handleOpenAddGrading}
        onAddGrading={handleAddGrading}
        onEditGrading={handleEditGrading}
        onUpdateGrading={handleUpdateGrading}
        onCancelEdit={handleCancelEdit}
        onDeleteGrading={(id) => setGradingToDelete(id)}
        onCloseAddGrading={() => setShowAddGrading(false)}
        gradingPhotoPreview={gradingPhotoPreview}
        uploadingGradingPhoto={uploadingGradingPhoto}
        onGradingPhotoUpload={handleGradingPhotoUpload}
        onDeleteGradingPhoto={handleDeleteGradingPhoto}
      />

      {/* Info Card */}
      <div className="card" style={{ borderColor: 'var(--accent)' }}>
        <h3 className="font-semibold mb-2">About Your Profile</h3>
        <ul className="text-sm text-[var(--muted)] space-y-1">
          <li>• Your profile data is stored securely on our servers</li>
          <li>• Default gym will pre-fill session logging forms</li>
          <li>• Belt progression tracks your BJJ journey over time</li>
          <li>• All fields are optional</li>
        </ul>
      </div>

      <ConfirmDialog
        isOpen={gradingToDelete !== null}
        onClose={() => setGradingToDelete(null)}
        onConfirm={handleDeleteGrading}
        title="Delete Grading"
        message="Are you sure you want to delete this grading? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      <ConfirmDialog
        isOpen={showDisconnectConfirm}
        onClose={() => setShowDisconnectConfirm(false)}
        onConfirm={handleWhoopDisconnect}
        title="Disconnect WHOOP"
        message="This will remove your WHOOP connection and clear all synced workout data from your sessions. You can reconnect at any time."
        confirmText="Disconnect"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
