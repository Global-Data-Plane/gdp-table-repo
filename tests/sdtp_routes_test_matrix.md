# SDTP Integration Test Matrix

This matrix defines the core tests for SDTP routes, with four tables and four user types.

## Table Types

- `owned_by_userA` — created/owned by userA
- `shared_to_userB` — shared with userB
- `hub_shared` — readable by hub users
- `public_table` — readable by anyone

## User Types

- **userA** — table owner
- **userB** — not owner; some shared
- **hub_user** — can see hub-shared
- **unauthenticated** — public access

---

## get_table_names

| Test                               | User         | Expected Tables Shown                                   |
|-------------------------------------|--------------|--------------------------------------------------------|
| Owner sees all                     | userA        | owned_by_userA, shared_to_userA, hub_shared, public_table |
| Shared user sees shared/hub/public | userB        | shared_to_userB, hub_shared, public_table              |
| Hub user sees hub/public           | hub_user     | hub_shared, public_table                               |
| Unauthenticated sees public        | none         | public_table                                           |

---

## get_tables

| Test                        | User    | Expected Result                      |
|-----------------------------|---------|--------------------------------------|
| Authenticated (userA)       | userA   | schemas for all visible tables       |
| Unauthenticated             | none    | schemas for public_table only        |

---

## get_table_schema

| Test                       | Params                      | User     | Expected Code/Result     |
|----------------------------|-----------------------------|----------|-------------------------|
| No table param             | {}                          | userA    | 400                     |
| Table not found            | {table: "nope"}             | userA    | 404                     |
| Table not permitted        | {table: "owned_by_userA"}   | userB    | 401/403                 |
| Success (owner)            | {table: "owned_by_userA"}   | userA    | 200 + schema            |
| Success (shared)           | {table: "shared_to_userB"}  | userB    | 200 + schema            |
| Success (hub)              | {table: "hub_shared"}       | hub_user | 200 + schema            |
| Success (public)           | {table: "public_table"}     | none     | 200 + schema            |

---

## get_range_spec

| Test                        | Params                             | User     | Expected Code/Result    |
|-----------------------------|------------------------------------|----------|------------------------|
| No table param              | {column: "id"}                     | userA    | 400                    |
| Table not found             | {table: "nope", column: "id"}      | userA    | 404                    |
| Table not permitted         | {table: "owned_by_userA", column: "id"} | userB | 401/403                |
| Table exists, missing col   | {table: "owned_by_userA", column: "nope"} | userA | 400                 |
| No column param             | {table: "owned_by_userA"}          | userA    | 400                    |
| Success (owner)             | {table: "owned_by_userA", column: "id"} | userA | 200 + min/max         |
| Success (shared)            | {table: "shared_to_userB", column: "id"} | userB | 200 + min/max         |
| Success (hub/public)        | {table: "hub_shared", column: "id"}<br>{table: "public_table", column: "id"} | hub_user<br>none | 200 + min/max |

---

## get_all_values / get_column

| Test    | Params                    | User    | Expected              |
|---------|---------------------------|---------|-----------------------|
| Success | table/column present      | any     | 200 + values (type)   |

---

## get_filtered_rows

| Test                   | Params                                                     | User    | Expected |
|------------------------|------------------------------------------------------------|---------|----------|
| No table param         | {"columns": ["id"]}                                        | userA   | 400      |
| Not authorized         | {"table": "owned_by_userA", "columns": ["id"]}             | userB   | 401/403  |
| Bad filter_spec        | {"table": "owned_by_userA", "filters": ["bad"]}            | userA   | 400      |
| Bad format             | {"table": "owned_by_userA", "format": "nope"}              | userA   | 400      |
| Bad columns set        | {"table": "owned_by_userA", "columns": ["nope"]}           | userA   | 400      |
| Success: list, all     | {"table": "owned_by_userA", "format": "list"}              | userA   | 200      |
| Success: list, filtered| {"table": "owned_by_userA", "filters": [...], "format": "list"} | userA | 200 |
| Success: csv, columns  | {"table": "owned_by_userA", "columns": ["id"], "format": "csv"} | userA | 200 |
| Success: public table  | {"table": "public_table", "format": "list"}                | none    | 200      |

---

## Notes

- Use the actual table names in your test setup.
- Simulate sharing, hub/public visibility as needed.
- Each test should assert both status codes and returned data/schema.

---

*Generated for Rick & Aiko — SDTP, 2025*
