# Trade-offs and known limits

## Fixture-first ingestion

The offline fixture makes the demonstration repeatable and reviewable without relying on AEMO availability or changing public files. Optional network retrieval is bounded and isolated, but the project does not claim continuous live-market ingestion.

## At-least-once delivery

The processor commits after persistence, favoring replayable work over at-most-once loss. Database uniqueness and upserts absorb duplicate dispatch delivery. Alert topic delivery can repeat across failures; consumers merge alerts by stable ID.

## Single-node local services

PostgreSQL and Redpanda run as single local nodes. This demonstrates interfaces, ordering, retries, and outage visibility without claiming production availability or disaster recovery.

## In-process WebSocket fanout

The API uses bounded in-memory client queues. This is simple and correct for one local API instance. Horizontal API scaling would require a shared fanout layer or client affinity.

## One active replay

A PostgreSQL advisory lock makes replay admission deterministic for the local MVP. A production scheduler would need leases, ownership, and crash recovery across workers.

## Security boundary

The app uses development-only local credentials and loopback-bound ports. It has no production identity, authorization, tenancy, trading controls, AWS resources, Kubernetes configuration, or secrets-management integration.
