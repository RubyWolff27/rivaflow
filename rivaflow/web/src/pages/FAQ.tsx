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
    { question: 'How do I connect my WHOOP device?', answer: 'Go to your Profile page and look for the WHOOP Integration section. Click Connect WHOOP and follow the authorization flow. Once connected, your recovery, sleep, and workout data will sync automatically.' },
    { question: 'Is there a Getting Started guide?', answer: 'Yes! When you first sign up, a Getting Started card appears on your Dashboard with step-by-step tasks: fill in your profile, log your first daily check-in, log your first session, and set weekly training goals. Complete each step to get the most out of RivaFlow.' },
  ]},
  { name: 'Training Logging', icon: '\u{1F4DD}', items: [
    { question: 'What does the intensity scale mean?', answer: 'Intensity is rated 1-5 and calibrated for BJJ: 1 Light \u2014 drilling, flow rolling, or active recovery. 2 Easy \u2014 technique-focused class with light sparring. 3 Moderate \u2014 standard class with normal rolling (the BJJ baseline). 4 Hard \u2014 tough rounds, competition-pace sparring (normal productive training). 5 War \u2014 comp simulation, shark tank, or max-effort rounds. An average of 3-4 means consistent, sustainable training \u2014 not over-training. Only sustained 5/5 across multiple sessions signals genuine overtraining risk.' },
    { question: 'How do I log BJJ rolls with details?', answer: 'Add detailed rolls with partner name, duration, submissions scored and conceded. Each roll tracked individually. Quick Log automatically creates rolls for each partner you add.' },
    { question: 'What is Quick Log vs Full Log vs Voice Log?', answer: 'Quick Log lets you capture the essentials fast \u2014 pick partners and it auto-creates rolls. Full Log gives you complete control with techniques, fight dynamics, notes, and speech-to-text input. Voice Log (in Grapple AI) lets you describe your session in natural language and the AI extracts structured data \u2014 date, type, duration, partners, techniques, and more \u2014 which you can review and edit before saving.' },
    { question: 'How do I track techniques?', answer: 'Add techniques from the unified glossary which covers positions, submissions, sweeps, escapes, and more. The Techniques page shows most-practised and stale moves.' },
    { question: 'What are fight dynamics?', answer: 'Fight dynamics track your attacks and defences during sparring. Record attempts and successes for deeper insight into your offensive and defensive game.' },
    { question: 'Can I log S&C and mobility sessions?', answer: 'Yes! Select the appropriate session type. Track exercises, sets, reps, and notes alongside BJJ training.' },
    { question: 'Can I use voice to log sessions?', answer: 'Yes! Full Log supports speech-to-text for the notes field. You can also use Voice Log in Grapple AI \u2014 describe your entire session naturally (or use the microphone) and Grapple will extract all the structured fields for you. Review and edit the extracted data before saving.' },
  ]},
  { name: 'Analytics & Insights', icon: '\u{1F4CA}', items: [
    { question: 'How do heatmaps and insights work?', answer: 'Reports show training heatmaps, breakdowns, submission ratios, and partner statistics. The training calendar displays a GitHub-style heatmap of your activity. Updated as you log sessions.' },
    { question: 'What analytics are available for comp prep?', answer: 'Performance overviews, technique breakdowns, partner head-to-head stats, gym comparison, class type effectiveness, time-of-day patterns, and consistency metrics with date filters.' },
    { question: 'How does readiness scoring work?', answer: 'Rate sleep, stress, soreness, and energy 1-5. RivaFlow calculates a composite score with training suggestions. The Insights tab also shows how your readiness correlates with performance.' },
    { question: 'What is the Insights tab?', answer: 'The Insights tab provides deep analytics: ACWR training load management, readiness-performance correlation, technique effectiveness quadrants, session quality scoring, overtraining risk assessment, and recovery analysis. It unlocks as you log more sessions.' },
    { question: 'What is ACWR?', answer: 'Acute:Chronic Workload Ratio compares your recent 7-day training load to your 28-day average. The sweet spot is 0.8-1.3. Below 0.8 is undertrained, above 1.5 is danger zone. This helps prevent injuries from sudden training spikes.' },
    { question: 'How does overtraining risk work?', answer: 'RivaFlow scores overtraining risk (0-100) based on four factors: ACWR spikes, readiness decline, injury hotspot mentions, and intensity creep. Green (<30), Yellow (30-60), and Red (>60) levels come with specific recommendations.' },
    { question: 'What are money moves?', answer: 'The technique effectiveness quadrant identifies your "money moves" \u2014 techniques you both train frequently and land successfully in rolls. It also highlights developing techniques, natural talent areas, and untested moves.' },
  ]},
  { name: 'Social', icon: '\u{1F465}', items: [
    { question: 'How do I share training with friends?', answer: 'Activity appears in the Feed for friends. They can like and comment on your sessions.' },
    { question: 'How do groups work?', answer: 'Connect with your training crew, comp team, or study group. Create, invite, and share your training journey.' },
    { question: 'Can I connect with my instructor?', answer: 'Add your instructor as a friend and tag them in sessions to track which coaches you train with most.' },
  ]},
  { name: 'Grapple AI Coach', icon: '\u{1F9E0}', items: [
    { question: 'What is Grapple?', answer: 'Grapple is your AI training coach. It answers BJJ questions, gives technique advice, and provides personalised insights based on your training data, readiness, and deep analytics.' },
    { question: 'What data does Grapple use?', answer: 'With your permission, Grapple analyses your sessions, readiness trends, ACWR training load, overtraining risk, technique effectiveness, session quality, and recovery patterns to give personalised advice.' },
    { question: 'Can Grapple help with game plans?', answer: 'Yes! Grapple can suggest techniques and strategies. You can also create structured Game Plans with position flows and drill sequences.' },
    { question: 'Does Grapple give post-session insights?', answer: 'Yes! After logging a session, Grapple generates a personalised insight that considers your training load, overtraining risk, and session quality alongside the session details.' },
    { question: 'How does the Grapple scheduler work?', answer: 'Grapple runs background jobs to help you stay on track. Weekly insights are generated every Sunday with a summary of your training patterns. Streak-at-risk notifications fire daily if your training streak is about to break. Onboarding drip emails go out over your first 5 days to help you get set up.' },
    { question: 'What are Game Plans?', answer: 'Game Plans are structured training blueprints you can create with Grapple. Define position flows (e.g., guard pull \u2192 sweep \u2192 pass \u2192 submission), add drill sequences, and track which plans you\'ve been working on. Great for competition prep or focused skill development.' },
    { question: 'Can I customise how Grapple coaches me?', answer: 'Yes! Go to Coach Settings (gear icon on the Grapple page) to configure your training mode (lifestyle, comp prep, skill development, recovery), coaching style (motivational, analytical, tough love, technical), focus areas, injuries, competition ruleset, and gi/no-gi preference. Grapple adapts all its advice based on these settings.' },
  ]},
  { name: 'WHOOP Integration', icon: '\u{231A}', items: [
    { question: 'What data does WHOOP sync?', answer: 'RivaFlow syncs your WHOOP recovery score, HRV, resting heart rate, SpO2, sleep performance, sleep duration, and workout data (including heart rate zones, strain, and calories). Data is cached and refreshed automatically.' },
    { question: 'What is auto-fill readiness?', answer: 'When enabled, your daily readiness check-in is pre-filled with sleep and energy scores derived from your WHOOP recovery data. You still rate stress and soreness manually. Toggle this in your Profile under WHOOP settings.' },
    { question: 'What is auto-create sessions?', answer: 'Auto-create sessions automatically logs BJJ workouts detected by WHOOP as training sessions in RivaFlow. The session includes duration, heart rate zones, strain, and calories. You can edit the session afterwards to add techniques, partners, and notes.' },
    { question: 'How do I reconnect WHOOP?', answer: 'If your WHOOP connection expires or stops syncing, go to Profile \u2192 WHOOP Integration and click Reconnect. You\'ll be taken through the WHOOP authorization flow again. Your historical data is preserved.' },
  ]},
  { name: 'Account', icon: '\u{2699}\u{FE0F}', items: [
    { question: 'How do I reset my password?', answer: 'Click Forgot Password on the login page. Check spam or contact support@rivaflow.app if no email arrives.' },
    { question: 'How do I update my profile?', answer: 'Go to Profile to update personal info, belt rank, gym, avatar, and training preferences.' },
    { question: 'What about my data privacy?', answer: 'Your training data is yours. Read our Privacy Policy for details on collection, storage, and protection.' },
    { question: 'How do notifications work?', answer: 'RivaFlow sends notifications for social activity (likes, comments, friend requests), training milestones (session counts, streak achievements), streak-at-risk warnings, and weekly AI insights. View them via the bell icon in the navigation. Email notifications are sent for important events like password resets and onboarding tips.' },
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
