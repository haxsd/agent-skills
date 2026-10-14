---
name: supabase-postgres-best-practices
description: "Postgres best practices maintained by Supabase, for Postgres running anywhere. Load this skill BEFORE writing or changing anything that lives in a Postgres database: creating or altering tables and columns (including choosing column types), schema design, migrations and declarative schema files, RLS policies and the tests that verify them, indexes, triggers, database functions, queues and scheduled jobs (pg_cron, pgmq), vector/semantic search (pgvector), and restoring dumps (pg_restore) or importing data. Also load it when diagnosing slow queries, high CPU, timeouts, EXPLAIN plans, connection exhaustion, locking, bloat, or rows visible to the wrong user or tenant. This is not just a performance guide — schema, migration, security, and SQL authoring tasks need these rules too, even for a one-column change or a single query."
license: MIT
metadata:
  author: supabase
  version: "1.1.1"
  organization: Supabase
  date: January 2026
  abstract: Comprehensive Postgres performance optimization guide for developers using Supabase and Postgres. Contains performance rules across 8 categories, prioritized by impact from critical (query performance, connection management) to incremental (advanced features). Each rule includes detailed explanations, incorrect vs. correct SQL examples, query plan analysis, and specific performance metrics to guide automated optimization and code generation.
---

# Supabase Postgres Best Practices

Comprehensive performance optimization guide for Postgres, maintained by Supabase. Contains rules across 8 categories, prioritized by impact to guide automated query optimization and schema design.

## When to Apply

Reference these guidelines when:
- Writing SQL queries or designing schemas
- Implementing indexes or query optimization
- Reviewing database performance issues
- Configuring connection pooling or scaling
- Optimizing for Postgres-specific features
- Working with Row-Level Security (RLS)

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Query Performance | CRITICAL | `query-` |
| 2 | Connection Management | CRITICAL | `conn-` |
| 3 | Security & RLS | CRITICAL | `security-` |
| 4 | Schema Design | HIGH | `schema-` |
| 5 | Concurrency & Locking | MEDIUM-HIGH | `lock-` |
| 6 | Data Access Patterns | MEDIUM | `data-` |
| 7 | Monitoring & Diagnostics | LOW-MEDIUM | `monitor-` |
| 8 | Advanced Features | LOW | `advanced-` |

## How to Use

Read individual rule files for detailed explanations and SQL examples:

```
references/query-missing-indexes.md
references/query-partial-indexes.md
references/_sections.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect SQL example with explanation
- Correct SQL example with explanation
- Optional EXPLAIN output or metrics
- Additional context and references
- Supabase-specific notes (when applicable)

## References

- https://www.postgresql.org/docs/current/
- https://supabase.com/docs
- https://wiki.postgresql.org/wiki/Performance_Optimization
- https://supabase.com/docs/guides/database/overview
- https://supabase.com/docs/guides/auth/row-level-security

## Complete local rule index

Read only the rules matching the query, schema or security task.

- [advanced-full-text-search](references/advanced-full-text-search.md)
- [advanced-jsonb-indexing](references/advanced-jsonb-indexing.md)
- [conn-idle-timeout](references/conn-idle-timeout.md)
- [conn-limits](references/conn-limits.md)
- [conn-pooling](references/conn-pooling.md)
- [conn-prepared-statements](references/conn-prepared-statements.md)
- [data-batch-inserts](references/data-batch-inserts.md)
- [data-n-plus-one](references/data-n-plus-one.md)
- [data-pagination](references/data-pagination.md)
- [data-upsert](references/data-upsert.md)
- [lock-advisory](references/lock-advisory.md)
- [lock-deadlock-prevention](references/lock-deadlock-prevention.md)
- [lock-short-transactions](references/lock-short-transactions.md)
- [lock-skip-locked](references/lock-skip-locked.md)
- [monitor-explain-analyze](references/monitor-explain-analyze.md)
- [monitor-pg-stat-statements](references/monitor-pg-stat-statements.md)
- [monitor-vacuum-analyze](references/monitor-vacuum-analyze.md)
- [query-composite-indexes](references/query-composite-indexes.md)
- [query-covering-indexes](references/query-covering-indexes.md)
- [query-index-types](references/query-index-types.md)
- [query-missing-indexes](references/query-missing-indexes.md)
- [query-partial-indexes](references/query-partial-indexes.md)
- [schema-constraints](references/schema-constraints.md)
- [schema-data-types](references/schema-data-types.md)
- [schema-foreign-key-indexes](references/schema-foreign-key-indexes.md)
- [schema-lowercase-identifiers](references/schema-lowercase-identifiers.md)
- [schema-partitioning](references/schema-partitioning.md)
- [schema-primary-keys](references/schema-primary-keys.md)
- [security-privileges](references/security-privileges.md)
- [security-rls-basics](references/security-rls-basics.md)
- [security-rls-performance](references/security-rls-performance.md)

<!-- provenance:start -->
> 创作归属：第三方引入。来源、署名与许可见 [来源说明](../../ATTRIBUTION.md#supabase-postgres-best-practices)。
<!-- provenance:end -->
