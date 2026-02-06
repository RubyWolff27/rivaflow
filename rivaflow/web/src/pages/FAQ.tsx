import { useState } from 'react';
import { Link } from 'react-router-dom';
import { HelpCircle, Search, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react';

interface FAQItem { question: string; answer: string; }
interface FAQCategory { name: string; icon: string; items: FAQItem[]; }

const FAQ_DATA: FAQCategory[] = [
  { name: 'Getting Started', icon: '\u{1F680}', items: [
    { question: 'How do I set up my profile?', answer: 'Go to your Profile page to add your belt rank, gym, training goals, and personal details. Upload a profile photo and set your weekly training targets.' },
    { question: 'How do I log my first training session?', answer: 'Click Log in the navigation or use Quick Log. Fill in session type, duration, intensity, techniques and rolls.' },
    { question: 'How do I find and add friends?', answer: 'Go to Friends page and click Find Friends to search for other RivaFlow users and send friend requests.' },
    { question: 'What training types can I log?', answer: 'Gi BJJ, No-Gi BJJ, Strength and Conditioning, Mobility/Yoga, Wrestling, Judo, MMA, and Open Mat.' },
  ]},
  { name: 'Training Logging', icon: '\u{1F4DD}', items: [
    { question: 'How do I log BJJ rolls with details?', answer: 'Add detailed rolls with partner name, duration, submissions scored and conceded. Each roll tracked individually.' },
    { question: 'How do I track techniques?', answer: 'Add techniques from the glossary or create custom ones. The Techniques page shows most-practised and stale moves.' },
    { question: 'What are fight dynamics?', answer: 'Fight dynamics track your attacks and defences during sparring. Record attempts and successes for deeper insight into your game.' },
    { question: 'Can I log S&C and mobility sessions?', answer: 'Yes! Select the appropriate session type. Track exercises, sets, reps, and notes alongside BJJ training.' },
  ]},
  { name: 'Analytics', icon: '\u{1F4CA}', items: [
    { question: 'How do heatmaps and insights work?', answer: 'Reports show training heatmaps, breakdowns, submission ratios, and partner statistics. Updated as you log sessions.' },
    { question: 'What analytics are available for comp prep?', answer: 'Performance overviews, technique breakdowns, partner head-to-head stats, and consistency metrics with date filters.' },
    { question: 'How does readiness scoring work?', answer: 'Rate sleep, stress, soreness, and energy 1-5. RivaFlow calculates a composite score with training suggestions.' },
  ]},
  { name: 'Social', icon: '\u{1F465}', items: [
    { question: 'How do I share training with friends?', answer: 'Activity appears in the Feed for friends. They can like and comment on your sessions.' },
    { question: 'How do groups work?', answer: 'Connect with your training crew, comp team, or study group. Create, invite, and share your training journey.' },
    { question: 'Can I connect with my instructor?', answer: 'Add your instructor as a friend and tag them in sessions to track which coaches you train with most.' },
  ]},
  { name: 'Account', icon: '\u{2699}\u{FE0F}', items: [
    { question: 'How do I reset my password?', answer: 'Click Forgot Password on the login page. Check spam or contact support@rivaflow.app if no email arrives.' },
    { question: 'How do I update my profile?', answer: 'Go to Profile to update personal info, belt rank, gym, avatar, and training preferences.' },
    { question: 'What about my data privacy?', answer: 'Your training data is yours. Read our Privacy Policy for details on collection, storage, and protection.' },
  ]},
];

export default function FAQ() {
  const [searchQuery, setSearchQuery] = useState('');
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggleItem = (key: string) => {
    setOpenItems(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const filteredCategories = FAQ_DATA.map(category => ({
    ...category,
    items: category.items.filter(
      item =>
        !searchQuery ||
        item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.answer.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter(category => category.items.length > 0);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <HelpCircle className="w-7 h-7" style={{ color: 'var(--accent)' }} />
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Frequently Asked Questions</h1>
      </div>

      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--muted)' }} />
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search FAQs..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }}
        />
      </div>

      <div className="space-y-6">
        {filteredCategories.map(category => (
          <div key={category.name} className="rounded-xl overflow-hidden" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="px-5 py-3" style={{ borderBottom: '1px solid var(--border)' }}>
              <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'var(--text)' }}>
                <span>{category.icon}</span>{category.name}
              </h2>
            </div>
            <div>
              {category.items.map((item, idx) => {
                const key = `${category.name}-${idx}`;
                const isOpen = openItems.has(key);
                return (
                  <div key={key} style={idx < category.items.length - 1 ? { borderBottom: '1px solid var(--border)' } : {}}>
                    <button onClick={() => toggleItem(key)} className="w-full flex items-center justify-between px-5 py-3 text-left hover:opacity-80 transition-opacity">
                      <span className="text-sm font-medium pr-4" style={{ color: 'var(--text)' }}>{item.question}</span>
                      {isOpen ? <ChevronUp className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--muted)' }} /> : <ChevronDown className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--muted)' }} />}
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-4">
                        <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>{item.answer}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {filteredCategories.length === 0 && (
        <div className="text-center py-12">
          <p className="text-sm" style={{ color: 'var(--muted)' }}>No results found for &ldquo;{searchQuery}&rdquo;</p>
        </div>
      )}

      <div className="mt-8 rounded-xl p-6 text-center" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        <MessageSquare className="w-8 h-8 mx-auto mb-3" style={{ color: 'var(--accent)' }} />
        <h3 className="font-semibold mb-2" style={{ color: 'var(--text)' }}>Still have questions?</h3>
        <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>We are here to help. Reach out and we will get back to you as soon as possible.</p>
        <Link to="/contact" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium" style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}>
          Contact Support
        </Link>
      </div>
    </div>
  );
}
