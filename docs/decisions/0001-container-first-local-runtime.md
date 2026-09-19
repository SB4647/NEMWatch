# ADR 0001: Container-first local runtime

- Status: Accepted
- Date: 2026-09-19

## Context

The development host does not provide project-managed Python or uv installations. The first milestone also needs PostgreSQL, Redpanda, Node, and repeatable clean-clone verification without relying on machine-specific service configuration.

## Decision

Docker Compose is the canonical local runtime. Application dependencies are locked, base images use explicit version tags, and all verification commands run inside project containers.

## Consequences

Clean-clone behaviour is reproducible across supported hosts and does not require host installations of Python, uv, Node, PostgreSQL, or Redpanda. Initial setup requires container image downloads, Docker Desktop with Linux containers, and enough Docker memory for the four services.

## Alternatives rejected

- Host-managed language runtimes and data services, because they create machine-specific setup and version drift.
- Cloud-first deployment, because it adds cost, credentials, and operational scope before the local product foundation is proven.
