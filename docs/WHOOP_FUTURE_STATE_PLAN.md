# WHOOP-Alternative — Future-State Plan · 2026-07-04 (Fable second-pass review)

Research-backed roadmap to turn our HR + RR data into a **best-in-class insight + prevention** tracker —
"not just stats, but great insights into my body and prevention." Built by a Council (sports scientist,
HRV/autonomic researcher, cardio-data-scientist, product lead) from the brand research, then stress-tested
by a Red Team, then hardened by a five-lens Fable second pass (physiology, feasibility, product, red-team,
references). Cross-check sources in `WHOOP_RESEARCH_REFERENCES.md`; current build in `WHOOP_CURRENT_STATE.md`.

> **⚠️ Safety & Scope (standing boundary — applies to the whole system and both surfaces).**
> Experimental, personal **n-of-1 wellness**. **Not a medical device**, not diagnostic, not for detecting or
> preventing disease; nothing here is medical advice — seek care for symptoms regardless of any score. All
> signals derive from firmware-emitted **optical pulse intervals**, blind to temperature and blood oxygen.
> "Prevention" here means **baseline-deviation watch**, not disease detection. The personal build is firewalled
> from anything shipped to other RivaFlow users — no health/illness/rhythm feature ships to third parties
> without medical-device review.

**Design constraints:** phone stays **slim** (fetch + display); rich graphs live in a **web deep-dive**; all
compute stays **server-side** (2-min GitOps iteration); everything scored vs Ruby's **own rolling baseline**
(**robust estimator — median/MAD, not mean±SD** — see prevention engine), never population norms; **no motion
sensor**, so HRV/stress/resp-rate are restricted to rest/sleep windows detected by an HR-stability heuristic
(a partial substitute for competitors' accelerometer gate). **Sabbath-aware** per the explicit tier→channel map
below (performance nudges silent Sunday; illness/safety flags always fire).
**Profile lens:** 44yo, BJJ blue→purple + CrossFit, high-strength/low-endurance DNA, NSAID-sensitive, >9 h sleep-need.

## Strategic pillars
1. **Recovery Intelligence** — one honest HRV-led "push vs rest" call vs his baseline (WHOOP Recovery / Oura Readiness / Fitbit Daily Readiness core — fully reproducible from HR+RR).
2. **Training Load & Injury Prevention** — strain target, acute:chronic load ratio, per-session recovery cost, tuned for a masters grappler so load never outruns recovery.
3. **Baseline-Deviation Watch** (the prevention centrepiece) — multi-signal deviation-from-baseline; matters more given NSAID-sensitivity (early rest beats late medication). *Renamed from "Illness Early-Warning" to avoid medical-device intended-use framing.*
4. **Sleep & Recovery Debt** — honours the >9 h DNA sleep-need with need/debt accrual + HR-based quality + **sleep regularity** (onset/offset consistency — cheap, universally shipped).
5. **Longevity & Trend Intelligence** — cardiovascular-age *proxy* (web-only, caveated), resilience/cumulative-stress, frequency & non-linear HRV, **circadian/chronotype** rhythm, weekly/monthly assessments (web deep-dive).
6. **Honest n-of-1 Science** — robust personal baselines, frequency-domain + Poincaré HRV unlocked (quality-gated), behaviour-correlation engine, faith-first surfacing.

> **✅ STATUS (2026-07-04): the entire matrix below is BUILT, tested (CI green), and on `main`** —
> 16 core modules, 35 `/whoop` endpoints, plus the delivery layer, web cockpit, and iOS slim app.
> Only **B20 (AFib)** is deferred (decode-gated). See `WHOOP_CURRENT_STATE.md §3b` for the shipped map;
> the remaining tail is B6 threshold *tuning* on real tags. Phasing lived in `WHOOP_REMAINING_BUILD_PLAN.md`.

## Traceability matrix (the single spine — every build appears once)
Feasibility legend: `now` = codeable + data available · `Nd` = needs N days of coverage · `~Nses` = needs ~N tagged sessions · `research` = experimental · `decode-gated` = blocked on locked R22/K21.
Surface: **slim** (always-visible phone) / **web** (deep-dive) / **both**.

| # | Build | Pillar | Prio | Feasibility | Surface | Web panel | Acceptance criterion (the "done" bar) |
|---|---|---|---|---|---|---|---|
| B0 | **RR/HR signal characterisation & QC gate** | 6 | **P0** | now | web | Data-integrity | Artifact-% per segment computed; clean-segment gate defined; ectopy-corrected + interpolated series feeds all downstream metrics; artifact-% shown beside each value |
| B1 | **Personalised Max-HR calibration** | 1,2 | **P0** | ~5ses | both | Load & Injury | Artifact-rejected sustained plateau (≥10–30 s near-max), not a 1-sample spike; value carries an uncertainty band; flagged "floor — sub-maximal" when below Tanaka; zones shift for Ruby |
| B2 | **Multi-input Readiness** (lnRMSSD-led) | 1 | **P0** | now | both | HRV Lab | Morning verdict fuses lnRMSSD (led) + nocturnal-RHR trend + resp-rate + sleep (down-weighted); reproduces the WHOOP-Recovery/Fitbit-Readiness shape; green carries the "green ≠ healthy" caveat |
| B3 | **Capture-coverage / wear-time guard** (HR **and** RR tracked separately) | 6 | **P0** | now | both | Data-integrity | RR-minutes/night + contiguous-segment length tracked; nights below RR threshold excluded from all baselines; coverage-in-days surfaced |
| B4 | **Frequency-domain + non-linear HRV** | 5,6 | **P0** | now | web | HRV Lab | LF/HF/total-power via Lomb-Scargle on **≥5-min stationary** windows only; LF:HF labelled descriptive (not sympatho-vagal); Poincaré shown as visualisation (SD1≡RMSSD/√2); SD2/SD1 + DFA the additive metrics |
| B5 | **Strain Target / Load Coach** | 2 | **P0** | 14d | both | Load & Injury | Readiness → prescribed daily 0–21 load; caps load when Strained. *Promoted to P0 to match the strongest-bet trio.* |
| B6 | **Baseline-Deviation Watch engine** | 3 | **P0-scoped, activates after baseline** | 14–21d | both (amber/red only) | Baseline-Deviation log | The centrepiece (spec below). Ships once its Validation & tuning gate passes; **no cardiac-rhythm signal**, resp-rate **not** headline-weighted until validated |
| B7 | **Acute:Chronic Workload Ratio** | 2 | P1 | 28d | both | Load & Injury | 7d:28d load computed once 28 d coverage exists; danger-band ribbon shaded (Gabbett) |
| B8 | **Heart-Rate Recovery (HRR) trend** | 2 | P1 | ~10ses | both | Load & Injury | Protocol-defined window (peak → HR at 60 s of relative stillness), gated on clean peak + low motion; presented as **within-person fitness trend, no mortality claim** |
| B9 | **Sleep Need + Sleep Debt** | 4 | P1 | 14d | both | Sleep | Personalised to >9 h DNA; accrual + recommended bedtime; feeds readiness/strain |
| B10 | **Sleep Consistency / Regularity** | 4 | P1 | now | both | Sleep | Onset/offset variability score from the HR sleep-window; a Sabbath-rest tag for the correlation engine |
| B11 | **Behaviour / Journal correlation** | 6 | P1 | ~20 tags | web | Behaviour | Yes-night vs no-night effect sizes (alcohol, late training, Sabbath rest) once a light tagging path exists |
| B12 | **Recovery-cost / dose-response coupling** | 2 | P1 | 21d | web | Recovery-cost | Lagged regression: prior-day load → next-day lnRMSSD/readiness; his personal recovery cost per dose |
| B13 | **HRV-based real-time Stress** | 1 | P2 | research | web (caveated) | HRV Lab | Live HR+HRV vs baseline; **down-tagged from `now`** — no motion gate, so restricted to detected rest windows and flagged experimental |
| B14 | **Passive VO₂max** | 5 | P2 | 21d + ~14 recoveries | both | Trends | RHR+HRV+demographics (WHOOP passive tier); presented as a **banded range**, not a point |
| B15 | **Cardiovascular-Age proxy** | 5 | P2 | 28d | **web only** | Trends | Composite proxy; hard non-clinical caveat, **no alarming arrows**, no individual-risk language (true PWV needs locked PPG) |
| B16 | **Resilience & Cumulative Stress** | 5 | P2 | 14d + 31d | both | Trends | 14-day bounce-back + 31-day chronic scan (Oura); slow-burn burnout warning |
| B17 | **Circadian / Chronotype rhythm** | 5 | P2 | 14d | web | Trends | Cosinor on time-of-day HR/HRV + nocturnal HR-dip timing; ties to >9 h need + Sabbath rhythm *(was dropped — restored)* |
| B18 | **DFA α1 aerobic/anaerobic threshold** | 2 | P2 | research | web (caveated) | Data-integrity | States both crossings (0.75≈VT1/AeT, 0.5≈VT2/AnT); **suppressed when artifact >3%**; validated vs chest-strap ECG before surfacing — **likely infeasible from optical exercise RR** |
| B19 | **Weekly + Monthly Assessment** | 5 | P2 | 14d / 31d | web | all | Monday + monthly narrative of what's improving/declining (WHOOP/Oura/Apple Trends) |
| B20 | **RR-irregularity (AFib-class) screen** | 3 | **deferred** | **decode-gated** (blocked on R22 raw-PPG SQI) | web, gated, **off by default** | Baseline-Deviation log | See red team. **Never** in the always-fire channel; only after separate validation + heavy artifact rejection + explicit non-diagnostic framing |

## 🛡️ The Prevention Engine — "Baseline-Deviation Watch" (centrepiece)
A personal-baseline **anomaly engine** — the common denominator across WHOOP Health Monitor, Oura Symptom
Radar, Apple Vitals, Fitbit Health Metrics — rebuilt from the two signals we own end-to-end: continuous HR
and the RR tachogram. **It detects *deviation*, never disease.**
- **Signals (FOUR — no cardiac-rhythm input):** (1) nocturnal-RHR elevation, (2) **ln**RMSSD / HF-power suppression, (3) RR-derived respiratory-rate rise, (4) nocturnal sleeping-HR elevation + blunted overnight dip. *The AFib-class RR-irregularity signal is **removed** from this engine (see red team + B20).* **Independence note:** signals (1) and (4) are both nocturnal-HR-level measures that co-move for non-illness reasons (alcohol, late meal, warm room), so the co-occurrence rule treats them as **one nocturnal-HR family** — a single HR-level shift counts once, never as two of the ≥2 required outliers. (2) is the vagal family, (3) the respiratory family; co-occurrence requires outliers across **distinct families**.
- **Baselines (robust, not mean±SD):** each signal gets its own rolling **14–21 day median ± MAD** (or winsorised mean) so a single anomaly can't desensitise the detector; **anchored to a curated healthy-reference window**; wear-gap **and** RR-gap nights excluded by B3, and tagged perturbed days (illness/alcohol/heavy-camp) excluded so they can't recalibrate "normal" upward.
- **Slow-drift guard:** compare the short 14–21 d baseline against a **longer stable reference** so a gradual overtraining/subacute drift becomes a flag rather than being silently absorbed.
- **Logic:** per-signal daily z-score **on the log scale for HRV** + a **CUSUM** accumulator (state slack `k` and decision interval `h`) for slow multi-day drifts; the alert fires on **co-occurrence** (Apple Vitals' "multiple outliers together" rule) — one flagged vital is noise, resp-rate + RHR + HRV deviating *together* is signal. Concrete defaults to tune: 🟡 amber at |z|≥1.5 on **≥2 distinct signal families**, or a CUSUM breach **confirmed by a second family** — a solo CUSUM breach never fires a tier, and **respiratory rate can never be the sole driver of any tier** (amber or red); 🔴 red at |z|≥2 on ≥2 families. **Respiratory rate is NOT headline-weighted until validated** — it is our least-direct signal (crude RSA estimate, degrades with age + autonomic suppression), so weight signals by **inverse-variance / measured reliability** (RHR and lnRMSSD are the most direct), and require true multi-signal co-occurrence so resp-rate alone can never trigger red.
- **Validation & tuning (gate before it ships to any channel):** retrospectively self-tag past illness/hard-training/travel days; backtest the engine over that window; establish the night-to-night SD of each signal (resp-rate must resolve a <1 bpm shift to earn weight). **Acceptance target:** flags the last ≥2 known illness onsets with **<1 false amber/week** before it is allowed to fire.
- **Tier → channel map (explicit, so no future edit silently reclassifies):**
  - 🟢 in-range — **not a clearance to push.** Carries the standing caveat: *"no deviation in the signals I can measure (HR, HRV, breathing); I am blind to temperature and blood oxygen — trust symptoms over a green light."*
  - 🟡 amber ("watch — your body's working harder") — **safety channel, fires Sunday.** It is early-warning, not a coaching nudge; silencing it would eat the 1–2 day pre-symptom window the engine exists for.
  - 🔴 red ("strong multi-signal deviation — rest and recover") — **always fires** (incl. Sunday).
  - Only pure **performance/coaching** nudges (strain target, push-harder) are Sabbath-silenced.
- **Delivery (anti-anxiety):** health/anomaly findings are a **once-daily morning digest with alert cooldown**, not a live-refreshing red light; the 2-min dashboard refresh is for **neutral performance data only**. Constant self-checking is itself a wellness risk — designed against on purpose.
- **Honest boundary:** detects *deviation* and prompts caution/rest/clinician-conversation — **never diagnoses**; reframed copy: *"your autonomics are strained — could be illness, training, alcohol, heat, or poor sleep; ease today and watch."* Without temp/SpO₂ it will miss purely thermal or oxygenation events (R22 decode is the future unlock).

## Recommended build sequence
1. **QC first:** **B0 signal characterisation & QC gate** — nothing downstream is trustworthy without it.
2. **P0 strongest-bet trio (the honest, reproducible recovery-and-load core Ruby actually asked for):**
   **B2 Multi-input Readiness → B3 Wear/RR-coverage guard → B5 Strain Target.** No sensor over-reach, no diagnostic framing.
3. **B1 Max-HR calibration** (enabler for every zone/strain/stress) + **B4 freq/non-linear HRV** (feeds the engine).
4. **B6 Baseline-Deviation Watch** — activates after its 14–21 d baseline + Validation gate; amber/red only, reframed copy, **no AFib signal**.
5. **P1 coaching:** B7 ACWR → B8 HRR trend → B9 Sleep Need/Debt → B10 Regularity → B11 Behaviour correlation → B12 Recovery-cost coupling.
6. **Web deep-dive** built in parallel with P0/P1 (it's just rendering server-computed series).
7. **P2 longevity + experimental** (B13 real-time Stress, B14–B19) — with validation caveats; **B15 CV-age web-only, no mortality/age-alarm framing**.
8. **B20 AFib screen:** deferred/decode-gated; ship only after separate validation, gated + non-alarming, **never in the always-fire channel**.

## Web deep-dive (analyst's cockpit — extends `/whoop/view`, renders server-computed series only)
1. **HRV Lab** — nightly lnRMSSD/SDNN/pNN50 with robust envelopes + frequency-domain (≥5-min windows, LF:HF descriptive) + Poincaré scatter.
2. **Load & Injury** — cardio-load bars, strain-target line, ACWR ribbon (danger band shaded), per-session BJJ/CrossFit deep-dives (zones, HR drift/decoupling, protocol HRR).
3. **Recovery-cost coupling** — prior-day load vs next-day readiness regression.
4. **Sleep** — duration vs >9 h need, debt curve, regularity, fragmentation, nocturnal HR dip + HRV trajectory.
5. **Trends & Longevity** — RHR/HRV/VO₂max arrows (90d vs 365d), resilience, cumulative stress, circadian rhythm; **CV-age proxy caveated, no alarming arrows**.
6. **Behaviour correlations** — effect sizes per tag.
7. **Baseline-Deviation log** — timeline of every flag with the driving signal + a **neutral personal data export** (stamped with validation status + blind spots; explicitly *context for a conversation, not clinical data* — never to rule anything in or out).
8. **Data integrity** — coverage/wear-time + **RR-coverage** chart, artifact-% trend, DFA-α1 (experimental, suppressed on high artifact).

## 🔴 Red Team — the honesty layer (read before building)
- **Critical — the AFib deferral was leaking.** The AFib-class RR-irregularity signal was written directly into the always-fire prevention engine's signal set and the screen's surface was "both" (the slim always-visible phone). **Fix applied:** the signal is **removed** from the engine (now 4 signals), and B20's surface is **web, gated, off by default**. No cardiac-rhythm signal contributes to any always-fire alert. And the feasibility is worse than "research": the artifact rejection FDA-cleared PPG AFib algorithms rely on runs on the **raw optical waveform (locked R22)**; on WHOOP-emitted PPI alone, ectopy/missed beats/motion are indistinguishable from true irregularity — so it is **decode-gated**, not merely experimental. (Competitor "AFib from RR" runs on raw-PPG bursts with quality gating, not a bare IBI feed.)
- **Critical — no standing "not a medical device" boundary.** "Prevention" and "illness early-warning" are intended-use language a regulator (TGA/FDA) classifies on, and RivaFlow is a **shipped, revenue product**. **Fix applied:** standing Safety & Scope boundary at the top of both docs + both UI surfaces; pillar 3 renamed **Baseline-Deviation Watch**; personal build firewalled from third-party ship.
- **High — false reassurance ("green ≠ healthy").** A green readiness or 🟢 tier can be returned while a fever/hypoxic event is incubating (temp/SpO₂ locked). **Fix applied:** every green/in-range verdict carries the explicit "blind to temperature and blood oxygen — trust symptoms" caveat; green = "no alarm", never "cleared to push" when symptoms are logged.
- **High — Sabbath-silence could suppress a real early-warning.** **Fix applied:** the tier→channel map above makes amber/red illness flags fire Sunday; only performance nudges are silenced.
- **High — respiratory rate was weighted heaviest but is the least-validated signal** (crude RSA estimate; references give WHOOP no day-count — the only sourced lead-time is Oura/TemPredict ~2.75 d). **Fix applied:** resp-rate is inverse-variance weighted with an error-budget gate, never headline-weighted or able to fire red alone until it resolves a <1 bpm shift.
- **High — baseline poisoning + no robust estimator.** **Fix applied:** median/MAD, healthy-reference anchoring, slow-drift guard, and perturbed-day exclusion (above).
- **Medium — individual-prognostic framing.** HRR "mortality marker" and a worsening CV-age arrow present population associations as personal prognosis. **Fix applied:** HRR is a fitness trend (no mortality claim); CV-age is web-only, caveated, no alarming arrows; population associations ≠ individual outcome.
- **Medium — artifact/ectopy contaminates *every* RR-derived metric, not just AFib** (benign PVCs/PACs + high vagal RSA in a fit 44 yo inflate RMSSD and distort resp-rate). **Fix applied:** B0 QC gate is the first build; ectopic/artifact handling sits upstream of every metric with a per-night artifact gate.
- **Most items = `needs-validation`:** compute them, but validate against a reference / show as trends before headlining absolute numbers (VO₂max, DFA-α1, max-HR, recovery-cost, resp-rate). `sound` with no caveat: Multi-input Readiness, Wear/RR-coverage guard, Strain Target, Sleep Regularity, Weekly Assessment.
- **Strongest bet:** ship the trio **Multi-input Readiness + Wear/RR-coverage guard + Strain Target** (after B0 QC) — the genuinely reproducible recovery-and-load core, no sensor over-reach, no diagnostic framing: the daily "push vs rest" call Ruby actually asked for.

*Council + Red Team + Fable five-lens second pass, 2026-07-04. All sources in `WHOOP_RESEARCH_REFERENCES.md` (146 sources). Workflow runs `wf_35d64a98-6ad`, `wf_a5ec3997-460`.*
