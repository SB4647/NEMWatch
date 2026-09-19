# Data Source and Use

NEMWatch will use only public data published by the Australian Energy Market Operator (AEMO). Any checked-in fixture derived from public AEMO material must retain enough source attribution to identify its origin and support later verification.

Employer data, private operational data, credentials, and confidential material must never be added to this repository. NEMWatch is an educational project and is not a trading, dispatch, or operational control system.

The required offline demonstration uses `backend/data/fixtures/dispatch_sample.csv`. Its adjacent `ATTRIBUTION.md` identifies AEMO's public NEMWeb source page, the fields retained, and the deterministic normalization applied. The fixture is educational and must not be interpreted as live market information.

Network retrieval is optional. When enabled, NEMWatch accepts only HTTPS, sends an identifying user agent, limits time and response size, retries a bounded number of times, and reports failures without exposing connection details.
