# Five-minute demonstration

1. Copy `.env.example` to `.env` and run `make demo`.
2. Open http://localhost:5173. Confirm all five regions have an observation and that the fixture disclaimer is visible.
3. Select Queensland and the fixture UTC range in **Market history**. Load the chart and compare its exact points with the table.
4. In **Historical replay**, keep all regions selected, choose speed `100`, and start replay. Watch durable counts and live regional updates.
5. Open the high-price alert for Queensland, enter a note, and acknowledge it. The open state changes without a page reload.
6. Open http://localhost:3000 and select **NEMWatch overview**. Inspect API rate, event throughput, alert, replay, WebSocket, and readiness panels.
7. Refresh the browser. The stored observations, alerts, acknowledgement, and replay job remain available.
8. Run `make verify` for the consolidated automated suite, then `make down` to stop services while preserving data.
