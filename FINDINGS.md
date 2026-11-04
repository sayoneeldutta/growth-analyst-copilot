# Findings: Nov 2019 e-commerce funnel

## Funnel
- Session conversion: 5.6% overall; 12.6% view->cart, 37.2% cart->purchase
- ~1.09M carted sessions ended without a purchase

## Where the abandonment is
- Electronics has the best cart->purchase rate (41%) but the most abandoned carts by volume
- Smartphones alone: ~383K abandoned cart sessions (57% of carted)
- Smartphone cart->purchase is fairly flat across price bands (39-45%), so price alone doesn't explain abandonment

## Revenue impact
- 500+ smartphone bands = 36% of abandoned carts but ~71% of revenue at risk (~$137M of ~$193M)
- 500-1000 band is the top target: 40.7% of revenue at risk, lowest cart->purchase among high-value bands (39.4%)
- Caveat: revenue at risk is an upper bound (uses max item price per session; some carts convert later)
- Your new finding here

## A/B test design (simulated, not a real result)
- Target: 233,946 carted smartphone sessions priced 500+, baseline cart->purchase 40.03%
- Needed sample for a +2pt lift at 80% power: 9,494 per group (18,988 total)
- Simulation check: 78.8% power at +2pt lift, 5.1% false positives with no effect
- The lift in the simulation is assumed, so this demonstrates the method, not that a financing prompt works
