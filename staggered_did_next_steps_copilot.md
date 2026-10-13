# Call-Center Education Program — Next Steps for Copilot

## Context and current result

The business offers voluntary education during inbound calls. Agents record **completed** education sessions, including customer, timestamp, topic and department, but offers declined and detailed call reasons are generally unavailable. The main business outcomes are inbound call volume and bill payment activity; overall program effect is primary, with topic and historical calling-frequency segments as complements.

Work environment: **Azure Databricks, Spark SQL and PySpark**. The user has built a preliminary **daily-cohort, 30-day pre/post DiD** pipeline:

1. `first_education`: earliest recorded education per customer, selected using `ROW_NUMBER`; subsequent education remains part of program exposure.
2. `treated_customers`: one row per customer, with `cohort_date`, first department/topic, FY25 numerical call count and categorical calling-frequency segment.
3. `eligible_controls`: customers who called the same department on the cohort date and whose first education is either null or **after cohort_date + 30 days**; a customer may be a control for multiple earlier cohorts.
4. `analysis_population`: treated and control customer–cohort records.
5. `customer_call_volume` / `customer_changes`: distinct inbound calls on days -30…-1 and +1…+30, excluding day 0; `call_change = post - pre`.
6. `cohort_att`: for each cohort date/department, mean treated change minus mean control change.
7. Overall sample-size-weighted ATT: `SUM(n_treated * att_30d) / SUM(n_treated)`.

**Preliminary overall result: -0.19 inbound calls per educated customer over 30 days.** This is an **unadjusted observational cohort DiD**, not yet the complete Callaway–Sant’Anna (CS) estimator, and no reliable causal or statistical-significance claim should be made yet.

## Mission

Continue **from the existing tables and results**; do not regenerate the completed pipeline unless needed to fix errors. Work step-by-step, display data quality outputs, and pause at substantive design decisions. Use Spark for data engineering. Prefer a validated statistical implementation (e.g. R `did` and `DRDID`) for formal CS estimation and bootstrap inference. Do not pretend that a simple SQL difference-in-differences or per-cohort linear regression is already a complete doubly robust CS estimator.

## Phase 1 — Audit existing estimate and population (do this first)

### Checks

- Confirm one row per treated customer; at most one row per `customer_id, cohort_date, department, treated` in the analysis population.
- Test whether customers called multiple departments on a cohort date; avoid counting the same treated customer multiple times in overall aggregations.
- Confirm 30 full days of historical and future data for every included cohort; don't misinterpret data censoring as zero calls.
- Ensure first-education coverage extends through the end of each observed outcome window. A null first-education date means **no recorded education**, not necessarily confirmed rejection of an offer.
- Verify call identifiers are uniquely deduplicated across transfers and department handoffs; check if `COUNT(DISTINCT call_id)` actually represents unique inbound contacts.
- Count treated customers/cohorts included vs excluded because of missing controls, missing customer covariates, incomplete follow-up, or sparse strata. Define the target estimand/population clearly.
- Show unweighted pre/post changes and cohort-size-weighted ATT, control sample sizes, department composition, and sensitivity to outlier cohorts.
- Check FY25 fiscal-year boundaries and confirm historical counts precede treatment (avoid post-treatment covariates).
- Ensure no education/index call is counted on Day 0; consider whether excluding Day 0 changes the target outcome meaningfully.

### Example audit code (adapt to actual schema)

```python
spark.sql("""
SELECT cohort_date, department, treated, customer_id, COUNT(*) AS n
FROM analysis_population
GROUP BY cohort_date, department, treated, customer_id
HAVING COUNT(*) > 1
""").show()

spark.sql("""
SELECT
    COUNT(*) AS cohort_department_cells,
    SUM(n_treated) AS included_treated,
    MIN(n_controls) AS min_controls,
    PERCENTILE_APPROX(n_controls, 0.5) AS median_controls,
    SUM(n_treated * att_30d) / SUM(n_treated) AS weighted_att
FROM cohort_att
""").show()

spark.sql("""
SELECT treated,
       COUNT(*) AS customer_cohort_rows,
       AVG(pre_30d_calls) AS avg_pre,
       AVG(post_30d_calls) AS avg_post,
       AVG(post_30d_calls - pre_30d_calls) AS avg_change,
       AVG(fy25_call_count) AS avg_fy25_calls
FROM customer_call_volume
GROUP BY treated
""").show()
```

**Caveat:** Directly pooling reused control rows in the third query is a *diagnostic*, not the final ATT or an independent-customer average.

## Phase 2 — Assess treated/control comparability and overlap

At minimum compare baseline numerical FY25 call count, call-frequency segment, recent pre-index 30-day call volume, earlier call trend, historical bill payment frequency, customer tenure/product holdings (if available), department and calendar date. Use **only pre-index** covariates. Report standardized mean differences (SMD) and distribution plots; compare treatment propensity distributions where applicable. Investigate sparse cohorts and lack of common support.

Historical call-frequency `fy25_call_count` remains numeric for adjustment; `call_frequency_segment` is for subgroup reporting. Avoid putting only the categorical bucket into the adjustment model when the numeric count is available. Use log1p for skewed counts if appropriate. **No future information** should enter a predictor.

Document likely selection bias: education is opt-in; unknown offer/decline status and limited call-reason detail restrict exchangeability. Department is only a rough proxy for reason for calling. Call-center inbound contacts can be followed by **regression to the mean**, so align control index events to comparable inbound calls and inspect pre-index trends.

## Phase 3 — Build formal time panel and event-study diagnostics

Choose a consistent **calendar time** unit for group-time estimation. Options:

- **Daily**: preserve precise treatment day but potentially very large panel, sparse daily call counts and many cohort-time cells.
- **Weekly**: manageable panel but define education week consistently; avoid counting exposure inside the same calendar week as wholly untreated. Consider dropping transition week or setting clearly defined timing conventions.

Start with 8–12 weeks (or longer if available) before treatment and 4–8 weeks after, ensuring full support by cohort. Every eligible customer-period must appear **including zero-outcome periods**. Build `customer_id, calendar_period, first_treat_period (0 if never), calls, bill_payments, pre_treatment_covariates`; retain a reference population and program eligibility status.

Important: The formal CS `att_gt` implementation ordinarily compares cohorts on a **common calendar-period panel**, rather than naively feeding duplicated customer×cohort records from the same-day-matched SQL table. Our same-day/department inbound control rule needs an explicit identification strategy: potentially define an eligible study population from comparable inbound interactions, use baseline covariates, and/or estimate separate department-specific designs. **Do not pass the duplicated `analysis_population` into `att_gt` as if its rows were unique customers.** Work out this mapping before running the estimator.

For a descriptive plot, produce untreated and treated pre-index weekly calling trajectories and SMDs; recognize that visual parallel pre-trends are not proof of conditional parallel trends.

## Phase 4 — Formal Callaway–Sant’Anna group-time estimation

Target `ATT(g,t)`, where `g` is the first treated calendar period and `t` is outcome calendar period. Use **never-treated and/or not-yet-treated** controls, not already treated customers. By default, for post-treatment effects use the last period before treatment as the common baseline; CS `base_period = "universal"` also makes pre-period event-study contrasts relative to a common reference. Pre-period diagnostics may use a varying base with other settings.

Prefer **doubly robust DiD** (outcome regression + propensity score) because groups differ in observed baseline behaviour. It is consistent if either nuisance model is correctly specified *under appropriate identification and overlap assumptions*. It **cannot fix unobserved voluntary participation bias**. Evaluate sample support and stability; daily cohorts may require sensible aggregation to weekly/monthly cohorts.

Illustrative **R `did` code** (template, not runnable until panel fields/timing and study population are validated):

```r
library(did)

att <- att_gt(
  yname = "calls",
  tname = "calendar_period_id",
  idname = "customer_id",
  gname = "first_treat_period_id",  # zero = never treated
  xformla = ~ log1p(fy25_call_count) + baseline_30d_calls + department,
  data = panel_df,
  panel = TRUE,
  control_group = "notyettreated",
  est_method = "dr",
  base_period = "universal",
  bstrap = TRUE,
  cband = TRUE,
  clustervars = "customer_id"
)

summary(att)

dyn <- aggte(att, type = "dynamic", min_e = -8, max_e = 8)
summary(dyn)
ggdid(dyn)

simple <- aggte(att, type = "simple")
summary(simple)
```

Ensure `calendar_period_id` and `first_treat_period_id` are coherent common-period integer indices and an appropriate feasible `gname` coding. Confirm package version/API and clustering support in current official docs before final code. Do not assume the `simple` aggregate equals the 30-day cumulative business KPI.

### Critical distinction: business 30-day calls versus event-study outcomes

Our existing `ATT_30d = (calls days 1–30 minus calls days -30…-1) treated minus control` is a **30-day cumulative pre/post count contrast**, with Day 0 omitted. Standard `aggte(type="dynamic")` applied to **daily/weekly call counts** yields period-level effect on the daily/weekly outcome, not directly 30-day cumulative calls avoided. For a 30-day total:

- Define a 30-day cumulative outcome/estimand explicitly, or
- Sum appropriately aligned **nonoverlapping daily effects** over days +1…+30 only if they share a coherent target population, treatment reference, comparison strategy and cohort weighting, with uncertainty derived for the sum (not by summing marginal confidence limits).

Do not sum overlapping 7/14/21/30-day cumulative estimates. Do not treat equal-length changing pre/post windows as automatically a standard CS event study.

### Suggested additional outputs

- `ATT(g,t)` with cohort-size and support counts.
- Dynamic effects at event weeks -8…+8; plot pre-period estimates and post-treatment response, with simultaneous confidence bands if appropriate.
- The business-aligned 30-day cumulative effect and confidence interval.
- Cohort-size-weighted overall estimate on a clearly stated supported cohort population.

## Phase 5 — Inference and sensitivity

- Use bootstrap / valid clustered standard errors accounting for repeated customer outcomes and reused controls. Prefer inference supported by the estimator, rather than treating control row reuse as independent observations.
- Consider multiple-testing and simultaneous confidence bands for dynamic event-study points.
- Check common support, weighting extremes, and cohort sizes. Avoid inferring “no effect” from a wide CI.
- Test alternative comparison definitions: never-treated only vs not-yet-treated; same department and same-day vs ±few-day index alignment; richer baseline adjustment; alternative frequency segmentation.
- Test 7/14/21/30-day separately defined business outcomes. Keep horizon-specific eligibility and windows consistent.
- Explore whether other education sessions or new campaigns during follow-up may affect outcome interpretation (the primary estimand includes subsequent program exposure).
- Consider seasonality, bill-payment cycles, holidays, operational disruptions, policy changes, and pre-treatment spikes in calling (regression to the mean).
- Quantify exclusion rates under alternative data-completeness and cohort-support thresholds.

## Phase 6 — Topic/segment analyses and reporting

**Primary:** adjusted overall 30-day call effect per educated customer plus confidence interval, raw treated change and control baseline change, treated sample size, and assumptions.

**Secondary:** bill payments and digital self-service metrics, customer call-frequency segment effects, departments, and first-education-topic descriptive patterns. For segment-specific ATT, estimate within segment or with a valid heterogeneity-aware procedure; do **not** simply assign the overall ATT to each segment. Topic results need care because customers can receive multiple topics; do not claim isolated topic causal effects by merely stratifying on first topic.

Translate to an illustrative number of calls avoided as `(-ATT_30d) × number of represented treated customers`; apply validated handling cost only with a clearly labeled estimated operational-value scenario. Avoid double counting, extrapolating to excluded cohorts, and claiming realized savings.

## Requested Copilot interaction style

1. Start by asking for the actual schema/row counts only when necessary; prefer mapping to current views.
2. Audit the existing **-0.19** result first and produce reproducible validation queries.
3. Explain each analytical decision briefly, then provide executable Databricks SQL/PySpark cells.
4. **Do not write the entire remaining pipeline at once.** Implement one phase, validate its output, then proceed.
5. Keep code scalable for large call-level tables; pre-aggregate when practical, use partition pruning and avoid giant customer×cohort Cartesian joins.
6. Clearly label estimates as descriptive, unadjusted DiD, regression-adjusted DiD, or formal CS-DR-DiD.

## Immediate next task

**Begin with Phase 1:** write a compact series of Spark SQL data-quality checks for `treated_customers`, `eligible_controls`, `analysis_population`, `customer_call_volume`, and `cohort_att`; identify any logical or population-coverage risks that could change the preliminary **-0.19** ATT. Then propose the smallest correction needed before progressing to the formal estimator.
