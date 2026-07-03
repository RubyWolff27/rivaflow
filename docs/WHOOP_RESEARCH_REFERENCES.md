# WHOOP-Alternative — Brand Research & References (2026-07-04)

> Deep research on the major health/fitness trackers, gathered by a 5-agent research council to inform our
> self-hosted build. **Every source URL is preserved for cross-checking with a secondary council.**
> Scope lens: we compute from **heart rate + RR-intervals only** (SpO₂/temp/steps/staging are locked — see CURRENT_STATE).

## WHOOP (WHOOP 5.0 / WHOOP MG, WHOOP Life & Peak/One memberships)
**Signature / why it's valuable:** The strain-vs-recovery balance loop is WHOOP's signature: a single morning Recovery Score (HRV-led) is converted into a prescriptive daily Strain Target, so the device doesn't just report numbers - it tells you how hard to go today and how much to sleep tonight to stay in balance. Critically for a HR+RR-only build, the two most valuable pillars (the HRV-driven Recovery/readiness score and the HR-zone Strain load, plus RR-derived respiratory-rate illness early-warning and the personal-baseline anomaly engine) are all reproducible from heart rate and beat-to-beat RR-intervals alone - SpO2, skin temp, ECG and blood pressure are additive refinements, not the core.

**Metrics surfaced:**
- Recovery Score (0-100%, red/yellow/green readiness band) - the flagship daily score
- Day Strain (0-21 logarithmic Borg-scale cardiovascular load across the whole 24h)
- Activity/Workout Strain (0-21 per logged workout)
- Heart Rate Variability (HRV, reported as RMSSD/lnRMSSD in ms, computed during sleep)
- Resting Heart Rate (RHR, measured during sleep)
- Live/continuous Heart Rate (bpm, 24/7)
- Respiratory Rate (breaths per minute during sleep)
- Sleep Performance (% of sleep need met)
- Sleep Duration + all 4 stages: Light, REM, Slow-Wave/Deep, Awake
- Sleep Need (personalized nightly target)
- Sleep Debt (accumulated shortfall)
- Sleep Efficiency (% of time in bed asleep)
- Sleep Consistency (regularity of bed/wake times over ~4-day window)
- Sleep Stress (autonomic activation during sleep)
- Wake events / disturbances / time in bed / latency
- Stress Score (0-3, real-time daytime, from Stress Monitor)
- Blood Oxygen / SpO2 (%)
- Skin Temperature (deviation from baseline)
- VO2 Max estimate (mL/kg/min)
- Steps / estimated distance
- Calories / energy expenditure
- Heart Rate Zones (time in each zone)
- WHOOP Age (biological age estimate, Healthspan)
- Pace of Aging (30-day trend of biological aging rate)
- Lean Body Mass (input to Healthspan)
- Strength Trainer muscular load (volume x intensity)
- Blood Pressure Insights (daily systolic/diastolic estimate ranges, MG only)
- ECG heart rhythm reading (normal sinus vs AFib/irregular, MG only)
- Menstrual/Hormonal cycle phase & Hormonal Insights
- Estimated max heart rate

**Insights / coaching (interpretation beyond raw numbers):**
- Daily readiness verdict: red/yellow/green Recovery translates raw HRV+RHR+sleep into a plain 'rest vs push' recommendation
- Strain Target / Strain Coach: prescribes an optimal daily strain number based on today's Recovery, so you 'maintain fitness and still recover tomorrow' - the signature strain-vs-recovery balance
- Real-time Strain Coach guidance during a workout: push harder / you've hit your goal / you're overdoing it
- Sleep Coach / Sleep Planner: tells you exactly how much sleep you need tonight and a recommended bedtime, adjusting for accrued sleep debt, that day's strain, and naps
- Everything is scored against YOUR personal rolling baseline (14-day / multi-day), not population norms - a deviation matters relative to your own normal
- WHOOP Journal behavior correlations: logs habits (alcohol, caffeine, late meals, reading, etc.) and statistically compares yes-nights vs no-nights to show how each behavior moves your HRV, RHR, Recovery, sleep efficiency and consistency
- Weekly Performance Assessment (every Monday) and Monthly assessments: trend summaries with bed/wake-time variability, sleep consistency, and what's improving or declining
- Stress Monitor recommends science-backed breathwork - relaxing or alerting - depending on live stress level
- WHOOP Coach (AI/LLM chat): natural-language, adaptive coaching answering 'what should I do today' from your own data
- Healthspan / WHOOP Age coaching: shows how current behaviors add or subtract biological years and what to change
- Hormonal Insights: tailors strain/recovery/sleep guidance to menstrual cycle phase and pregnancy

**Prevention / early-warning:**
- Health Monitor: 5 vitals (HRV, RHR, respiratory rate, SpO2, skin temp) each flagged green-check (in range) or orange/red exclamation (outside personal baseline)
- Illness early-warning: elevated respiratory rate frequently rises BEFORE symptoms of respiratory infection/fever - documented case studies of pneumonia and viral illness caught pre-symptom
- Skin-temperature and SpO2 deviations from baseline flag illness, fever, environmental change, or menstrual-phase shifts
- Overtraining / strain-recovery imbalance protection: suppressed HRV + elevated RHR drive a low (red) Recovery and Strain Target caps recommended load so you don't dig deeper
- Sleep-debt accrual warning drives higher Sleep Need and earlier recommended bedtime
- Stress Monitor surfaces sustained physiological stress and prompts breathwork intervention in real time
- Exportable Health Report (baselines/trends PDF) to share with a physician
- ECG / Heart Screener (MG): detects irregular rhythm / atrial fibrillation from a 30-second thumb reading + irregular-rhythm notifications
- Daily Blood Pressure Insights (MG) flag hypertension trends
- Core anomaly engine = deviation-from-your-own-baseline across every vital; the HR+RR-derived vitals (HRV, RHR, respiratory rate) are the reproducible early-warning signals

**Methods + sensor inputs (what's reproducible from HR+RR):**
- Recovery Score: weighted model dominated by HRV (carries most predictive value), plus RHR and Sleep Performance (down-weighted, overlap with HRV), plus respiratory rate/skin temp/SpO2/menstrual phase as outlier-correcting inputs. HR + RR-intervals do the heavy lifting (HRV+RHR) => core Recovery is largely reproducible from HR+RR alone.
- HRV: computed during sleep (most stable state); weighted average across the night, MORE weight on slow-wave sleep and later-night stages; uses RMSSD and lnRMSSD (log-transformed) for day-to-day stability. Inputs: RR-intervals ONLY - fully reproducible.
- RHR: lowest sustained heart rate during sleep. Inputs: HR only - fully reproducible.
- Respiratory Rate: extracted from beat-to-beat waveform during sleep (respiratory sinus arrhythmia modulates RR-intervals). Inputs: RR-intervals - reproducible via RSA/ECG-derived respiration, no extra sensor strictly required.
- Strain: 0-21 logarithmic Borg-RPE scale; core = time-weighted HR-zone duration relative to estimated max HR; log scaling so 0->10 is far easier than 10->20 and workouts don't linearly sum. Inputs: HR only for cardio strain (reproducible); muscular/Strength-Trainer load adds accelerometer + logging.
- Sleep staging (Light/REM/SWS/Awake): HR + HRV + accelerometer motion. Inputs: HR+RR+accel - partially reproducible (staging degrades without motion).
- Sleep Need / Debt: personal baseline need + accrued debt + that day's Strain + recent naps. Derived - reproducible if you have strain+sleep.
- Stress Score (0-3): live HR + HRV vs 14-day baseline using lnRMSSD, with accelerometer motion-gating to separate exercise from psychological stress. Inputs: HR+RR+accel - largely reproducible from HR+RR.
- VO2 Max: 3-tier proprietary model - passive tier (>=14 recoveries in 21 days) from resting HR, HRV, activity, sleep, demographics (age/height/weight/sex); optional GPS-augmented tier from outdoor-run pace+HR; optional lab 'Ground Truth' calibration. Accuracy ~3.3-3.7 mL/kg/min vs metabolic cart. Passive tier reproducible from HR+HRV+demographics.
- Baseline/anomaly engine: rolling personal baseline (~14-day) per vital; flag when a reading exits the personal typical range.
- SpO2: red+infrared pulse oximetry (dedicated LEDs) - NOT reproducible from HR+RR. Skin Temperature: dedicated thermal sensor, deviation from baseline - NOT reproducible from HR+RR. Blood Pressure: PPG-waveform overnight model (MG). ECG: single-lead clasp electrodes (MG). Steps/distance/calories: accelerometer + HR. Algorithm lineage cited to HRV/training research (Kiviniemi, Plews, Buchheit, Flatt).

**Sources:**
- https://www.whoop.com/us/en/thelocker/how-does-whoop-recovery-work-101/
- https://www.whoop.com/us/en/thelocker/member-averages-recovery-strain-sleep-hrv/
- https://developer.whoop.com/docs/whoop-101/
- https://www.whoop.com/us/en/thelocker/heart-rate-variability-hrv/
- https://www.whoop.com/us/en/thelocker/heart-rate-variability-training/
- https://www.whoop.com/us/en/thelocker/introducing-stress-monitor-a-new-way-to-monitor-manage-stress/
- https://www.whoop.com/us/en/press-center/whoop-launches-new-stress-monitor-feature-first-wearable-to-measure-daily-stress-levels-and-implement-stress-reduction-interventions-in-real-time/
- https://www.kygo.app/post/whoop-stress-score-recovery-explained
- https://www.whoop.com/us/en/thelocker/health-monitor-feature/
- https://support.whoop.com/s/article/WHOOP-Health-Monitor-Report
- https://www.whoop.com/us/en/thelocker/how-whoop-tracks-skin-temperature/
- https://www.whoop.com/us/en/thelocker/introducing-whoop-5-0-and-whoop-mg/
- https://www.whoop.com/us/en/life/
- https://www.whoop.com/us/en/press-center/whoop-unveils-5.0-MG/
- https://www.whoop.com/us/en/thelocker/how-does-whoop-strain-work-101/
- https://www.whoop.com/us/en/thelocker/strain-coach/
- https://support.whoop.com/s/article/Strain-Coach?language=en_US
- https://www.whoop.com/us/en/thelocker/how-much-sleep-do-i-need/
- https://www.whoop.com/us/en/thelocker/everything-to-know-about-sleep/
- https://www.whoop.com/us/en/thelocker/the-whoop-journal/
- https://whoop.com/en-gb/thelocker/new-weekly-performance-assessment
- https://support.whoop.com/s/article/VO2-Max?language=en_US
- https://www.whoop.com/us/en/thelocker/how-accurate-is-whoop-vo2-max/
- https://www.whoop.com/us/en/thelocker/estimate-your-vo-max-with-whoop-/
- https://support.whoop.com/s/article/WHOOP-Recovery?language=en_US
- https://support.whoop.com/s/article/How-to-Use-the-AI-Powered-WHOOP-Coach?language=en_US
- https://www.whoop.com/us/en/how-it-works/
- https://wearablebeat.com/articles/how-does-whoop-work-sensors-recovery-scores-and-strain-explained/
- https://openwearables.io/blog/whoop-api-recovery-strain-sleep-data-for-developers
- https://the5krunner.com/2025/10/31/2026-whoop-5-0-mg-review-discount-accuracy-strain-recovery-athletes/

---

## Oura Ring (Gen 3 / Ring 4 / Ring 5) — smart ring; the benchmark for trends, temperature and pre-symptomatic illness detection
**Signature / why it's valuable:** Oura's signature value is TREND-OVER-TIME baselining that converts biometrics into two things nobody else nails as cleanly: (1) a single, trustworthy morning Readiness verdict that tells you what to do today, and (2) Symptom Radar — genuine pre-symptomatic illness detection (~2 days early) built primarily on overnight temperature deviation fused with resting HR, HRV and breathing rate. The temperature signal is its illness-prediction moat; the readiness/HRV/stress/resilience layer is highly reproducible from your HR+RR data, but the temperature-driven early-warning edge will need a temp input to fully match.

**Metrics surfaced:**
- THREE HEADLINE SCORES (all 0-100, personalised baselines): Readiness Score, Sleep Score, Activity Score
- Sleep architecture: Total Sleep Time, Deep (N3), REM, Light (N1/N2), Awake Time, Time in Bed
- Sleep quality metrics: Sleep Efficiency (%), Sleep Latency (mins to fall asleep), Restfulness / Restless Periods, Sleep Timing & Sleep Regularity, Bedtime & Wake Time
- Readiness 'Balance' contributors (14-day weighted avg vs ~2-month baseline): HRV Balance, Sleep Balance, Activity Balance
- Recovery Index — how quickly resting HR settled to its nocturnal minimum and how long it stayed low
- Resting Heart Rate — lowest nocturnal RHR PLUS timing of the RHR low-point (early low = well-recovered)
- Heart Rate Variability — rMSSD, nightly average + the full overnight HRV curve; daytime/live HRV
- Average HR, Lowest HR, and continuous Daytime/Live Heart Rate
- Body Temperature Deviation — nightly skin-temperature trend vs personal baseline (detects +/-0.5C shifts)
- Respiratory Rate (breaths per minute, overnight)
- Blood Oxygen (SpO2) average + overnight variation
- Breathing Disturbance Index (sleep-apnea / breathing-regularity screen)
- Daytime Stress — time in Stressed / Engaged / Relaxed / Restored states + Recovery Time
- Cumulative Stress (Nov 2025) — 31-day chronic-stress accumulation scan
- Resilience — 5 levels: Limited, Adequate, Solid, Strong, Exceptional
- Cardiovascular Age — estimated arterial-stiffness age vs chronological age
- Cardio Capacity (VO2 Max estimate), age-adjusted
- Chronotype (circadian type)
- Activity metrics: Steps, Active Calories, Total Calories, Sedentary/Inactive Time, Low/Medium/High activity time, MET-based activity, training frequency/volume, auto-adjusting daily Activity Goal
- Symptom Radar illness signal (No signs / Minor signs / Major signs)
- Cycle Insights (period prediction, cycle phase) and Pregnancy Insights
- Tags / notes for context (alcohol, illness, caffeine, etc.)

**Insights / coaching (interpretation beyond raw numbers):**
- Every metric is judged against YOUR personal rolling baseline, not population norms — the core Oura philosophy is 'how are you trending vs your own normal'
- Morning Readiness verdict = single actionable recommendation: 'Pay attention / take it easy' vs 'you're recovered, go for it' — turns raw biometrics into one daily call
- Balance contributors coach load management: Activity Balance flags overtraining (too much recent load vs baseline) OR under-training; Sleep Balance flags accumulating sleep debt; HRV Balance flags autonomic drift
- Ideal Bedtime window / bedtime guidance nudging consistent sleep timing to align with chronotype
- Rest Mode — when illness or big temperature/RHR deviation is detected, Oura suggests scaling back and reframes low scores as 'recovery expected'
- Stress-recovery narrative: pairs Daytime Stress load against daytime + sleep recovery so you see whether you're banking or draining reserves
- Resilience coaching: bouncing-back capacity over 14 days — a declining trend is framed as early burnout risk before you feel it
- Cycle-aware readiness: adjusts expectations for natural temperature/HRV/RHR shifts across menstrual cycle and pregnancy so hormonal changes aren't misread as poor recovery
- Auto-adjusting Activity Goal that scales down on low-readiness days rather than pushing a fixed step target
- Cardiovascular Age framed as a motivational 'your heart is X years older/younger than you' with lifestyle levers to improve it

**Prevention / early-warning:**
- Symptom Radar — flagship pre-symptomatic illness detection: fuses elevated skin temperature + elevated resting HR + depressed HRV + disrupted sleep/breathing to warn of oncoming cold/flu, on average ~2 days (TemPredict: 2.75 days) BEFORE subjective symptoms; V2 shows which biomarker drove the alert
- Body-temperature deviation trend — earliest and strongest illness/fever signal; detects shifts as small as +0.5C vs baseline (99% accuracy vs lab in Oura's claims, 76% pre-symptomatic fever detection)
- Cumulative Stress (31-day) — surfaces chronic stress that daily scores normalise away; a chronic-overload / burnout early-warning
- Resilience decline — long-term erosion of bounce-back capacity signals accumulating strain / overtraining / life-stress before collapse
- HRV Balance + Recovery Index drop — autonomic markers of overtraining, under-recovery, or incipient illness
- Cardiovascular Age / arterial-stiffness estimate — long-term cardiovascular-risk early indicator
- Breathing Disturbance Index — screens for disrupted nocturnal breathing / possible sleep apnea
- Elevated resting HR trend + reduced HRV as a general physiological-strain / anomaly flag (also alcohol, poor sleep, late meals)
- Strain-vs-recovery imbalance surfaced explicitly via Readiness balance contributors — activity load outrunning recovery capacity
- Menstrual-cycle and pregnancy anomaly context so illness signals aren't confused with hormonal temperature rises
- Oura has moved toward heart-health screening (AFib-type / cardiovascular preventative direction) as part of its 'deeper into preventative health' roadmap

**Methods + sensor inputs (what's reproducible from HR+RR):**
- SENSORS: PPG (green + red + infrared LEDs with photodetectors), NTC skin-temperature sensor, and a 3D accelerometer. Finger placement gives higher signal-to-noise than wrist (digital arteries near surface, less motion artifact) — Oura's core accuracy claim
- Heart Rate & HRV: from PPG beat-to-beat (inter-beat/RR) intervals; HRV computed as rMSSD (time-domain) plus frequency-domain HRV — REPRODUCIBLE from HR+RR alone (validated: 'Deriving Accurate Nocturnal Heart Rate, rMSSD and Frequency HRV from the Oura Ring', PMC)
- Resting Heart Rate: lowest nocturnal HR + its timing — REPRODUCIBLE from HR
- Respiratory Rate: derived from PPG/HRV respiratory sinus arrhythmia modulation — LARGELY REPRODUCIBLE from RR-interval series (respiratory sinus arrhythmia) even without a dedicated sensor
- Sleep staging (OSSA 2.0): ML model fusing accelerometer (movement) + NTC temperature + PPG (HR, HRV, respiration) + priors on sleep architecture; 79% epoch agreement vs polysomnography (near the 83% human inter-rater rate) — NOT fully reproducible from HR+RR alone (needs accelerometer + temperature; HR/HRV-only staging is weaker)
- Readiness 'Balance' math: recent 14-day weighted average (days 2-5 weighted heavier) compared against ~2-month personal baseline — REPRODUCIBLE algorithmically from any baselined metric
- Recovery Index: time for RHR to reach nocturnal minimum + duration at minimum — REPRODUCIBLE from HR
- Daytime Stress: classification from daytime HRV + HR + skin temperature + motion into stressed/engaged/relaxed/restored — MOSTLY reproducible from HR+RR (temp/motion add fidelity)
- Resilience: 14-day aggregation of daytime stress load (HR, HRV, motion, temp) + daytime AND sleep recovery (Sleep Score, RHR, HRV Balance, Recovery Index) into 5 levels — core is reproducible from HR+RR
- Symptom Radar: on-device model detecting multi-signal deviation (temperature, RHR, HRV, respiratory rate, activity) from personal baseline, trained on years of member-tagged illness data — HR/HRV/resp portion reproducible from HR+RR, but temperature is a key missing input for you
- Body Temperature Deviation: NTC sensor vs personal nightly baseline — NOT reproducible from HR+RR (needs a temperature sensor)
- SpO2 / Blood Oxygen: red + IR PPG ratio — NOT reproducible from HR+RR (needs multi-wavelength SpO2)
- Cardiovascular Age: estimated pulse-wave-velocity (PWV) from PPG waveform SHAPE / arterial-stiffness morphology — NOT reproducible from RR intervals alone (needs raw PPG pulse-wave morphology, not just beat timing)
- Cardio Capacity (VO2 Max): estimated from a 6-minute walk test + anthropometrics (age, sex, height, weight) — NOT reproducible without accelerometer/gait + demographics
- Activity/Steps/Calories: 3D accelerometer + MET modeling — NOT reproducible from HR+RR alone

**Sources:**
- https://support.ouraring.com/hc/en-us/articles/360025589793-Readiness-Score
- https://ouraring.com/blog/readiness-score/
- https://support.ouraring.com/hc/en-us/articles/360025445574-Sleep-Score
- https://ouraring.com/blog/sleep-score/
- https://simplewearablereport.com/learn/metrics
- https://neura.health/insight/how-to-read-and-understand-oura-ring-data
- https://ouraring.com/blog/inside-the-ring-symptom-radar/
- https://ouraring.com/blog/symptom-radar/
- https://www.wareable.com/wearable-tech/oura-symptom-radar-launch
- https://www.androidpolice.com/oura-ring-symptom-radar-out-of-beta/
- https://vertu.com/lifestyle/can-oura-ring-detect-health-problems-early-signs-illness
- https://ouraring.com/blog/inside-the-ring-resilience-feature/
- https://ouraring.com/blog/building-resilience-recover-from-stress/
- https://support.ouraring.com/hc/en-us/articles/25358829055251-Resilience
- https://www.kygo.app/post/oura-ring-stress-tracking-explained
- https://www.wareable.com/health-and-wellbeing/how-to-use-improve-oura-resilience-stress-tracking-shyamal-patel
- https://ouraring.com/blog/smart-sensing/
- https://ouraring.com/blog/new-sleep-staging-algorithm/
- https://www.sciencedirect.com/science/article/pii/S1389945724000200
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8271886/
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11644394/
- https://ouraring.com/blog/cardiovascular-age/
- https://support.ouraring.com/hc/en-us/articles/28451491040019-Cardiovascular-Age
- https://ouraring.com/blog/heart-health-at-oura/
- https://techcrunch.com/2024/05/10/oura-new-heart-health-features/
- https://www.wareable.com/features/vo2-max-cardio-capacity-oura-ring-explained
- https://support.ouraring.com/hc/en-us/articles/28336620578835-Cardio-Capacity-VO2-Max
- https://myringsizecalculator.com/oura-ring-features/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11923143/

---

## Ultrahuman Ring AIR (with Ultrahuman app / M1 CGM / PowerPlugs app-store; UltraSignal dev platform)
**Signature / why it's valuable:** Dynamic (intraday, real-time) Recovery that decomposes into 5 named, individually-explained sub-factors so you see exactly what to fix — combined with the PowerPlugs app-store model (AFib detection, Cardio Adaptability via Lorenz/tachogram autonomic analysis, Caffeine Window, circadian Stress Rhythm) and the UltraSignal open developer platform exposing raw PPG/accelerometer/temperature. The signature edge: recovery you can act on and improve during the day, plus first-on-a-ring cardiovascular prevention (AFib + cardio adaptability) driven almost entirely from HR and RR-interval analysis.

**Metrics surfaced:**
- Dynamic Recovery Score (0-100, updates through the day)
- Sleep Index / Sleep Score (personalised, Algorithm 2.0)
- Sleep architecture: total sleep duration, sleep onset time, wake time, time in light/deep/REM, sleep efficiency %, wake events, WASO (wake after sleep onset)
- Movement Index (0-100, daily activity/strain-vs-recovery balance, resets to 100 each morning)
- HRV (nightly, from RR/beat-to-beat intervals, ms) + 'HRV Form' baseline deviation
- Resting Heart Rate (RHR, baseline-relative deviation)
- Heart rate (continuous nightly, periodic daytime)
- Sleeping heart rate + HRV during sleep + breathing/respiratory rate during sleep
- Skin temperature deviation (nightly, vs personal baseline)
- Nightly blood oxygen / SpO2
- Stress Rhythm Score (stimulated / relaxed / stressed, circadian-mapped)
- VO2 Max estimate
- Cardio Age
- Cardio Adaptability (tachograms + Lorenz/Poincaré plots of RR intervals)
- AFib / irregular-heart-rhythm detection (PowerPlug, nightly)
- Metabolic Score (0-100, requires M1 CGM: glucose variability, average glucose, time-in-target 70-110 mg/dL)
- Glucose metrics (avg glucose, variability %, time-in-range) via M1 CGM
- Movement/activity detection: steps, walking, running, cycling, swimming auto-detection; workout profiles
- Circadian phase alignment metric
- Caffeine window / real-time body caffeine level
- Vitamin D absorption estimate
- Social Jetlag (weekday vs free-day sleep-timing gap)
- Cycle & ovulation / fertile window (skin temp + HRV + RHR)

**Insights / coaching (interpretation beyond raw numbers):**
- Dynamic, intraday recovery that tells you your body's readiness for the next day and updates in real time as markers shift — not a fixed morning number
- Recovery breaks down into 5 named sub-factors (Sleep Quotient, Stress Rhythm, Temperature, RHR deviation, HRV Form) and shows exactly which one is dragging the score so you know what to fix
- Actionable 'what to do today' coaching to reach 85%+ recovery: sleep 7-9h, zone-2 active recovery (120-140 bpm) on rest days, cold therapy 5-10 min spaced from workouts, hydration cadence, caffeine cut-off after ~4pm and 3h before bed
- Recommends recovery interventions in-app: NSDR, naps, breathwork sessions, and stress-rhythm resets
- Stress Rhythm interpretation: maps your stress against your circadian rhythm — high score = stress well-regulated and timed with cortisol curve (stress in morning OK, stress at night bad); flags 'working against your circadian rhythm'
- Personalised baselines: recovery/RHR/HRV/temperature all judged against YOUR rolling baseline deviation, not population norms
- Sleep Algorithm 2.0 personalises the score by age, sex and BMI (e.g. age-adjusts declining deep sleep, credits women for higher REM, gives athletes with low RHR accurate deep/REM) so the score is comparative not absolute
- Movement Index frames movement as strain-vs-recovery balance and non-exercise energy expenditure for glucose metabolism, nudging you to move through the day
- HRV coaching rules for training: use low-HRV mornings to back off / deload, high-HRV to push — turns HRV trend into training-load guidance
- Caffeine Window and Phase Alignment give timing-based nudges (when to get light, caffeine, wind-down) tied to your own rhythm
- Cardio Age contextualises RHR + HRV + VO2max into a single 'how old is your cardiovascular system' number

**Prevention / early-warning:**
- AFib / atrial-fibrillation detection PowerPlug — 'world's first on a smart ring'; nightly PPG bursts analyse rhythm irregularity and generate reports, marketed as catching ~91% of irregular-rhythm events; medical approval in limited markets
- Cardio Adaptability — nightly tachogram + Lorenz/Poincaré plot analysis of RR intervals to track autonomic (SNS/PNS) responsiveness and flag maladaptive cardiac response to stress/activity/rest over time
- Low-HRV early-warning: app explicitly frames low-HRV days as early warning signs of accumulated load — poor sleep, mental stress, heavy training, alcohol, late eating all suppress HRV
- Skin-temperature deviation as illness/sickness signal — sickness spikes temperature; used as a recovery-suppressing input and (via cycle plug) ovulation signal
- Strain-vs-recovery imbalance surfaced by Movement Index + Dynamic Recovery combination
- Stress Rhythm dysregulation flag — chronic mistimed stress (elevated night-time sympathetic tone) surfaced as a lower score, an overtraining/burnout early indicator
- Cardio Age as a longevity/cardiovascular-risk screening proxy (RHR + HRV + VO2max)
- Cycle & Ovulation Pro generates clinician-shareable reports (90%+ ovulation-confirmation accuracy claim)
- Vitamin D plug gives overexposure safety alerts; Social Jetlag flags circadian misalignment that undermines recovery

**Methods + sensor inputs (what's reproducible from HR+RR):**
- Sensor hardware: PPG (green/red/IR) optical sensor for HR/HRV/SpO2, skin-temperature sensor, 3-axis accelerometer/motion sensor. Raw PPG + accelerometer + temperature streams exposed via UltraSignal developer platform
- HRV: computed from beat-to-beat RR intervals (ms) — REPRODUCIBLE from HR+RR alone. Note validation study validated HR but NOT HRV (differing sampling rates)
- Resting Heart Rate: nightly HR minima vs personal baseline — REPRODUCIBLE from HR
- Dynamic Recovery: proprietary weighted aggregate of 5 factors — Sleep Quotient, Stress Rhythm, Temperature, RHR deviation, HRV Form (exact weights undisclosed). 4 of 5 factors derive from HR/HRV; only Temperature needs the temp sensor — LARGELY REPRODUCIBLE from HR+RR (minus temp)
- Stress Rhythm: analyses variations in HR, RHR and HRV across circadian phases — FULLY REPRODUCIBLE from HR+RR
- Cardio Adaptability: tachograms (RR over time) + Lorenz/Poincaré plots (RR[n] vs RR[n+1]) to estimate autonomic HF/parasympathetic modulation — FULLY REPRODUCIBLE from RR intervals
- AFib detection: nightly continuous-PPG bursts; irregular-rhythm classification from RR-interval irregularity (Poincaré/tachogram morphology) — RR-interval irregularity is REPRODUCIBLE from RR alone, though Ultrahuman uses raw PPG
- Sleep staging (Algorithm 2.0): inputs = heart rate, HRV, skin temperature, movement; personalised by age/sex/BMI; enforces physiological stage-transition rules (no deep<->REM without light) — PARTIALLY reproducible (movement + temp missing from HR+RR-only)
- VO2 Max: estimated from age, gender, mobility level, max HR, nightly RHR and body weight (non-exercise sub-maximal HR model); blood-oxygen sensor also cited — mostly REPRODUCIBLE via RHR+demographics, no SpO2 strictly required
- Cardio Age: composite of RHR + HRV + VO2max — REPRODUCIBLE from HR+RR+demographics
- SpO2 / blood oxygen: red/IR PPG ratio-of-ratios — NOT reproducible from HR+RR (needs multi-wavelength PPG)
- Movement Index / activity / step / workout auto-detection: accelerometer — NOT reproducible from HR+RR
- Metabolic Score: proprietary; glucose variability + average glucose + time-in-target — requires M1 CGM, NOT reproducible
- Skin temperature deviation: dedicated temp sensor — NOT reproducible from HR+RR
- HR validation: MAE 2.4-2.6 bpm, RMSE 3.9 bpm, 99.5% variance vs Apple Watch, benchmarked against FDA-cleared SleepImage

**Sources:**
- https://ultrahuman.com/blog/ultrahuman-ring-recovery-score-guide/
- https://www.ultrahuman.com/ring/
- https://www.ultrahuman.com/us/powerplugs/
- https://cyborg.ultrahuman.com/press-releases/ultrahuman-announces-its-app-store-powerplugs-with-the-worlds-first-afib-detection-technology-on-a-smart-ring
- https://ultrahuman.com/blog/sleep-algorithm-2-0-explained-personalized-sleep-scoring/
- https://science.ultrahuman.com/studies/sleep-heart-rate-sensing
- https://ultrahuman.com/science/studies/sleep-heart-rate-sensing
- https://www.ultrahuman.com/blog/hrv-and-stress-explained-how-your-body-signals-overload/
- https://www.ultrahuman.com/blog/5-ways-to-train-better-using-hrv-metric/
- https://www.ultrahuman.com/blog/how-the-timing-of-stress-can-protect-your-health-and-stay-productive/
- https://connectthewatts.com/2024/05/09/ultrahuman-stress-rhythm/
- https://science.ultrahuman.com/studies/is-stress-in-women-more-circadian-aligned
- https://blog.ultrahuman.com/blog/how-the-ultrahuman-ring-air-tracks-skin-temperature/
- https://blog.ultrahuman.com/blog/how-is-your-metabolic-score-calculated/
- https://openwearables.io/blog/ultrahuman-api-ring-data-cgm-recovery-metrics
- https://wearablexp.com/smart-rings/ultrahuman-ring-air-fitness-tracking-capabilities/
- https://www.androidcentral.com/wearables/ultrahuman-ring-air-adds-afib-new-app-store-of-powerplugs
- https://longevity.technology/news/ultrahuman-launches-atrial-fibrillation-detection-via-smart-ring/
- https://x.com/UltrahumanHQ/status/1814321634884411811
- https://honehealth.com/edge/oura-vs-ultrahuman/
- https://liviunastasa.com/2025/08/03/six-months-with-the-ultrahuman-ring-air-a-balanced-data-focused-review/

---

## Google Fitbit / Google Health (Fitbit Sense 2, Charge 6, Pixel Watch line; free tier + Fitbit/Google Premium)
**Signature / why it's valuable:** The Daily Readiness Score is the signature feature - a single, baseline-personalized recovery verdict (HRV + RHR + recent sleep) that translates directly into 'what to do today' via a daily activity goal and an adaptive Cardio Load / Target Load training window, closing the loop from raw HRV/RHR into concrete over/under-training and recovery coaching. Crucially for our build, the whole Readiness + Cardio Load (TRIMP) + Target Load stack, plus HRV, RHR, breathing rate, resting-HR trends and even AFib-style irregular-rhythm screening, are all derivable from heart rate + beat-to-beat RR intervals alone - the exact data we capture - while only SpO2, skin temperature, EDA and single-lead ECG require sensors we lack.

**Metrics surfaced:**
- Daily Readiness Score (0-100, banded Low 1-29 / Good 30-64 / Excellent 65-100)
- Sleep Score (0-100; sub-scores: Time Asleep 50%, Deep+REM 25%, Restoration 25%)
- Sleep stages: light / deep / REM / awake minutes per night
- Sleep Profile (10 monthly metrics: schedule variability, sleep start time, time before sound sleep, sleep duration, deep sleep %, REM sleep %, restorative sleep, restlessness, days with naps, disturbances)
- Sleep Animal chronotype (Bear, Dolphin, Giraffe, Hedgehog, Parrot, Tortoise)
- Stress Management Score (0-100; components Responsiveness /30, Exertion Balance /40, Sleep Patterns /30)
- Cardio Fitness Score / VO2max estimate (single value with GPS run, otherwise a range + Poor/Fair/Good/Very Good/Excellent band)
- Active Zone Minutes (AZM; 1/min Fat Burn, 2/min Cardio & Peak; weekly target default 150)
- Heart-rate zones (Fat Burn / Cardio / Peak, personalized to HR reserve)
- Cardio Load (daily training load, modified Banister TRIMP)
- Target Load / Target Cardio Load range (adaptive weekly load window)
- Training Status (over / optimal / under-training vs history)
- Resting Heart Rate (RHR) + trend
- Heart Rate Variability (HRV, nightly RMSSD-style ms) + 7/30-day trend and personal range
- Breathing / respiratory rate (breaths per min, nightly) + trend
- SpO2 / blood-oxygen saturation (nightly average + on-demand) + variation trend
- Skin temperature variation (deviation from personal baseline)
- All-day continuous EDA (cEDA) skin-conductance stress responses; on-demand EDA Scan
- ECG single-lead reading (sinus rhythm vs AFib)
- Irregular Heart Rhythm Notifications (background AFib screening)
- High & Low heart-rate notifications (threshold alerts)
- Steps, distance, floors, calories, hourly activity (250 steps/hr)
- Health Metrics dashboard aggregating HRV, breathing rate, SpO2, skin-temp variation, RHR with 7/30-day personal ranges
- Menstrual health / cycle tracking (skin temp + logging)

**Insights / coaching (interpretation beyond raw numbers):**
- Daily Readiness verdict tailored to a personal baseline (built over 7 nights, refined ~30 days) rather than population norms
- Readiness breakdown: shows which factor (HRV / RHR / recent sleep) dragged the score up or down that day
- 'What to do today': a personalized daily activity goal plus recommended workouts on high-readiness days or recovery/active-recovery sessions on low-readiness days (Premium)
- Target Load range as an explicit optimal-training corridor: told when today's cardio load is below (undertraining) or above (overreaching) where it 'should' be
- Training Status coaching contextualizing acute vs chronic load (ACWR: last week vs last month) to balance performance, recovery and injury risk
- Stress score read as fewer/more physical signs of stress, with the three components explaining whether stress comes from body (Responsiveness), activity imbalance (Exertion Balance) or poor sleep (Sleep Patterns)
- Exertion Balance flags BOTH overexertion and too little exercise as stress drivers (two-sided balance)
- 'Sleep reservoir': a running 1-week bank of sleep quantity+quality that modulates stress/recovery guidance
- Sleep Profile monthly narrative + Sleep Animal benchmarking 10 sleep traits against ideal profiles with habit suggestions
- Cardio Fitness level bucketed vs same age/sex cohort, framed as a longevity/health indicator with guidance to raise it
- Restoration insight: how much of the night HR spent below RHR, read as recovery quality
- Health Metrics 'personal range' framing: your own normal band so you notice meaningful deviations, not absolute numbers
- Mindfulness / Mind & Body content, guided breathing (Relax) and mood logging tied to stress readings
- Premium adaptive coaching that dynamically adjusts training to prevent overtraining or under-recovery

**Prevention / early-warning:**
- Irregular Heart Rhythm Notifications: FDA-cleared background AFib screening from PPG heart-rhythm data during stillness/sleep (~98% agreement with ECG-patch confirmation)
- On-demand single-lead ECG app classifying AFib vs normal sinus rhythm
- High and Low heart-rate notifications flagging HR crossing personal thresholds at rest
- HRV drop as early warning: a significant fall in overnight HRV flagged as possible stress, strain or oncoming illness
- Elevated RHR over several days surfaced as body 'working harder to recover or fight illness'
- Skin-temperature-variation deviations positioned to catch fever onset (illness) and ovulation shifts
- SpO2 variation trends surfaced as possible signs of breathing disturbance or wellness change overnight
- Breathing-rate trend deviations as an additional illness / physiological-stress signal
- Health Metrics dashboard's core purpose: watch multiple vitals (HRV, breathing, SpO2, skin temp, RHR) drift outside personal range together as a composite early-warning of illness/stress/fatigue
- Readiness Score as an overtraining / under-recovery guardrail (low readiness = accumulated strain, poor sleep or stress)
- Target Load / Training Status explicitly warns of overreaching (load too high vs chronic) and detraining (load too low)
- Stress Management Score as a daily physiological-stress early-warning before it's consciously felt
- cEDA continuous skin-conductance to catch stress-response events across the day

**Methods + sensor inputs (what's reproducible from HR+RR):**
- Daily Readiness Score: weighted blend of overnight HRV + resting heart rate + recent (~7-day) sleep vs personal baseline. Inputs HR + RR (HRV) + sleep staging. REPRODUCIBLE FROM HR+RR (sleep component degrades without accelerometer but HR-only sleep estimation is workable).
- HRV: variation in beat-to-beat (RR) intervals during sleep, RMSSD-family in ms. Input RR intervals ONLY - directly reproducible from your beat-to-beat capture.
- Resting Heart Rate: lowest stable HR at rest, rolling personal baseline. Input HR only - reproducible.
- Breathing / respiratory rate: DERIVED from HRV (respiratory sinus arrhythmia in the RR series) during sleep. Input RR intervals - reproducible from your data, no separate sensor needed.
- Stress Management Score - Responsiveness /30: HRV + elevated RHR + sleeping HR above RHR + EDA (HR+RR reproduce all but the EDA term). Exertion Balance /40: steps/activity load (needs accelerometer/steps). Sleep Patterns /30: deep-sleep amount + fragmentation + sleep reservoir (needs sleep staging).
- Cardio Load: modified Banister TRIMP - duration in each HR zone exponentially weighted by intensity, using HR, HR-reserve, age, sex, RHR. Input HR (+profile). REPRODUCIBLE FROM HR alone; closest analog to WHOOP strain.
- Target Load / Training Status: Acute:Chronic Workload Ratio - last 7-day load vs last 28-day load, adjusted by readiness/recovery. Derived from Cardio Load history - reproducible.
- Cardio Fitness / VO2max: submaximal estimate from RHR, age, sex, weight (+ pace/HR relationship during GPS runs for a point value). Input HR + profile (+GPS optional) - reproducible as a range without GPS.
- Active Zone Minutes & HR zones: minutes in Fat Burn/Cardio/Peak from HR vs personalized max-HR / HR-reserve. Input HR only - reproducible.
- Sleep stages (light/deep/REM/awake): per-30-sec-epoch classification from accelerometer motion + HR/HRV patterns. Input accelerometer + HR/HRV - PARTIALLY reproducible (HR/HRV give REM/deep hints; accuracy drops without motion).
- Restoration sub-score: fraction of night with HR below RHR, combined with SpO2 and HRV. Input HR + RR reproduce most; SpO2 term missing.
- AFib / Irregular Rhythm: PPG tachogram analyzed for irregular beat-to-beat timing during stillness; sudden >10 bpm swings flagged. Input RR-interval irregularity - REPRODUCIBLE IN PRINCIPLE from beat-to-beat RR (exactly the signal AFib detection uses).
- ECG: single-lead electrical trace, on-demand. Input dedicated ECG electrodes - NOT reproducible from optical HR/RR.
- SpO2: red/infrared PPG ratio-of-ratios. Input dedicated multi-wavelength optical sensor - NOT reproducible (no validated SpO2).
- Skin temperature variation: on-wrist thermistor deviation vs personal baseline. Input temp sensor - NOT reproducible (no temp).
- EDA / cEDA: skin conductance via electrodes. Input EDA sensor - NOT reproducible.

**Sources:**
- https://support.google.com/fitbit/answer/14236710?hl=en
- https://www.tomsguide.com/news/fitbits-daily-readiness-score-helps-you-work-out-more-intuitively-and-im-here-for-it
- https://store.google.com/us/magazine/fitbit_daily_readiness_score?hl=en-US
- https://www.dcrainmaker.com/2021/11/fitbit-readiness-review.html
- https://blog.google/products-and-platforms/devices/fitbit/premium-daily-readiness/
- https://fitbit.google/enterprise/blog/prioritize-recovery-maximize-results-new-daily-readiness-score/
- https://www.androidcentral.com/what-fitbit-daily-readiness-score-and-how-do-i-use-it
- https://support.google.com/fitbit/answer/14236513
- https://support.google.com/fitbit/answer/14236712?hl=en
- https://www.androidpolice.com/fitbit-sleep-score-calculation-explainer/
- https://blog.google/products/fitbit/fitbit-sleep-premium-experience/
- https://www.androidauthority.com/fitbit-sleep-score-1111682/
- https://www.techadvisor.com/article/742445/fitbit-health-and-fitness-scores-and-stats-explained.html
- https://community.fitbit.com/t5/The-Pulse-Fitbit-Community-Blog/Learn-More-The-Stress-Management-Score-Part-2/ba-p/5398693
- https://www.myhealthyapple.com/complete-guide-to-fitbit-sense-stress-management-features/
- https://www.wareable.com/fitbit/fitbit-brings-stress-score-to-all-devices-8394
- https://www.kygo.app/post/pixel-watch-fitbit-stress-tracking-explained
- https://wellyhub.com/what-does-eda-mean-on-my-fitbit-a-guide-to-stress-tracking
- https://support.google.com/fitbit/answer/14236917?hl=en
- https://store.google.com/magazine/fitbit_health_metrics?hl=en-US
- https://www.wareable.com/fitbit/fitbit-health-metrics-explained-8248
- https://community.fitbit.com/t5/The-Pulse-Fitbit-Community-Blog/What-should-I-know-about-health-metrics-in-the-Fitbit-app/ba-p/5542412
- https://support.google.com/fitbit/answer/15402655?hl=en
- https://community.fitbit.com/t5/The-Pulse-Fitbit-Community-Blog/Daily-Readiness-Cardio-Load-and-Target-Load/ba-p/5660192
- https://www.androidcentral.com/wearables/fitbit-cardio-load-and-target-load-explained
- https://community.fitbit.com/t5/Charge-6/How-is-Cardio-load-calculated/td-p/5704967
- https://support.google.com/fitbit/answer/14236719?hl=en
- https://www.fitbit.com/global/us/technology/irregular-rhythm
- https://blog.google/products/fitbit/irregular-heart-rhythm-notifications/
- https://dev.fitbit.com/build/reference/web-api/cardio-fitness-score/get-vo2max-summary-by-date/
- https://www.myhealthyapple.com/cardio-fitness-level-on-fitbit/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6789195/
- https://www.businesswire.com/news/home/20200825005373/en/Fitbit-Debuts-Sense-Its-Most-Advanced-Health-Smartwatch-Worlds-First-With-EDA-Sensor-for-Stress-Management1-Plus-ECG-App2-SpO2-and-Skin-Temperature-Sensors
- https://www.fitabase.com/blog/post/hrv-spo2-br-data-available/

---

## Apple Health / Apple Fitness+ (Apple Watch ecosystem)
**Signature / why it's valuable:** The watchOS 11+ Vitals app: it learns each user's personal overnight baseline for heart rate, HRV, respiratory rate, wrist temperature, blood oxygen and sleep, then flags Outliers and — crucially — fires a single next-morning notification only when MULTIPLE metrics deviate together, naming probable causes (illness onset, alcohol, altitude, overtraining). Paired with Training Load's 7-day-vs-28-day strain-balance readout, this is Apple's WHOOP-style recovery/readiness + early-illness layer. Most of its INSIGHT logic (personal baseline + multi-metric outlier co-occurrence) is directly reproducible from HR + RR-intervals alone (RHR, HRV, RR-derived respiratory rate), even though two of Apple's five input signals — SpO2 and wrist temp — need sensors you don't yet have.

**Metrics surfaced:**
- Heart rate — live/current BPM (continuous PPG)
- Resting heart rate (daily, derived from background readings + accelerometer)
- Walking heart rate average
- Workout heart rate + heart rate zones (5 zones, personalized off HRR/max)
- Cardio recovery / heart rate recovery (BPM drop 1 min after workout ends)
- Cardio Fitness / VO2 max estimate (14–65 mL/kg/min, with Low/Below Avg/Above Avg/High category + 3-month trend)
- Heart rate variability (HRV, SDNN — surfaced in Health app and overnight in Vitals)
- Respiratory rate (breaths/min, tracked overnight and during Breathe)
- Blood oxygen / SpO2 (Series 6+, overnight and on-demand — sensor)
- Wrist temperature (overnight skin temp deviation from baseline — sensor)
- Sleep duration and time asleep vs time in bed
- Sleep stages: Awake, REM, Core (light), Deep + time in each
- Sleep Score (watchOS 26 / iOS 26 — 0–100 composite of duration, consistency, stages, wake events)
- Bedtime & wake consistency
- Breathing Disturbances (overnight, 30-day trend feeding sleep apnea notifications)
- Vitals overnight panel: heart rate, respiratory rate, wrist temperature, blood oxygen, sleep duration — each flagged Typical vs Outlier
- Training Load (7-day acute vs 28-day weighted average, classified Well Below/Below/Steady/Above/Well Above)
- Effort rating per workout (1–10, auto-estimated for cardio or manual)
- Activity rings: Move (active kcal), Exercise (minutes), Stand (hours)
- Active + total (resting) energy / calorimetry
- Steps, distance, flights climbed, walking speed/step length/asymmetry, double support %, 6-min walk distance
- Workout metrics: pace, cadence, running/cycling power (watts), splits, elevation, GPS route, custom pace/HR/power alerts
- AFib History (estimate of % of time in AFib for diagnosed users, weekly)
- ECG rhythm classification (Sinus / AFib / Low or High HR / Inconclusive — single-lead)
- State of Mind — momentary emotion + daily mood logging (very unpleasant → very pleasant scale + descriptors)
- Mindful minutes (Breathe / Reflect / meditation sessions)
- Time in Daylight
- Cycle tracking with wrist-temperature-based retrospective ovulation estimate

**Insights / coaching (interpretation beyond raw numbers):**
- Vitals morning summary: if MULTIPLE overnight metrics (HR, resp rate, wrist temp, SpO2, sleep) are simultaneous Outliers, a next-morning notification names likely causes (illness, alcohol, elevation, late workout, medication) — a recovery/readiness-style interpretation
- Personalized 'typical range' baseline learned per user over 7+ nights, so every metric is judged against YOUR normal, not a population number
- Training Load 7-day-vs-28-day comparison told back as 'ramping up / steady / easing off' with guidance to adjust or rest — an acute:chronic strain-balance readout
- Cardio Fitness category + notification when your VO2 max drops into Low, framed as a long-term cardiovascular-health signal
- Sleep Score with contributor breakdown and coaching to improve consistency/duration
- State of Mind correlations — shows how mood tracks against exercise, sleep, time in daylight, and mindful minutes (lifestyle→mood insight engine)
- Activity ring coaching, streaks, awards, customizable per-day goals, rest days, and weekly Fitness+ 'time to move' nudges
- Health app Trends: 90-day vs 365-day directional arrows on resting HR, HRV, VO2 max, sleep, cardio recovery etc. with up/down/steady interpretation
- Highlights cards in Health surfacing notable changes and comparisons automatically

**Prevention / early-warning:**
- Vitals Outlier detection — multi-metric overnight deviation flagged as a possible EARLY ILLNESS / stress / overtraining signal the next morning (Apple's marquee prevention feature; explicitly marketed for spotting when you're getting sick)
- Elevated wrist temperature as an early illness / infection / ovulation cue
- Irregular Rhythm Notification (IRN) — background PPG scans for irregular pulse suggestive of undiagnosed AFib, alerts after multiple confirming readings (FDA De Novo cleared)
- AFib History — for diagnosed users, tracks AFib burden over time with lifestyle-factor correlations
- High heart rate notification (above threshold while inactive 10+ min) and Low heart rate notification (bradycardia)
- Sleep Apnea notification — 30-day Breathing Disturbances trend flags possible moderate–severe OSA (FDA authorized)
- ECG app — on-demand single-lead rhythm check to catch AFib episodes
- Blood oxygen dips overnight as a respiratory/altitude warning
- Cardio Fitness low-VO2-max notification tied to elevated cardiovascular/all-cause mortality risk
- Training Load 'Well Above' classification as an overtraining / injury-risk / strain-recovery-imbalance early warning
- Fall Detection and Crash Detection (accelerometer/gyro) with emergency escalation

**Methods + sensor inputs (what's reproducible from HR+RR):**
- Cardio Fitness / VO2 max: physiological ODE model + deep neural network fusing HR + GPS pace/speed + demographics (age/sex/height/weight) during outdoor walk/run/hike ≥20 min; validated ~1.2 mL/kg/min. NEEDS motion/GPS pace — NOT reproducible from HR+RR alone (a submax HR-vs-pace estimate is partially replicable if you add accel/GPS).
- Cardio recovery / HRR: peak workout HR minus HR at 1 min post-workout (3-min post-workout HR monitoring). FULLY reproducible from HR alone — need only a marked workout-end timestamp.
- Resting HR: statistical minimum of background HR correlated with accelerometer to confirm inactivity. Reproducible from HR + a motion/quiet-window proxy.
- Walking HR average: HR gated to detected steady walking (needs accelerometer). Partial without accel.
- HRV (SDNN): computed from beat-to-beat RR intervals over short windows (esp. overnight and during Breathe). FULLY reproducible — this IS your HR + RR data; you can also compute RMSSD/pNN50/LF-HF.
- Irregular Rhythm / AFib PPG algorithm: measures inter-beat-interval tachograms from PPG peaks during stillness and classifies irregularity (higher beat-to-beat variability = AFib). CORE LOGIC REPRODUCIBLE from RR intervals — AFib detection is fundamentally an RR-irregularity classifier (Poincaré/entropy/RMSSD).
- ECG classification: single-lead electrical waveform via digital-crown circuit — sensor-specific, NOT reproducible from PPG HR/RR.
- Sleep stages: ML classifier on accelerometer motion + PPG heart rate/HRV patterns (respiration-induced motion, HR modulation). PARTIALLY reproducible — HR+RR give strong REM/deep/light signal (HRV differs by stage); wake detection weaker without accel. ~50–65% multi-state agreement vs PSG.
- Respiratory rate: derived from PPG/accelerometer during sleep (respiratory sinus arrhythmia in RR + motion). PARTIALLY reproducible — RR intervals carry respiratory modulation extractable via RSA/EDR.
- Sleep apnea / Breathing Disturbances: accelerometer-ONLY algorithm detecting breathing-related wrist micro-movement interruptions over 30 days (explicitly NOT SpO2). NOT reproducible from HR+RR — needs accelerometer.
- Training Load: Effort (1–10) × Duration; cardio effort auto-estimated from HR + GPS + elevation + demographics; 28-day exponentially weighted average vs 7-day acute. Reproducible from HR + workout metadata (manual RPE substitutes for strength).
- Blood oxygen: red/IR reflectance oximetry — dedicated SpO2 sensor, NOT reproducible from HR/RR.
- Wrist temperature: dedicated skin-temp sensors sampling overnight vs personal baseline — NOT reproducible from HR/RR.
- Calorimetry / active energy: HR + accelerometer + demographics regression. Partial without accel.
- State of Mind: pure self-report logging (no sensor); a correlation engine joins it to sensor + activity streams.
- Vitals Outlier engine: per-metric personal baseline (mean/SD over rolling nights) → Typical vs Outlier thresholding, then multi-metric co-occurrence triggers the morning notification. FULLY reproducible as a method — run the same baseline-and-outlier logic on any metric you compute (RHR, HRV, RR-derived resp rate).

**Sources:**
- https://www.apple.com/healthcare/docs/site/Using_Apple_Watch_to_Estimate_Cardio_Fitness_with_VO2_max.pdf
- https://www.empirical.health/blog/how-apple-watch-cardio-fitness-vo2max-works/
- https://www.empirical.health/blog/apple-watch-cardio-fitness-accuracy-vo2max/
- https://support.apple.com/en-us/108790
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12080799/
- https://support.apple.com/en-us/120277
- https://www.apple.com/health/pdf/Heart_Rate_Calorimetry_Activity_on_Apple_Watch_November_2024.pdf
- https://www.empirical.health/metrics/heart-rate-recovery/
- https://support.apple.com/en-us/120276
- https://support.apple.com/en-us/120278
- https://www.accessdata.fda.gov/cdrh_docs/reviews/DEN180042.pdf
- https://www.apple.com/legal/ifu/irnf/irn-ifu-2-en_US.pdf
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11694482/
- https://support.apple.com/en-us/120142
- https://www.centuryai.app/blog/apple-watch-vitals-app-explained
- https://www.xda-developers.com/guide-to-the-vitals-app-in-watchos-11/
- https://tidbits.com/2025/01/21/watchos-11s-vitals-app-may-detect-illness/
- https://www.wareable.com/apple/how-vitals-app-finally-makes-apple-watch-a-wellness-powerhouse
- https://www.apple.com/health/pdf/sleep-apnea/Sleep_Apnea_Notifications_on_Apple_Watch_September_2024.pdf
- https://9to5mac.com/2024/09/16/apple-details-how-apple-watch-accelerometer-based-sleep-apnea-feature-works/
- https://support.apple.com/guide/watch/receive-sleep-apnea-notifications-apd4e7713562/watchos
- https://www.apple.com/health/pdf/Estimating_Sleep_Stages_from_Apple_Watch_Oct_2025.pdf
- https://the5krunner.com/2025/10/06/how-apple-watchs-sleep-score-is-calculated-all-you-need-to-know-to-improve-sleep-health/
- https://academic.oup.com/sleep/article/42/12/zsz180/5549536
- https://support.apple.com/guide/watch/track-your-training-load-apde4c07a6cf/watchos
- https://www.apple.com/newsroom/2024/06/watchos-11-brings-powerful-health-and-fitness-insights/
- https://www.dcrainmaker.com/2024/07/apples-training-load-vitals-watchos11.html
- https://www.tomsguide.com/wellness/smartwatches/im-a-marathoner-and-have-been-testing-apple-watchs-training-load-feature-heres-the-pros-and-cons
- https://support.apple.com/guide/watch/log-your-state-of-mind-apd7de0f5610/watchos
- https://en.wikipedia.org/wiki/Mindfulness_(Apple)
- https://9to5mac.com/2024/05/01/track-mood-on-apple-watch-how-to/
- https://www.apple.com/apple-fitness-plus/
- https://support.apple.com/guide/fitness-plus/listen-audio-workouts-guided-meditations-apd9ee1c00c4/ios

---
