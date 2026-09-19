# Dispatch sample attribution

The valid rows in `dispatch_sample.csv` use the public field structure of AEMO dispatch regional summary data. The compact values are normalized for a deterministic educational demonstration and are not presented as current market data.

- Public source page: https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-data-nemweb
- Retrieved for schema reference: 2026-09-19
- Selected fields: region identifier, dispatch interval, regional reference price, total demand, generation, and net interchange
- Normalization: ISO-8601 UTC timestamps, stable decimal formatting, a three-interval subset for all five NEM regions, and deterministic high-price and demand-change examples
- Synthetic additions: the final four rows are deliberately malformed to demonstrate typed row rejection

This fixture contains no employer, participant-private, or operationally sensitive data.
