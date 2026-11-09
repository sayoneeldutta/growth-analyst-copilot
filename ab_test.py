import duckdb
import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    proportion_effectsize, proportions_ztest, confint_proportions_2indep
)

# 1. Baseline from the real data (normal days only: 14-17 Nov excluded)
con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
carted_sessions, baseline = con.sql("""
    SELECT COUNT(*), AVG(purchased)
    FROM 'data/session_category.parquet'
    WHERE category_code = 'electronics.smartphone'
      AND carted = 1 AND cart_price >= 500
      AND day NOT BETWEEN '2019-11-14' AND '2019-11-17'
""").fetchall()[0]
print(f"Target population: {carted_sessions:,} carted sessions, baseline cart->purchase = {baseline:.2%}")

# 2. Sample size
MDE = 0.02
ALPHA, POWER = 0.05, 0.80
effect = proportion_effectsize(baseline + MDE, baseline)
n = int(np.ceil(NormalIndPower().solve_power(
    effect, alpha=ALPHA, power=POWER, ratio=1.0, alternative="two-sided")))
print(f"Sample size needed: {n:,} per group ({2 * n:,} total)")

# 3. One simulated experiment (the lift here is an ASSUMPTION, not a finding)
rng = np.random.default_rng(42)
TRUE_LIFT = 0.02
control = rng.binomial(1, baseline, n)
treat = rng.binomial(1, baseline + TRUE_LIFT, n)

counts = np.array([treat.sum(), control.sum()])
nobs = np.array([n, n])
z, p = proportions_ztest(counts, nobs)
lo, hi = confint_proportions_2indep(counts[0], n, counts[1], n)
print(f"Control {control.mean():.2%} | Treatment {treat.mean():.2%} | diff {treat.mean() - control.mean():+.2%}")
print(f"z = {z:.2f}, p = {p:.4f}, 95% CI for difference: [{lo:+.2%}, {hi:+.2%}]")
print("Decision:", "SHIP" if (p < ALPHA and treat.mean() > control.mean()) else "DO NOT SHIP")

# 4. Repeat many experiments to check power and false positives
def significant(true_lift):
    c = rng.binomial(1, baseline, n)
    t = rng.binomial(1, baseline + true_lift, n)
    _, pv = proportions_ztest(np.array([t.sum(), c.sum()]), nobs)
    return pv < ALPHA

runs = 2000
print(f"Power check (true lift +2pt): {np.mean([significant(0.02) for _ in range(runs)]):.1%} of {runs} experiments significant")
print(f"False-positive check (no effect): {np.mean([significant(0.0) for _ in range(runs)]):.1%} of {runs} experiments significant")
