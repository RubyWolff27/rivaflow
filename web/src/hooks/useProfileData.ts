import { useState, useEffect } from 'react';
import { getLocalDateString } from '../utils/date';
import { profileApi, gradingsApi, friendsApi, adminApi, gymsApi, whoopApi, getErrorMessage } from '../api/client';
import { logger } from '../utils/logger';
import { validateImageFile } from '../utils/validation';
import { compressImage } from '../utils/imageCompression';
import { formatCount } from '../utils/text';
import type { Profile, Grading, Friend, WhoopConnectionStatus } from '../types';
import { useToast } from '../contexts/ToastContext';

function mapProfileToFormData(data?: Profile | null) {
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

export type ProfileFormData = ReturnType<typeof mapProfileToFormData>;

export interface GradingFormData {
  grade: string;
  date_graded: string;
  professor: string;
  instructor_id: number | null;
  notes: string;
  photo_url: string;
}

export function useProfileData() {
  const [profile, setProfile] = useState<Profile | null>(null);
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

  const [formData, setFormData] = useState(mapProfileToFormData());

  const [gradingForm, setGradingForm] = useState<GradingFormData>({
    grade: '',
    date_graded: getLocalDateString(),
    professor: '',
    instructor_id: null,
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
          } catch (err) {
            logger.debug('Scope check not available', err);
          }
        }
      } catch (err) {
        logger.debug('WHOOP feature flag off or not available', err);
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

    // Compress and upload file
    setUploadingPhoto(true);
    try {
      const compressed = await compressImage(file, { maxWidth: 512, maxHeight: 512 });
      const fd = new FormData();
      fd.append('file', compressed);

      const response = await profileApi.uploadPhoto(fd);

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

    // Compress and upload file
    setUploadingGradingPhoto(true);
    try {
      const compressed = await compressImage(file);
      const fd = new FormData();
      fd.append('file', compressed);

      const response = await gradingsApi.uploadPhoto(fd);

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
      whoopApi.getStatus().then(r => setWhoopStatus(r.data)).catch(err => logger.debug('WHOOP status refresh failed', err));
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
        ? `Synced ${formatCount(total_fetched, 'workout')} — ${formatCount(auto_sessions_created, 'session')} auto-created`
        : `Synced ${formatCount(total_fetched, 'workout')} from WHOOP`;
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

  return {
    // State
    profile,
    gradings,
    instructors,
    loading,
    saving,
    success,
    showAddGrading,
    editingGrading,
    isCustomGym,
    gymVerificationPending,
    gradingToDelete,
    uploadingPhoto,
    photoPreview,
    formData,
    gradingForm,
    uploadingGradingPhoto,
    gradingPhotoPreview,
    gymHeadCoach,
    whoopStatus,
    whoopLoading,
    whoopSyncing,
    showDisconnectConfirm,
    whoopNeedsReauth,

    // Setters
    setFormData,
    setGradingForm,
    setIsCustomGym,
    setGymVerificationPending,
    setGradingToDelete,
    setShowAddGrading,
    setShowDisconnectConfirm,

    // Handlers
    handlePhotoUpload,
    handleDeletePhoto,
    handleGradingPhotoUpload,
    handleDeleteGradingPhoto,
    handleSubmit,
    handleGoalsSubmit,
    handleOpenAddGrading,
    handleAddGrading,
    handleEditGrading,
    handleUpdateGrading,
    handleCancelEdit,
    handleDeleteGrading,
    handleWhoopConnect,
    handleWhoopSync,
    handleWhoopDisconnect,
    handleSetAutoCreate,
    handleSetAutoFillReadiness,
    handleCreateGym,
  };
}
