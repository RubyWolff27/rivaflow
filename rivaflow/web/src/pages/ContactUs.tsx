import { useState } from 'react';
import { Mail, Send, MessageSquare } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';

const SUBJECT_OPTIONS = [
  { value: 'general', label: 'General Inquiry' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feature_request', label: 'Feature Request' },
  { value: 'account_issue', label: 'Account Issue' },
];

export default function ContactUs() {
  const toast = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: 'general',
    message: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim() || !formData.message.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }
    setSubmitting(true);
    // Simulated submit - backend will be wired later
    await new Promise(resolve => setTimeout(resolve, 800));
    toast.success('Thank you for your message! We will get back to you soon.');
    setFormData({ name: '', email: '', subject: 'general', message: '' });
    setSubmitting(false);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <MessageSquare className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Contact Us</h1>
      </div>

      <div
        className="rounded-xl p-6 mb-6"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <span style={{ color: 'var(--text)' }}>
            You can also reach us at{' '}
            <a
              href="mailto:support@rivaflow.app"
              className="font-medium underline"
              style={{ color: 'var(--accent)' }}
            >
              support@rivaflow.app
            </a>
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Name <span style={{ color: 'var(--accent)' }}>*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
              }}
              placeholder="Your name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Email <span style={{ color: 'var(--accent)' }}>*</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
              }}
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Subject
            </label>
            <select
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
              }}
            >
              {SUBJECT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Message <span style={{ color: 'var(--accent)' }}>*</span>
            </label>
            <textarea
              name="message"
              value={formData.message}
              onChange={handleChange}
              required
              rows={6}
              className="w-full px-3 py-2 rounded-lg text-sm resize-none"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
              }}
              placeholder="How can we help?"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-opacity disabled:opacity-50"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            <Send className="w-4 h-4" />
            {submitting ? 'Sending...' : 'Send Message'}
          </button>
        </form>
      </div>
    </div>
  );
}
