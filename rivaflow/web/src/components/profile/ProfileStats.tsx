export default function ProfileStats() {
  return (
    <div className="card" style={{ borderColor: 'var(--accent)' }}>
      <h3 className="font-semibold mb-2">About Your Profile</h3>
      <ul className="text-sm text-[var(--muted)] space-y-1">
        <li>• Your profile data is stored securely on our servers</li>
        <li>• Default gym will pre-fill session logging forms</li>
        <li>• Belt progression tracks your BJJ journey over time</li>
        <li>• All fields are optional</li>
      </ul>
    </div>
  );
}
