# CI test scope

The blocking backend unit suite runs `backend/tests/` and excludes only:

- `backend/tests/e2e/`, which runs in the dedicated E2E job against PostgreSQL
  and Redis services.
- `backend/tests/performance/`, which is a load/performance suite and is not a
  correctness gate. Run it separately when validating performance changes.

The backend job also explicitly runs root-level indexing authorization,
GraphQL ownership, OAuth fail-closed, and rate-limit regression tests. OAuth
provider login remains disabled until a complete provider verification and
identity persistence flow is implemented; the OAuth regression suite asserts
that disabled routes cannot create or link accounts.

The backend test command uses `pipefail`, so a pytest failure cannot be hidden
by its log tee. Type checking, Bandit, and dependency auditing are blocking
steps: tool failures and findings fail the job.
