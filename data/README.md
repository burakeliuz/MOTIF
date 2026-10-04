# data/

Run outputs are written here and ignored by git:

- `raw/<run_id>/`: run record, request log, and verbatim harness output.
- `normalized/<run_id>/`: seed resolutions, observations, coverage, comparison, facts sheet.

Live runs contain Qloo response data. Keep it out of source control and
out of public demos unless the event's data terms allow it. Share only the
small, secret-free excerpts a report needs. Credentials are never written
here: the harness holds them, and every error message is redacted before it
is stored.

Use `--data-dir` or `$MOTIF_DATA_DIR` to write somewhere else.
