# Spec-Driven Execution SOP

Operating rule: create or update the change package first, then borrow execution-only skills for implementation discipline.

## Step 1

Read `rules/`, `knowledge/`, and any existing change package first.

## Step 2

Write or update `spec.md` with real file-path evidence.

## Step 3

Split the work into atomic tasks in `tasks.md`.

## Step 4

Route the work to the right companion skill:

- Frontend: `frontend-design`
- Backend API: `api-design-principles`
- PostgreSQL: `postgresql-table-design`

Add execution discipline when appropriate:

- New feature or refactor: `test-driven-development`
- Bug investigation: `systematic-debugging`
- Final completion gate: `verification-before-completion`
- Review checkpoint: `requesting-code-review`

## Step 5

Implement task by task and record key findings in `log.md`.

## Step 6

If implementation diverges from the plan, update `spec.md` and `tasks.md` first.

## Step 7

Review spec compliance, code quality, and verification evidence before closing the change.
