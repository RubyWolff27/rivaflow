# WHOOP-Alternative — Future-State Plan · 2026-07-04

Research-backed roadmap to turn our HR + RR data into a **best-in-class insight + prevention** tracker —
"not just stats, but great insights into my body and prevention." Built by a Council (sports scientist,
HRV/autonomic researcher, cardio-data-scientist, product lead) from the brand research, then stress-tested
by a Red Team. Cross-check sources in `WHOOP_RESEARCH_REFERENCES.md`; current build in `WHOOP_CURRENT_STATE.md`.

**Design constraints:** phone stays **slim** (fetch + display); rich graphs live in a **web deep-dive**; all
compute stays **server-side** (2-min GitOps iteration); everything scored vs Ruby's **own rolling baseline**,
never population norms; **Sabbath-aware** (wellness nudges silent Sunday — but illness/safety flags always fire).
**Profile lens:** 44yo, BJJ blue→purple + CrossFit, high-strength/low-endurance DNA, NSAID-sensitive, >9 h sleep-need.

## Strategic pillars
1. **Recovery Intelligence** — one honest HRV-led "push vs rest" call vs his baseline (WHOOP Recovery / Oura Readiness / Fitbit Daily Readiness core — fully reproducible from HR+RR).
2. **Training Load & Injury Prevention** — strain target, acute:chronic load ratio, per-session recovery cost, tuned for a masters grappler so load never outruns recovery.
3. **Illness & Autonomic Early-Warning** (the prevention centrepiece) — multi-signal deviation-from-baseline + nocturnal screening; matters more given NSAID-sensitivity (early rest beats late medication).
4. **Sleep & Recovery Debt** — honours the >9 h DNA sleep-need with need/debt accrual + HR-based quality.
5. **Longevity & Trend Intelligence** — cardiovascular-age proxy, resilience/cumulative-stress, frequency & non-linear HRV, weekly/monthly assessments (web deep-dive).
6. **Honest n-of-1 Science** — personal baselines, frequency-domain + Poincaré HRV unlocked, behaviour-correlation engine, faith-first surfacing.

## 🛡️ The Prevention Engine (centrepiece)
A personal-baseline **anomaly engine** — the common denominator across WHOOP Health Monitor, Oura Symptom
Radar, Apple Vitals, Fitbit Health Metrics — rebuilt from the two signals we own end-to-end: continuous HR
and the full RR tachogram.
- **Signals:** (1) resting-HR elevation, (2) RMSSD / HF-power suppression, (3) RR-derived respiratory-rate rise, (4) nocturnal sleeping-HR elevation + blunted overnight dip, (5) RR-irregularity burst (AFib-class — see caution).
- **Baselines:** each signal gets its own rolling **14–21 day personal mean ± SD** (n-of-1); wear-gap days excluded by the coverage guard so a charging night can't poison the baseline.
- **Logic:** per-signal daily z-score + a **CUSUM** accumulator for slow multi-day drifts; the alert fires on **co-occurrence** (Apple Vitals' "multiple outliers together" rule) — one flagged vital is noise, resp-rate + RHR + HRV deviating *together* is signal. **Respiratory rate weighted heaviest** — it's WHOOP's documented ~1–2-day pre-symptom infection lead and the strongest early-warning we can reproduce (temp/SpO₂ are locked).
- **Tiers:** 🟢 in-range · 🟡 "watch — your body's working harder, consider easing today" · 🔴 "strong multi-signal deviation — rest and recover." Overtraining = the same engine + load context (suppressed HRV + elevated RHR + ACWR spike → load-cap).
- **Honest boundary:** detects *deviation* and prompts caution/rest/clinician-review — **never diagnoses**; without temp/SpO₂ it will miss purely thermal or oxygenation events. R22 decode is the future unlock that would add temperature and close the gap to Oura/Apple.

## Roadmap (18 builds, prioritised)
Feasibility: `now` · `time-baseline` (needs days of data) · `more-data` · `research` (experimental). Surface: slim-app / web / both.

### P0 — ship first (the honest, reproducible core)
| Build | Feasibility | Surface | Value / method |
|---|---|---|---|
| **Personalised Max-HR calibration** | now | both | Kills the hardcoded 190 that distorts every zone/strain/stress. Rolling 99.5th-pct observed session-max + HR-reserve, Tanaka sanity band. *Enabler for everything.* |
| **Multi-input Readiness upgrade** | now | both | Fuse RMSSD (led) + RHR trend + resp-rate + sleep (down-weighted) → robust morning verdict (WHOOP Recovery + Fitbit Daily Readiness model). **Red-team's strongest bet.** |
| **Capture-coverage / wear-time guard** | now | both | Excludes off-strap days from baselines so alerts + readiness stay trustworthy. **Promote to P0 (red-team).** |
| **Frequency-domain + non-linear HRV** | now | web | LF/HF/total-power (Lomb-Scargle) + Poincaré SD1/SD2 — autonomic *balance*, the richest unlocked signal; feeds the prevention engine. |
| **Illness / Autonomic Early-Warning engine** | time-baseline | both | The prevention centrepiece (above). Resp-rate + RHR + HRV co-occurrence, personal baseline, CUSUM. |

### P1 — the coaching + safety layer
| Build | Feasibility | Surface | Value / method |
|---|---|---|---|
| **Strain Target / Load Coach** | time-baseline | both | Turns readiness into a prescribed daily 0–21 load — WHOOP's signature loop; caps load when Strained. |
| **Acute:Chronic Workload Ratio** | now | both | 7d:28d load, flags the overreaching/injury window (Gabbett) — direct injury-prevention for a grappler. |
| **Heart-Rate Recovery (HRR) trend** | now | both | 1-min HRR = validated fitness + all-cause-mortality marker; promote our per-session best-60 s to a tracked trend. |
| **Sleep Need + Sleep Debt** | time-baseline | both | Personalised to his >9 h DNA (not generic 8 h); accrual + recommended bedtime; feeds readiness/strain. |
| **Behaviour / Journal correlation** | more-data | web | Yes-night vs no-night effect sizes (alcohol, late training, Sabbath rest) — the WHOOP Journal killer feature; needs a light tagging path. |
| **Recovery-cost / dose-response coupling** | time-baseline | web | Lagged regression: prior-day load → next-day HRV/readiness — his *personal* recovery cost per dose. |
| **AFib / irregular-rhythm screen** | research | both | ⚠️ **Red-team's biggest risk — see below. Gate carefully or defer.** |

### P2 — longevity + deep science (web-first)
| Build | Feasibility | Surface | Value / method |
|---|---|---|---|
| **HRV-based real-time Stress** | now | both | Live HR+HRV vs baseline (upgrade from HR-elevation-only); breathwork nudges. |
| **Passive VO₂max** | more-data | both | RHR+HRV+demographics (WHOOP passive tier); present as a **banded range**, not a point. |
| **Cardiovascular-Age proxy** | more-data | web | RHR+HRV+VO₂max composite; label as proxy (true PWV needs locked PPG). |
| **Resilience & Cumulative Stress** | time-baseline | both | 14-day bounce-back + 31-day chronic scan (Oura) — slow-burn burnout warning. |
| **DFA α1 aerobic-threshold** | research | web | True zone-2 for low-endurance-DNA base-building; experimental, from exercise RR. |
| **Weekly + Monthly Assessment** | time-baseline | web | Monday + monthly narrative of what's improving/declining (WHOOP/Oura/Apple Trends). |

## Web deep-dive (analyst's cockpit — extends `/whoop/view`)
1. **HRV Lab** — nightly RMSSD/SDNN/pNN50 with mean±SD envelopes + frequency-domain (LF/HF/total power) + Poincaré scatter.
2. **Load & Injury** — cardio-load bars, strain-target line, ACWR ribbon (danger band shaded), per-session BJJ/CrossFit deep-dives (zones, HR drift/decoupling, best-60 s HRR).
3. **Recovery-cost coupling** — prior-day load vs next-day readiness regression.
4. **Sleep** — duration vs >9 h need, debt curve, fragmentation, nocturnal HR dip + HRV trajectory.
5. **Trends & Longevity** — RHR/HRV/VO₂max/CV-age arrows (90d vs 365d), resilience, cumulative stress.
6. **Behaviour correlations** — effect sizes per tag.
7. **Prevention log** — timeline of every flag with the driving signal + exportable physician-shareable report.
8. **Data integrity** — coverage/wear-time chart + DFA-α1 (experimental).
All compute server-side; the web app only renders.

## 🔴 Red Team — the honesty layer (read before building)
- **Biggest risk — the AFib / irregular-rhythm screen.** Every competitor ships this *only* on FDA-cleared, clinician-validated algorithms; ours would run on undecoded optical PPG where beat-detection artifact is routinely indistinguishable from true irregularity. Surfacing any cardiac "flag" — even "discuss with a clinician" — risks real anxiety (false positives) or false reassurance (false negatives), and it rides into the always-fire safety channel. **Verdict: `medically-risky-framing`.** Fix: **defer, or gate behind heavy artifact-rejection + explicit "not a medical device, screening prompt only" framing + conservative thresholds — and do NOT put it in the always-fire channel until validated.**
- **Second caution — over-claiming illness.** Red-tier copy that asserts "likely illness" is over-reach: HR+RR alone can't distinguish infection from alcohol, heat, hard training, or poor sleep. Fix: reframe as *"your autonomics are strained — could be illness, training, alcohol, or poor sleep; ease today and watch."*
- **Over-promised — Cardiovascular Age.** True arterial-stiffness needs PPG pulse-wave morphology (locked); ours is a composite proxy — label it as such.
- **Most items = `needs-validation`:** compute them, but validate against a reference / show as trends before headlining absolute numbers (VO₂max, DFA-α1, max-HR, recovery-cost, resp-rate). `sound` with no caveat: Multi-input Readiness, Wear-time guard, Strain Target, Weekly Assessment.
- **Strongest bet:** ship the trio **Multi-input Readiness + Wear-time guard + Strain Target** first — the genuinely reproducible recovery-and-load core, no sensor over-reach, no diagnostic framing, immediate honest value: the daily "push vs rest" call Ruby actually asked for.

## Recommended build sequence
1. **P0 core (strongest bet):** Max-HR calibration → Multi-input Readiness → Wear-time guard → freq/non-linear HRV → Illness engine (amber/red, reframed copy, **no AFib in the always-fire channel yet**).
2. **P1 coaching:** Strain Target → ACWR → HRR trend → Sleep Need/Debt.
3. **Web deep-dive** built in parallel with P0/P1 (it's just rendering server-computed series).
4. **P2 longevity + experimental** (VO₂max, CV-age, resilience, DFA-α1, assessments) — with validation caveats.
5. **AFib screen:** research + validate separately; ship only gated + non-alarming, or defer to the R22-decode era.

*Council + Red Team, 2026-07-04. All sources in `WHOOP_RESEARCH_REFERENCES.md` (147 citations). Workflow run `wf_35d64a98-6ad`.*
