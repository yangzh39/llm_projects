# Copilot Project Brief: Call-Center Education Program — Staggered DiD

## Your role
Act as a senior causal-inference data scientist and Azure Databricks/Spark SQL engineer. Help implement the evaluation **incrementally**, validate intermediate tables, and distinguish a practical cohort DiD prototype from a formal Callaway–Sant'Anna (2021) group-time estimator. Do not claim observational comparisons prove causality.

## Business context
Inbound call-center agents offer customer education on different banking topics (bill payments, digital banking, fraud, etc.). Customers may accept or decline. Agents manually log **completed education sessions**, not offers/declines or outcomes. Customers may receive multiple sessions across topics. Business priorities: (1) overall effect on subsequent inbound calls and bill-payment behavior; (2) secondary reporting by first education topic, department, and historical call-frequency segment. There is no randomized treatment assignment and detailed call reason is unavailable; **inbound department** is a rough proxy for comparability.

## Decisions already made
- Define first recorded education as each customer's sole **first-treatment date**, with absorbing exposure thereafter; subsequent sessions are part of overall program exposure (not separately attributed in primary ATT).
- Daily first-treatment cohorts; use common calendar periods for formal group-time analysis.
- Initial business KPI: cumulative **calls per customer during Days +1 to +30 versus Days -30 to -1**, excluding Day 0; count DISTINCT call IDs because transfers may duplicate rows. Produce analogous bill-payment outcomes, counting valid successful payments.
- Initial controls: customers with a comparable inbound call **on the index/cohort date and in the same department**, who are untreated at that date and remain untreated through Day +30 for the fixed-window comparison. A control can be reused in multiple earlier cohorts and later receive treatment; never use already-treated customers as untreated controls. Department/index matching is a working assumption, not intrinsic to Callaway–Sant'Anna.
- For a formal period-specific comparison at time t, use eligible not-yet-treated or never-treated controls at t; do not apply the fixed Day +30 eligibility filter indiscriminately.
- Historical FY25 call count (`fy25_call_count`) is a **numeric count** for covariate adjustment; `call_frequency_segment` is a categorical label for subgroup analyses. Examine count distribution and choose transparent cutoffs; preserve 0/1-call customers. Ensure FY25 is before program initiation; otherwise build covariates strictly before each customer's treatment/control index.
- Compare controls and treated on pre-period calls, historical bill payments, customer tenure, products/segment, and department. Check overlap, pre-trends, sensitivity, uncertainty. Voluntary opt-in creates selection concerns that DiD/DR alone cannot fully remove.
- The practical 30-day cohort DiD is **not** automatically the formal Callaway–Sant'Anna estimator. Formal approach estimates `ATT(g,t)` using a common pre-treatment reference for each treated cohort, valid comparison cohorts, optional doubly robust covariate adjustment, then aggregates group-time estimates. A 7/14/21/30-day sliding equal-length pre/post analysis gives different cumulative-window estimands, **not** a standard dynamic event study.

## Expected raw sources (rename in code for my environment)
`education_sessions(customer_id, education_timestamp, session_id, education_topic, department)`
`inbound_calls(customer_id, call_id, call_timestamp, department)`
`bill_payments(customer_id, transaction_id, transaction_timestamp, payment_channel, transaction_status, payment_amount)`
`customer_universe(customer_id, ...customer-profile covariates...)`

Assume these are Spark tables/views. Treat timestamps carefully (business time zone), normalize date values, confirm observation horizon/data completeness, and index by distinct **customer + cohort date + comparison department**, with one treated record per customer.

## Phase A: Build an auditable fixed-window cohort DiD prototype (Spark SQL)

### A1 — First education per customer (deterministic)
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW first_education AS
SELECT customer_id,
       CAST(education_timestamp AS DATE) AS first_education_date,
       department, education_topic
FROM (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY education_timestamp, session_id
  ) AS rn
  FROM education_sessions
) s
WHERE rn = 1
""")
```

### A2 — FY25 numerical call count, including customers with zero calls
**Replace the following FY25 date boundaries with the bank's true fiscal calendar; illustrative only.**
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW customer_baseline AS
SELECT u.customer_id,
       COALESCE(h.fy25_call_count, 0) AS fy25_call_count
FROM customer_universe u
LEFT JOIN (
  SELECT customer_id, COUNT(DISTINCT call_id) AS fy25_call_count
  FROM inbound_calls
  WHERE CAST(call_timestamp AS DATE) >= DATE '2024-11-01'
    AND CAST(call_timestamp AS DATE) <  DATE '2025-11-01'
  GROUP BY customer_id
) h ON u.customer_id = h.customer_id
""")

spark.sql("""
SELECT fy25_call_count, COUNT(*) AS n_customers
FROM customer_baseline GROUP BY fy25_call_count
ORDER BY fy25_call_count
""").show(100)
```
Choose frequency boundaries **after examining the actual counts/ties**. Placeholder cutoffs:
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW customer_segments AS
SELECT customer_id, fy25_call_count,
 CASE WHEN fy25_call_count <= 1 THEN 'Low'
      WHEN fy25_call_count <= 5 THEN 'Medium'
      ELSE 'High' END AS call_frequency_segment
FROM customer_baseline
""")
```

### A3 — Daily treated cohort table
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW treated_customers AS
SELECT e.customer_id, e.first_education_date AS cohort_date,
       e.department, e.education_topic,
       s.fy25_call_count, s.call_frequency_segment
FROM first_education e JOIN customer_segments s
  ON e.customer_id = s.customer_id
""")
```

### A4 — Eligible controls for a fixed 30-day comparison
Require a documented definition of comparable index interaction; this example uses **same department, same calendar date**. Verify full follow-up coverage and appropriate customer eligibility.
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW eligible_controls AS
SELECT DISTINCT g.cohort_date, g.department, c.customer_id,
       s.fy25_call_count, s.call_frequency_segment
FROM (SELECT DISTINCT cohort_date, department FROM treated_customers) g
JOIN (
  SELECT DISTINCT customer_id, CAST(call_timestamp AS DATE) AS call_date, department
  FROM inbound_calls
) c
  ON c.call_date = g.cohort_date AND c.department = g.department
JOIN customer_segments s ON c.customer_id = s.customer_id
LEFT JOIN first_education e ON c.customer_id = e.customer_id
WHERE e.first_education_date IS NULL
   OR e.first_education_date > DATE_ADD(g.cohort_date, 30)
""")
```
The `DISTINCT` makes control records unique **per cohort, department, customer**, not globally. A customer may be control in multiple earlier cohorts. Handle customers calling multiple departments on the same date carefully so overall counts/weights are not inadvertently duplicated. Validate exclusion of any treated individual from control status within the same cohort.

### A5 — Combine analysis population and calculate call outcomes
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW analysis_population AS
SELECT customer_id, cohort_date, department, fy25_call_count,
       call_frequency_segment, 1 AS treated
FROM treated_customers
UNION ALL
SELECT customer_id, cohort_date, department, fy25_call_count,
       call_frequency_segment, 0 AS treated
FROM eligible_controls
""")

spark.sql("""
CREATE OR REPLACE TEMP VIEW customer_call_volume AS
SELECT p.customer_id, p.cohort_date, p.department, p.treated,
       p.fy25_call_count, p.call_frequency_segment,
       COUNT(DISTINCT CASE
         WHEN CAST(c.call_timestamp AS DATE) >= DATE_SUB(p.cohort_date, 30)
          AND CAST(c.call_timestamp AS DATE) < p.cohort_date
         THEN c.call_id END) AS pre_30d_calls,
       COUNT(DISTINCT CASE
         WHEN CAST(c.call_timestamp AS DATE) > p.cohort_date
          AND CAST(c.call_timestamp AS DATE) <= DATE_ADD(p.cohort_date, 30)
         THEN c.call_id END) AS post_30d_calls
FROM analysis_population p
LEFT JOIN inbound_calls c
  ON c.customer_id = p.customer_id
 AND CAST(c.call_timestamp AS DATE) BETWEEN DATE_SUB(p.cohort_date,30)
                                           AND DATE_ADD(p.cohort_date,30)
GROUP BY p.customer_id, p.cohort_date, p.department, p.treated,
         p.fy25_call_count, p.call_frequency_segment
""")
```
**Day 0 is intentionally excluded** to avoid the index inbound/education call contaminating either period. Call outcome counts are across all inbound departments, while index department is used to form comparisons. Duplicate call records due to transfers are deduplicated by `call_id`. Use pre-aggregated customer-day call counts when raw call records are large.

### A6 — Unadjusted cohort DiD and aggregation
```python
spark.sql("""
CREATE OR REPLACE TEMP VIEW cohort_changes AS
SELECT cohort_date, department, treated,
       COUNT(*) AS n_customers,
       AVG(post_30d_calls - pre_30d_calls) AS avg_change
FROM customer_call_volume
GROUP BY cohort_date, department, treated
""")

spark.sql("""
CREATE OR REPLACE TEMP VIEW cohort_att AS
SELECT t.cohort_date, t.department, t.n_customers AS n_treated,
       t.avg_change AS treated_change,
       c.avg_change AS control_change,
       t.avg_change - c.avg_change AS att_30d
FROM cohort_changes t JOIN cohort_changes c
 ON t.cohort_date = c.cohort_date
AND t.department = c.department
WHERE t.treated = 1 AND c.treated = 0
""")

spark.sql("""
SELECT SUM(n_treated * att_30d) / SUM(n_treated) AS overall_att_30d,
       SUM(n_treated) AS n_treated_in_estimable_cohorts
FROM cohort_att
""").show()
```
Cohorts with no controls are dropped by the inner join: report their count and characteristics; do not conceal missing support. This unadjusted result assumes comparable trends and has **no valid confidence interval yet**. Treat as exploratory, not definitive.

### A7 — Numerical adjustment / heterogeneity (next iteration)
Use the actual historical call count (perhaps `log1p`) and pre-index call activity as **pre-treatment** covariates in an appropriate estimator. Use segment labels for subgroup ATT reports; **do not merely append a segment column to the overall cohort ATT and pretend it estimates segment-specific effects**. Estimate within strata or model heterogeneous effects explicitly. Check covariate overlap and sparse per-day cohorts. Avoid treating predictions of untreated outcomes as individual known causal effects.

### A8 — Additional outcome: bill payments
Build analogous distinct-successful-payment counts over same windows with a separate pre-aggregation. Specify whether the KPI is transaction count, digital share, payment amount, or customer activity; each has a different estimand. Join aggregated payments to `analysis_population` by customer/cohort rather than joining raw calls and raw payments simultaneously (which creates a multiplicative join).

## Phase B: Full Callaway–Sant'Anna estimation

### B1 — Customer-calendar-day (or consistently defined week) panel
For all eligible customers and periods, construct:
```
customer_id | period_id | first_treat_period | daily_calls | ...baseline covariates
```
- `first_treat_period` is first education period, `0` for never-treated in the R `did` convention.
- Complete zero-call observations; define coherent calendar period IDs for treated dates and outcomes.
- Choose a common, well-defined analysis population and eligible risk sets; **the standard `did` function does not automatically implement same-day inbound-call index matching or department-specific risk sets**. Do not silently replace our design with all uneducated customers.
- For daily adoption, `ATT(g,t)` estimates changes in **daily call outcomes** relative to a cohort's last pre-treatment period; to make the primary 30-day cumulative calls KPI comparable, construct/aggregate period effects with careful handling of non-overlapping outcome intervals, stable cohorts and weights. Avoid adding overlapping cumulative estimates.
- For controls, avoid using a customer's post-treatment records as untreated. Examine data restrictions from exact index-date sampling, anticipation, treatment timing and complete horizon.

### B2 — Illustrative R estimator (requires correctly constructed population/panel)
```r
library(did)
# customer_panel: one row per customer × calendar period,
# period_id and first_treat_period on the SAME period scale;
# first_treat_period = 0 for never-treated.
fit <- att_gt(
  yname = "daily_calls",
  tname = "period_id",
  idname = "customer_id",
  gname = "first_treat_period",
  xformla = ~ log1p(fy25_call_count) + baseline_30d_calls + department,
  data = customer_panel,
  panel = TRUE,
  control_group = "notyettreated",
  est_method = "dr",
  base_period = "universal",
  bstrap = TRUE,
  cband = TRUE
)
summary(fit)
dynamic <- aggte(fit, type = "dynamic")
summary(dynamic)
ggdid(dynamic)
overall <- aggte(fit, type = "simple")
summary(overall)
```
**Important:** `aggte(..., type="simple")` is not automatically the same estimand as cumulative **calls saved per treated customer during Days +1…+30**. Define horizon-specific weights and outcome first. Covariates should be pre-treatment, not post-treatment and should be encoded sensibly. R library installation, dataset scalability, and practical index-matching integration need checking.

### B3 — Estimation methods and assumptions
- **Unadjusted cohort DiD:** difference in average treated and untreated changes within a comparable cohort/time contrast.
- **Outcome regression:** model untreated outcome change given pre-treatment X.
- **Inverse propensity weighting:** reweight eligible untreated comparisons by probability of cohort participation conditional on pre-treatment X.
- **Doubly robust DiD:** combines both; may remain consistent if one nuisance model is correctly specified under conditional parallel trends, overlap, and other assumptions. It cannot fix unobserved opt-in motivation, changes in eligibility, or misaligned index events.
- Include customer-clustered/bootstrap inference where appropriate; shared controls contribute repeated observations. Inspect covariance/support and pre-trend estimates.

## Validation checklist before results are shown
1. One unique first-treatment date per treated customer, deterministic timestamp tie handling.
2. One unique customer/cohort/department/group record; no already-treated customer as control.
3. Zero-call and zero-payment rows included; distinct call IDs; Day 0 excluded by design.
4. Cohort coverage: at least 30 full days of pre and post data for initial analysis; report dropped cohorts and customers.
5. Pre-period covariate balance and common support: FY25 actual call counts, recent baseline calls, bill-pay history, department, tenure and other customer attributes.
6. Pre-treatment trajectories: ideally 8–12 weeks of historical outcomes, align appropriate calendar periods, check systematic differences and anticipation.
7. Sensitivity: same-day vs nearby-date comparable calls, alternative departments/risk sets, 7/14/21/30-day business windows, overlapping subsequent sessions, topic heterogeneity, model specification.
8. Proper confidence intervals and a transparent statement that education is voluntary and effects are observational.
9. Explicit interpretation of sample-average 30-day calls avoided, uncertainty, and any cost conversion; financial savings are estimates, not guaranteed realized savings.

## What to deliver
A modular Databricks pipeline with clear temp views, easily edited source column mappings, quality checks and sample output at each stage; cohort-level comparison tables; adjusted overall ATT and heterogeneous ATT; a properly specified dynamic event study; confidence intervals; business-ready Tableau-ready result tables. Begin by reviewing identification assumptions and table schemas. **Implement Stage A1 first, then move step-by-step with validation. Do not dump the whole codebase at once.**
