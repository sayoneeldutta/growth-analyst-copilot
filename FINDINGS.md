# Findings: November 2019 e-commerce funnel

Numbers use normal days (14-17 Nov excluded) unless stated. Revenue is in the dataset's own price units.

## Funnel
- 10.5M sessions; 5.2% end in a purchase
- 47.6% of carted sessions end in a purchase; about 491K carts abandoned

## Data problem, 14-17 Nov
- 15 Nov: 255,279 carted sessions and exactly 1 purchase (a normal day has about 20,000)
- Carts run at 2 to 5 times normal on 14-17 Nov; purchases are 2.7 and 7 times normal on 16-17 Nov
- These four days hold 24% of sessions, 46% of carted sessions and 55% of abandoned carts
- With them included: cart-to-purchase 37.2%, abandoned carts 1.09M, sessions with a purchase 5.6%
- Cause unknown (tracking fault, bot traffic or a real event). Excluded by default; the dashboard has a toggle

## Where the money is (smartphones)
- Carts priced 500+ are 31% of abandoned carts but 67% of the revenue at risk (about 49M of 74M)
- With all days included the split was 36% and 71%, so the finding holds
- Cart-to-purchase is 54-58% for every band from 100 up, so price alone does not explain abandonment
- The 500-1000 band holds the most revenue at risk (27.4M); 1000+ holds 21.9M
- Caveat: revenue at risk is an upper bound (most expensive item per cart; some shoppers return)

## Do abandoned carts come back? (smartphones priced 500+, 19,192 carts)
- 11.5% of shoppers bought the same phone within 7 days; 21% bought any phone
- About 79% of cart value shows no repeat purchase in the category within 7 days
- Caveats: followed by user ID only; first-hour returns may be split visits; cheaper later purchases are credited at the full cart price

## A/B test design (simulated, not a real result)
- Segment: smartphone carts priced 500+, 116,990 sessions over 26 normal days (about 4,500 a day), baseline cart-to-purchase 56.9%
- For a +2 point lift at 80% power: about 9,600 sessions per group, run at least 7 days
- The lift in the simulation is assumed, so this demonstrates the method, not that any intervention works
