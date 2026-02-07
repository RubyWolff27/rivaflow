import { Shield } from 'lucide-react';

export default function Privacy() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Shield className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Privacy &amp; Data Safety</h1>
      </div>

      <div className="rounded-xl p-6 space-y-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>Last updated: February 2026</p>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>1. Information We Collect</h2>
          <p className="text-sm leading-relaxed mb-2" style={{ color: 'var(--muted)' }}>We collect information you provide directly:</p>
          <ul className="text-sm leading-relaxed list-disc list-inside space-y-1" style={{ color: 'var(--muted)' }}>
            <li><strong>Account Information:</strong> Name, email address, password (hashed)</li>
            <li><strong>Profile Data:</strong> Belt rank, gym affiliation, training goals, profile photo</li>
            <li><strong>Training Data:</strong> Session logs, techniques, rolls, readiness check-ins, notes</li>
            <li><strong>Social Data:</strong> Friend connections, group memberships, feed interactions</li>
            <li><strong>Device Data:</strong> Browser type, operating system (for troubleshooting)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>2. How We Use Your Data</h2>
          <ul className="text-sm leading-relaxed list-disc list-inside space-y-1" style={{ color: 'var(--muted)' }}>
            <li>Provide and improve the RivaFlow service</li>
            <li>Generate your personal training analytics and insights</li>
            <li>Enable social features (friends, feed, groups)</li>
            <li>Send transactional emails (password reset, welcome)</li>
            <li>Diagnose and fix technical issues</li>
          </ul>
          <p className="text-sm leading-relaxed mt-2" style={{ color: 'var(--muted)' }}>
            We do <strong>not</strong> sell your data to third parties. We do <strong>not</strong> use your training data for advertising.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>3. Data Storage &amp; Security</h2>
          <ul className="text-sm leading-relaxed list-disc list-inside space-y-1" style={{ color: 'var(--muted)' }}>
            <li>Data is stored on secure servers with encryption at rest and in transit</li>
            <li>Passwords are hashed using industry-standard bcrypt</li>
            <li>Access to production data is restricted to authorised personnel only</li>
            <li>We use HTTPS for all data transmission</li>
            <li>Regular security audits and dependency updates</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>4. Data Sharing</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            Your training data is visible only to you unless you choose to share it via the social feed or with friends. We may share anonymised, aggregated statistics (e.g., "average sessions per week across all users") but never individual training data.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>5. Your Rights</h2>
          <p className="text-sm leading-relaxed mb-2" style={{ color: 'var(--muted)' }}>Under the Australian Privacy Act 1988 and applicable law, you have the right to:</p>
          <ul className="text-sm leading-relaxed list-disc list-inside space-y-1" style={{ color: 'var(--muted)' }}>
            <li><strong>Access</strong> your personal data at any time via the app</li>
            <li><strong>Correct</strong> inaccurate information via your Profile page</li>
            <li><strong>Delete</strong> your account and all associated data</li>
            <li><strong>Export</strong> your training data (available on Premium plans)</li>
            <li><strong>Withdraw</strong> consent for optional data processing</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>6. Cookies &amp; Analytics</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            RivaFlow uses essential cookies for authentication (JWT tokens stored in local storage). We may use privacy-friendly analytics to understand usage patterns. We do not use third-party tracking cookies or advertising pixels.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>7. Data Retention</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            We retain your data for as long as your account is active. If you delete your account, we will remove your personal data within 30 days, except where required by law to retain it. Anonymised analytics data may be retained indefinitely.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>8. Children&apos;s Privacy</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            RivaFlow is not intended for children under 16. We do not knowingly collect personal information from children. If you believe a child has provided us with personal data, please contact us to have it removed.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>9. Changes to This Policy</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            We may update this Privacy Policy from time to time. We will notify you of significant changes via email or in-app notification. Continued use of the Service after changes constitutes acceptance.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>10. Contact</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            For privacy enquiries, contact us at{' '}
            <a href="mailto:privacy@rivaflow.app" className="underline" style={{ color: 'var(--accent)' }}>privacy@rivaflow.app</a>
            {' '}or{' '}
            <a href="mailto:support@rivaflow.app" className="underline" style={{ color: 'var(--accent)' }}>support@rivaflow.app</a>.
          </p>
        </section>
      </div>
    </div>
  );
}
