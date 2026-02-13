import { useState } from 'react';
import { Mail, Send } from 'lucide-react';
import AdminNav from '../components/AdminNav';
import { adminApi } from '../api/client';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';

export default function AdminEmail() {
  const toast = useToast();

  const [subject, setSubject] = useState('');
  const [htmlBody, setHtmlBody] = useState('');
  const [textBody, setTextBody] = useState('');
  const [sending, setSending] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleSend = async () => {
    setShowConfirm(false);
    setSending(true);
    try {
      const res = await adminApi.broadcastEmail({
        subject,
        html_body: htmlBody,
        text_body: textBody || undefined,
      });
      const data = res.data as { recipients: number; message: string };
      toast.success(`Email sent to ${data.recipients} users`);
      setSubject('');
      setHtmlBody('');
      setTextBody('');
    } catch (error: unknown) {
      const e = error as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const canSend = subject.trim() && htmlBody.trim();

  return (
    <div className="max-w-4xl mx-auto">
      <AdminNav />

      <div className="flex items-center gap-3 mb-6">
        <Mail className="w-6 h-6" style={{ color: 'var(--accent)' }} />
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Broadcast Email</h1>
      </div>

      <div className="space-y-4">
        {/* Subject */}
        <div>
          <label className="text-sm font-medium block mb-1" style={{ color: 'var(--text)' }}>Subject</label>
          <input
            type="text"
            value={subject}
            onChange={e => setSubject(e.target.value)}
            placeholder="Email subject line"
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
          />
        </div>

        {/* HTML Body */}
        <div>
          <label className="text-sm font-medium block mb-1" style={{ color: 'var(--text)' }}>HTML Body</label>
          <textarea
            value={htmlBody}
            onChange={e => setHtmlBody(e.target.value)}
            placeholder="HTML email content..."
            rows={12}
            className="w-full px-3 py-2 rounded-lg text-sm font-mono"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
          />
          <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
            Use {'{{first_name}}'} to personalise with the recipient's first name.
          </p>
        </div>

        {/* Text Body (optional) */}
        <div>
          <label className="text-sm font-medium block mb-1" style={{ color: 'var(--text)' }}>
            Plain Text Body <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
          </label>
          <textarea
            value={textBody}
            onChange={e => setTextBody(e.target.value)}
            placeholder="Plain text fallback..."
            rows={6}
            className="w-full px-3 py-2 rounded-lg text-sm font-mono"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
          />
        </div>

        {/* Send Button */}
        <button
          onClick={() => setShowConfirm(true)}
          disabled={!canSend || sending}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-opacity disabled:opacity-40"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          <Send className="w-4 h-4" />
          {sending ? 'Sending...' : 'Send Broadcast'}
        </button>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleSend}
        title="Send Broadcast Email"
        message="This will email all active users. Are you sure you want to continue?"
        confirmText="Send"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
