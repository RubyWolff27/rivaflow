import { usePageTitle } from '../hooks/usePageTitle';
import { useTier } from '../hooks/useTier';
import { useProfileData } from '../hooks/useProfileData';
import { CardSkeleton } from '../components/ui';
import ConfirmDialog from '../components/ConfirmDialog';
import PersonalInformationForm from '../components/profile/PersonalInformationForm';
import WeeklyGoalsForm from '../components/profile/WeeklyGoalsForm';
import ConnectedDevicesSection from '../components/profile/ConnectedDevicesSection';
import BeltProgressionCard from '../components/profile/BeltProgressionCard';
import ProfileHeader from '../components/profile/ProfileHeader';
import ProfileStats from '../components/profile/ProfileStats';
import ProfileSettings from '../components/profile/ProfileSettings';

export default function Profile() {
  usePageTitle('Profile');
  const tierInfo = useTier();
  const {
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
    setFormData,
    setGradingForm,
    setIsCustomGym,
    setGymVerificationPending,
    setGradingToDelete,
    setShowAddGrading,
    setShowDisconnectConfirm,
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
  } = useProfileData();

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
      <ProfileHeader tierInfo={tierInfo} />

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

      <WeeklyGoalsForm
        formData={formData}
        onChange={(data) => setFormData(prev => ({ ...prev, ...data }))}
        saving={saving}
        onSubmit={handleGoalsSubmit}
      />

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

      <ProfileSettings />

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

      <ProfileStats />

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
