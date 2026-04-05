import { Link } from 'react-router-dom';

/**
 * Landing — public marketing page for logged-out visitors.
 *
 * Positioning (2026-04-05):
 *   - Serious BJJ athletes (blue/purple belts learning their game)
 *   - Free forever for the core loop (log sessions + readiness + health)
 *   - Future paid tier for deep insights + Grapple AI coach
 *   - Early adopters grandfathered free until aggressive marketing begins
 *
 * This is the first real marketing surface for rivaflow.app. Before
 * today a cold visitor saw an empty SPA shell and got bounced to /login
 * with zero context. That was the #1 PM problem surfaced in the Designer
 * review — conversion ceiling was literally zero.
 */
export default function Landing() {
  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: 'var(--background)', color: 'var(--text)' }}
    >
      {/* ─── Top nav ──────────────────────────────────────── */}
      <header
        className="border-b"
        style={{ borderColor: 'var(--border)' }}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <img
              src="/logo.webp"
              alt="RivaFlow"
              className="w-9 h-9 rounded-lg"
            />
            <span
              className="text-xl font-black tracking-tight"
              style={{ color: 'var(--text)' }}
            >
              RIVAFLOW
            </span>
          </Link>
          <nav className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium px-4 py-2 rounded-lg transition-opacity hover:opacity-70"
              style={{ color: 'var(--text)' }}
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="text-sm font-semibold px-4 py-2 rounded-lg text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              Start free
            </Link>
          </nav>
        </div>
      </header>

      {/* ─── Hero ─────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 md:pt-24 md:pb-28">
        <div className="max-w-3xl">
          <div
            className="inline-block text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full mb-6"
            style={{
              backgroundColor: 'rgba(255, 77, 45, 0.12)',
              color: 'var(--accent)',
            }}
          >
            🥋 Free forever for athletes · Beta
          </div>
          <h1
            className="text-4xl md:text-6xl font-black leading-tight tracking-tight mb-6"
            style={{ color: 'var(--text)' }}
          >
            Training OS
            <br />
            <span style={{ color: 'var(--accent)' }}>for the Mat.</span>
          </h1>
          <p
            className="text-lg md:text-xl leading-relaxed mb-8 max-w-2xl"
            style={{ color: 'var(--muted)' }}
          >
            Log every session, track your readiness, find your game.
            Built by a purple-belt-in-progress for BJJ athletes who train
            like they mean it. Strava for the mat, with your own cornerman.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/register"
              className="inline-flex items-center justify-center px-6 py-3.5 rounded-xl text-white font-bold text-base transition-opacity hover:opacity-90"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              Start free — no card, no catch
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center px-6 py-3.5 rounded-xl font-bold text-base border-2 transition-opacity hover:opacity-70"
              style={{
                borderColor: 'var(--border)',
                color: 'var(--text)',
              }}
            >
              I already have an account
            </Link>
          </div>
          <p
            className="text-sm mt-4"
            style={{ color: 'var(--muted)' }}
          >
            All training logs + health stats are free forever.
          </p>
        </div>
      </section>

      {/* ─── What RivaFlow Does (4 value props) ─────────────── */}
      <section
        className="py-20"
        style={{ backgroundColor: 'var(--surfaceElev)' }}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2
              className="text-3xl md:text-4xl font-black mb-4"
              style={{ color: 'var(--text)' }}
            >
              Everything you need to train smarter
            </h2>
            <p
              className="text-base md:text-lg max-w-2xl mx-auto"
              style={{ color: 'var(--muted)' }}
            >
              The log, the coach, the library, the feedback loop — all
              designed for how BJJ actually works, not generic fitness.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Value prop 1 — Log every session */}
            <div
              className="p-6 rounded-2xl border"
              style={{
                backgroundColor: 'var(--background)',
                borderColor: 'var(--border)',
              }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-2xl"
                style={{ backgroundColor: 'rgba(255, 77, 45, 0.12)' }}
              >
                📝
              </div>
              <h3
                className="text-xl font-bold mb-2"
                style={{ color: 'var(--text)' }}
              >
                Log every session
              </h3>
              <p style={{ color: 'var(--muted)' }} className="text-sm leading-relaxed">
                Mat time, rolls, partners, submissions for + against,
                techniques drilled, intensity, notes. Quick log in 10
                seconds or detailed log with voice notes and roll-by-roll
                breakdowns.
              </p>
            </div>

            {/* Value prop 2 — Daily readiness */}
            <div
              className="p-6 rounded-2xl border"
              style={{
                backgroundColor: 'var(--background)',
                borderColor: 'var(--border)',
              }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-2xl"
                style={{ backgroundColor: 'rgba(59, 130, 246, 0.12)' }}
              >
                ⚡
              </div>
              <h3
                className="text-xl font-bold mb-2"
                style={{ color: 'var(--text)' }}
              >
                Daily readiness coach
              </h3>
              <p style={{ color: 'var(--muted)' }} className="text-sm leading-relaxed">
                Sleep, stress, soreness, energy — in 15 seconds each
                morning. Optional WHOOP integration auto-fills recovery
                data. Get a smart recommendation: gi, no-gi, drilling, or
                rest day.
              </p>
            </div>

            {/* Value prop 3 — Technique library */}
            <div
              className="p-6 rounded-2xl border"
              style={{
                backgroundColor: 'var(--background)',
                borderColor: 'var(--border)',
              }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-2xl"
                style={{ backgroundColor: 'rgba(16, 185, 129, 0.12)' }}
              >
                📚
              </div>
              <h3
                className="text-xl font-bold mb-2"
                style={{ color: 'var(--text)' }}
              >
                82-technique library
              </h3>
              <p style={{ color: 'var(--muted)' }} className="text-sm leading-relaxed">
                Submissions, sweeps, passes, takedowns, escapes — every
                technique categorised, searchable, and linked to the
                sessions where you actually drilled them. Build your
                personal game book as you train.
              </p>
            </div>

            {/* Value prop 4 — Progress */}
            <div
              className="p-6 rounded-2xl border"
              style={{
                backgroundColor: 'var(--background)',
                borderColor: 'var(--border)',
              }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-2xl"
                style={{ backgroundColor: 'rgba(251, 191, 36, 0.12)' }}
              >
                📈
              </div>
              <h3
                className="text-xl font-bold mb-2"
                style={{ color: 'var(--text)' }}
              >
                Progress that matters
              </h3>
              <p style={{ color: 'var(--muted)' }} className="text-sm leading-relaxed">
                Weekly mat time, submissions tally, technique frequency,
                belt progression, training load vs recovery. See the
                trends that tell the truth about your game — not vanity
                metrics.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Who it's for ─────────────────────────────────── */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2
            className="text-3xl md:text-4xl font-black mb-6"
            style={{ color: 'var(--text)' }}
          >
            Made for the athletes who take this seriously
          </h2>
          <p
            className="text-base md:text-lg leading-relaxed mb-4"
            style={{ color: 'var(--muted)' }}
          >
            White belts logging their first ever class. Blue belts building
            their game. Purple belts sharpening it. Brown and black belts
            protecting what they've built. If you show up, roll, and care
            about seeing the data behind your progress — RivaFlow is for
            you. Not for pros with full-time coaches managing teams, not
            for people who just want a step counter. For athletes who are
            serious about logging and data.
          </p>
          <p
            className="text-base md:text-lg leading-relaxed"
            style={{ color: 'var(--muted)' }}
          >
            Right now RivaFlow is <strong style={{ color: 'var(--text)' }}>free forever</strong> for
            all core features. No trial, no paywall, no card required.
            When we eventually ship a Pro tier with deep data insights
            and an AI coaching assistant, every early adopter from this
            beta will be grandfathered free.
          </p>
        </div>
      </section>

      {/* ─── Built by the community ─────────────────────────── */}
      <section
        className="py-16"
        style={{ backgroundColor: 'var(--surfaceElev)' }}
      >
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="text-4xl mb-4">🤙</div>
          <h2
            className="text-2xl md:text-3xl font-black mb-4"
            style={{ color: 'var(--text)' }}
          >
            Built in the open
          </h2>
          <p
            className="text-base leading-relaxed"
            style={{ color: 'var(--muted)' }}
          >
            RivaFlow is built by Ruby Wolff — a purple-belt-in-progress
            based in Sydney, Australia. I built this because nothing else
            out there captured how BJJ actually feels to train. If you
            find a bug, spot a missing feature, or just want to say hi,
            the feedback form is one tap away once you're in.
          </p>
        </div>
      </section>

      {/* ─── Final CTA ────────────────────────────────────── */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2
            className="text-3xl md:text-5xl font-black mb-6 leading-tight"
            style={{ color: 'var(--text)' }}
          >
            Log your first session in
            <br />
            <span style={{ color: 'var(--accent)' }}>under 60 seconds.</span>
          </h2>
          <p
            className="text-base md:text-lg mb-8"
            style={{ color: 'var(--muted)' }}
          >
            Free. No card. No catch. Your data, your progress, forever yours.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center justify-center px-8 py-4 rounded-xl text-white font-bold text-lg transition-opacity hover:opacity-90"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            Start free →
          </Link>
          <p className="text-xs mt-6" style={{ color: 'var(--muted)' }}>
            Already have an account?{' '}
            <Link
              to="/login"
              className="underline"
              style={{ color: 'var(--accent)' }}
            >
              Sign in
            </Link>
          </p>
        </div>
      </section>

      {/* ─── Footer ───────────────────────────────────────── */}
      <footer
        className="border-t py-10"
        style={{ borderColor: 'var(--border)' }}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <img
                src="/logo.webp"
                alt="RivaFlow"
                className="w-7 h-7 rounded-md"
              />
              <span
                className="text-sm font-bold tracking-tight"
                style={{ color: 'var(--text)' }}
              >
                RIVAFLOW
              </span>
            </div>
            <div
              className="flex items-center gap-6 text-sm"
              style={{ color: 'var(--muted)' }}
            >
              <Link to="/privacy" className="hover:opacity-70">
                Privacy
              </Link>
              <Link to="/terms" className="hover:opacity-70">
                Terms
              </Link>
              <Link to="/faq" className="hover:opacity-70">
                FAQ
              </Link>
              <Link to="/contact" className="hover:opacity-70">
                Contact
              </Link>
            </div>
            <div
              className="text-xs"
              style={{ color: 'var(--muted)' }}
            >
              © 2026 RivaFlow · Sydney, Australia
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
