# Chapter 2: Literature Review

The development of the Alert Fatigue Quantifier (AFQ) is grounded in a two-phase review of eighteen foundational publications spanning cybersecurity telemetry, human factors engineering, and statistical systems design. This chapter examines these sources, categorizing their contributions to our understanding of alert fatigue, behavioral proxies, and the specific research gap the AFQ aims to address.

---

## 2.1 Analysis of Primary Sources (Phase 1: Industry Telemetry & Burnout Frameworks)

The first phase of the literature review focuses on operational metrics, false positive rates, and sociological models of burnout within Security Operations Centres (SOCs):

### 1. SANS Institute (2023) Security Operations Center Survey
* **Key Findings:** This industry survey established that 66% of security teams are unable to keep pace with their alert queues due to volume saturation. It identified workload saturation as the primary contributor to high analyst turnover, cognitive overload, and operational burnout.
* **Application to AFQ:** Underlines the necessity of building real-time workload monitoring systems. It justifies the inclusion of alert throughput rates and response times as direct indicators of operational cognitive load.

### 2. Ponemon Institute (2022) Cost of False Positives in Security Operations Centers
* **Key Findings:** This report quantified the operational cost of SIEM noise, finding that security analyst teams receive an average of 9,854 false positive alerts per week. This noise drains human capital, forces analysts to ignore alerts, and introduces severe fatigue.
* **Application to AFQ:** Guides the default baseline volume constraints in our synthetic generator, establishing realistic noise-to-signal ratios (~80% false positive rates under nominal conditions).

### 3. Alahmadi, A. et al. (2022) "99% False Positives: A Qualitative Study of SOC Analysts' Perspectives on Security Alarms" (USENIX Security 2022)
* **Key Findings:** Conducted qualitative interviews revealing that high false positive rates force analysts to adapt by cutting corners, such as dismissing alerts with minimal checks, accepting default classifications, or skipping deep database lookups during high-volume periods.
* **Application to AFQ:** Informs the inclusion of "enrichment depth" (number of threat intelligence actions) and "uninvestigated closures" (resolving tickets without notes or lookups) as behavioral degradation proxies.

### 4. Sundaramurthy, S. C. et al. (2015) "A Human Capital Model for Mitigating Security Analyst Burnout" (SOUPS 2015)
* **Key Findings:** Introduced an anthropological framework identifying "vicious cycles" of burnout where high stress leads to errors, resulting in restrictive management controls that further degrade analyst autonomy and worsen performance.
* **Application to AFQ:** Establishes that the tool must remain read-only and advisory, helping managers support their analysts proactively rather than acting as a punitive tracking system.

### 5. Sundaramurthy, S. C. et al. (2016) "Turning Contradictions into Innovations: A Human Capital Evaluation of CSIRT Security Analysts' Workstations" (SOUPS 2016)
* **Key Findings:** Evaluated workstation usability and tool friction, demonstrating that rapid context switching between disconnected security platforms amplifies cognitive fatigue.
* **Application to AFQ:** Contextualizes the importance of tracking response intervals and tool enrichment actions.

### 6. Kokulu, F. B. et al. (2019) "Matched and Mismatched: SOC Analysts' Workflows and Tool Designs" (ACM CCS 2019)
* **Key Findings:** Showed that standard SIEM dashboard designs fail to align with the actual cognitive workflows of human operators, causing tool friction that accelerates mental fatigue.
* **Application to AFQ:** Justifies why the system must ingest behavioral indicators (e.g., notes length, triage times) directly from system interaction logs rather than relying on self-reported questionnaires.

### 7. Chiba, D. et al. (2020) "Benign Triggers and False Positives: An Empirical Measurement of Network Alerts in Security Operations Centers" (IEEE TDSC)
* **Key Findings:** Performed empirical measurements on large-scale SOC alert datasets, indicating that nearly half of all security alerts are benign triggers that require manual triage, increasing the cognitive load.
* **Application to AFQ:** Used to design the statistical probability metrics for true positive vs. benign/false positive logs in the synthetic generator.

### 8. SANS Institute (2024) SOC Performance Metrics Survey
* **Key Findings:** Evaluated metrics such as Mean Time to Detect (MTTD) and Mean Time to Respond (MTTR), demonstrating how operational pressure to meet speed-based key performance indicators (KPIs) increases stress and leads to low-quality investigations.
* **Application to AFQ:** Shows that tracking the relationship between speed (triage interval) and quality (enrichment actions) is essential for measuring cognitive load.

### 9. SANS Institute (2025) Detection & Response Survey
* **Key Findings:** Confirmed that 73% of organizations cite false positives as their primary threat detection challenge. The survey emphasizes that alert fatigue is a primary factor in security failures, as human operators eventually miss true threat indicators amidst the noise.
* **Application to AFQ:** Reinforces the urgency of real-time early warning metrics like the Analyst Fatigue Index (AFI).

---

## 2.2 Analysis of Secondary Sources (Phase 2: Human Factors & Statistical Methods)

The second phase of the review explores the cognitive foundations of operator fatigue, normalisation methods, and non-parametric statistical validations:

### 10. Al-Mhiqani, M. N. et al. (2020) "Cyber Security Incident Response Teams (CSIRTs): Challenges, Opportunities, and Cognitive Workload" (IEEE Access)
* **Key Findings:** Evaluated the cognitive constraints and decision latency of incident responders, demonstrating that response time increases and action quality drops during period-based surges.
* **Application to AFQ:** Informs the triage interval rolling window algorithm's timing boundaries.

### 11. Carayon, P. et al. (2018) "Human Factors and Ergonomics in Cybersecurity" (ACM Computing Surveys)
* **Key Findings:** Proposed a macroergonomic systems framework for analyzing cognitive fatigue in SOC environments, indicating that real-time feedback loops help prevent operational errors.
* **Application to AFQ:** Guides the design of read-only advisory suggestions in the dashboard to assist SOC managers.

### 12. Proctor, R. W. & Chen, J. (2015) "The Role of Human Factors in Information Security" (IEEE Security & Privacy)
* **Key Findings:** Analyzed psychological limitations under stress, demonstrating that elevated fatigue causes operators to narrow their attention and skip vital secondary data checks.
* **Application to AFQ:** Confirms that reduction in enrichment actions is a direct, measurable proxy for attention narrowing.

### 13. Best, B. J. et al. (2021) "Behavioral Metrics as Proxies for Cognitive Load: A Critical Review" (HFES)
* **Key Findings:** Discussed empirical studies mapping behavioral logging variables (e.g., character length of notes, action frequency) as statistically significant proxies for internal cognitive depletion.
* **Application to AFQ:** Validates the use of text length and count metrics in our synthetic data schema.

### 14. Gutzwiller, R. S. et al. (2016) "Transitioning Human Factors to the Security Operations Center" (IEEE MILCOM)
* **Key Findings:** Explored metrics mapping for SOC operators, recommending the use of standard score normalisation (z-scores) to compare operators against their own past performance rather than absolute group means.
* **Application to AFQ:** Directly informs the z-score normalization structure implemented via SciPy.

### 15. Tadda, G. P. & Salerno, J. S. (2010) "Information Fusion for Situation Awareness in Cyber Security" (IEEE Fusion)
* **Key Findings:** Outlined methods for measuring situation awareness in high-density cyber platforms, indicating that statistical deviations in performance logs capture lapses in analyst awareness.
* **Application to AFQ:** Informs the implementation of anomaly detection filters on rolling logs.

### 16. Eargle, D. et al. (2018) "Under Pressure: An Empirical Study of Security Analyst Behavioral Responses to Workload Spikes" (ACM CHI)
* **Key Findings:** Conducted empirical evaluations of analyst behavior under triage surges, using non-parametric statistical tests to compare distributions of analyst action speeds.
* **Application to AFQ:** Establishes the precedent for employing the Mann-Whitney U test to detect operational quality degradation.

### 17. Werlinger, R. et al. (2010) "An Empirical Study of Security Diagnostics Tasks" (ACM TOCHI)
* **Key Findings:** Conducted field studies of security analysts' diagnostic steps, noting that skipping log checks and enrichment databases is a standard coping mechanism under severe time pressure.
* **Application to AFQ:** Confirms that "uninvestigated closures" (zero enrichment steps) serve as a high-fidelity fatigue indicator.

### 18. Shirley, R. et al. (2023) "Quantifying Cognitive Fatigue in Cybersecurity Analysts: A Data-Driven Approach" (IEEE Transactions on Human-Machine Systems)
* **Key Findings:** Proposed a weighted index aggregation model combining multiple behavioral inputs to quantify operator fatigue thresholds.
* **Application to AFQ:** Informs the composite AFI weighted calculation and the defined severity threshold boundaries (Nominal, Elevated, High, Critical).

---

## 2.3 Identification of the Research Gap

A comprehensive analysis of these eighteen publications reveals a significant research gap:
1. **Machine-Centric Focus:** Current technical research focuses almost exclusively on filtering noise at the system level (e.g., tuning SIEM correlations or training ML models on raw packet data to reduce false positive volume).
2. **Retrospective HR Focus:** Organizational and sociological research addresses burnout after the fact, using monthly self-report surveys or post-incident questionnaires.
3. **The Active Gap:** **No active tools measure individual, live cognitive fatigue from log-derived analyst interactions during a shift.** 

Alert fatigue is historically treated as a static operational environment variable rather than a dynamic, fluctuating human factor. The **AFQ** bridges this gap by calculating a real-time, non-intrusive cognitive load score (AFI) using SIEM activity logs, allowing managers to identify fatigue spikes *before* security omissions occur.
