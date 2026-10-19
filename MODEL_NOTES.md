# Model and teaching conventions

All examples use hypothetical monetary units. Each problem has one to four periods. Node index j counts down moves.

## Supplied lecture moves

The guided examples use a 20% rise or 20% fall per annual step: u=1.2, d=0.8. The effective annual risk-free rate is 5%, equivalent to continuous r=ln(1.05); q=0. These moves are supplied returns, not reciprocal CRR moves.

## CRR construction workspace

dt=T/n; u=exp(sigma*sqrt(dt)); d=1/u.

Risk-neutral p=(exp((r-q)*dt)-d)/(u-d), while R=exp(r*dt). q is a continuous dividend or convenience yield; the example assumes zero storage cost. Require d < exp((r-q)*dt) < u. Use p for pricing, not forecasting.

European maturity payoffs are max(S-K,0) for calls and max(K-S,0) for puts. Earlier values discount weighted child option values. American exercise compares immediate exercise with continuation.

## Compound access gates

G buys continued access; K is the strike paid on exercise. At a European access gate, value=max(0, continuation-G). Declining ends access permanently. The signed NPV of paying may be negative even though the option value is zero.

In the construction workspace's American compound contract, exercise is available before the access payment: compare immediate exercise with max(0, continuation-G). Exercise ends future payments. This convention is explicit in the app. The guided lecture cases retain their original contracts.

Pricing assumes the relevant market risk can be spanned. Technical failures, competition and salvage proceeds are not modeled. One-to-four-step CRR comparisons are deliberately coarse and may oscillate around the European Black-Scholes benchmark.

## Lecture checks

- One-period call: 11.9047619.
- Two-period simple call: 15.5895692.
- Two-period gates (5,10,100): starting option 4.6371882.
- Three-period gates (5,10,10,100): starting option 2.7812871.
- Three-period gate node S=96: continuation 9.0476190; signed gate NPV -0.9523810; optimal value zero.
