#!/usr/bin/env bash
# Reviewed candidate only. Never roll back to a legacy script that drops an
# active or pending event overlay. No installed host adapter can prove safety.
printf '%s\n' 'SaaS Vendedor rollback refused: host integration for exact-ID handoff is not installed.' >&2
exit 78
