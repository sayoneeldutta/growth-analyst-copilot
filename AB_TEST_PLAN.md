# A/B test plan: prompt for high-priced smartphone carts

- Hypothesis: showing a payment-plan prompt to shoppers with a 500+ smartphone in their cart raises the cart-to-purchase rate.
- Population: carted smartphone sessions where the most expensive cart item is 500 or more. On normal days (14-17 Nov excluded): 116,990 sessions over 26 days, about 4,500 a day.
- Randomization unit: user_id, so one person never sees both versions.
- Control: current experience. Treatment: current experience plus the prompt.
- Primary metric: cart-to-purchase rate. Baseline 56.9% on normal days.
- Secondary metric: revenue per carted session.
- Guardrails: average order value; cancellations and returns (not measurable in this dataset).
- Minimum detectable effect: +2 percentage points (about 3.5% relative).
- Significance level 5% (two-sided), power 80%.
- Sample size: about 9,600 per group (19,200 total), roughly 5 days of traffic. Run at least 7 full days to cover weekday and weekend behaviour.
- Fixed sample size, no peeking. Ship only if the primary metric is significantly higher and guardrails do not drop.
- Context: about 21% of shoppers with an abandoned cart in this segment buy a phone within 7 days without any prompt, which is why the control group matters.
