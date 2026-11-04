# A/B test plan: financing prompt for high-ticket smartphone carts

- Hypothesis: showing a financing / payment-plan prompt to users with a 500+ smartphone in their cart raises the cart->purchase rate.
- Population: carted smartphone sessions where the most expensive cart item is 500 or more (~234K sessions in Nov 2019).
- Randomization unit: user_id, so one person never sees both versions.
- Control: current experience. Treatment: current experience plus the financing prompt.
- Primary metric: cart->purchase rate. Baseline ~40.0%.
- Secondary metric: revenue per carted session.
- Guardrails: average order value; cancellations/returns (not measurable in this dataset).
- Minimum detectable effect: +2 percentage points (~5% relative).
- Significance level 5% (two-sided), power 80%.
- Run for at least 7 full days, even if the sample fills sooner, to cover weekday/weekend patterns.
- Fixed sample size, no peeking. Ship only if the primary metric is significantly higher and guardrails don't drop.
