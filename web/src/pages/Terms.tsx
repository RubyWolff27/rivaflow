import { FileText } from 'lucide-react';

export default function Terms() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <FileText className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Terms &amp; Conditions</h1>
      </div>

      <div className="rounded-xl p-6 space-y-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>Last updated: February 2026</p>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>1. Acceptance of Terms</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            By accessing or using RivaFlow ("the Service"), you agree to be bound by these Terms and Conditions. If you do not agree, please do not use the Service. RivaFlow is operated by RivaFlow Pty Ltd, an Australian company.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>2. Description of Service</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            RivaFlow is a training journal and analytics platform designed for Brazilian Jiu-Jitsu practitioners. The Service allows users to log training sessions, track techniques, monitor readiness, view analytics, and connect with training partners.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>3. User Accounts</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            You must provide accurate and complete information when creating an account. You are responsible for maintaining the confidentiality of your login credentials and for all activities under your account. You must be at least 16 years old to use the Service.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>4. Acceptable Use</h2>
          <p className="text-sm leading-relaxed mb-2" style={{ color: 'var(--muted)' }}>You agree not to:</p>
          <ul className="text-sm leading-relaxed list-disc list-inside space-y-1" style={{ color: 'var(--muted)' }}>
            <li>Use the Service for any unlawful purpose</li>
            <li>Harass, abuse, or threaten other users</li>
            <li>Upload malicious content or attempt to compromise the Service</li>
            <li>Create multiple accounts or impersonate others</li>
            <li>Scrape, crawl, or use automated tools to access the Service</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>5. Content Ownership</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            You retain ownership of all content you create on the Service, including training logs, notes, and photos. By posting content, you grant RivaFlow a non-exclusive, worldwide licence to use, display, and distribute your content within the Service for the purpose of providing the Service to you and other users.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>6. Service Availability</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            We strive to maintain high availability but do not guarantee uninterrupted access. The Service may be temporarily unavailable for maintenance, updates, or due to circumstances beyond our control. We reserve the right to modify or discontinue features with reasonable notice.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>7. Limitation of Liability</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            RivaFlow is provided "as is" without warranties of any kind. We are not liable for any injuries, losses, or damages arising from your use of the Service or reliance on training recommendations. Always consult a qualified instructor and medical professional before training.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>8. Termination</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            We may suspend or terminate your account if you violate these Terms. You may delete your account at any time by contacting support@rivaflow.app. Upon termination, your data will be deleted in accordance with our Privacy Policy.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>9. Governing Law</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            These Terms are governed by and construed in accordance with the laws of Australia. Any disputes arising from these Terms shall be subject to the exclusive jurisdiction of the courts of Australia.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>10. Contact</h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
            If you have any questions about these Terms, please contact us at{' '}
            <a href="mailto:support@rivaflow.app" className="underline" style={{ color: 'var(--accent)' }}>support@rivaflow.app</a>.
          </p>
        </section>
      </div>
    </div>
  );
}
