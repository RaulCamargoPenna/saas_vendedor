#!/usr/bin/env bash
# Reviewed candidate only. Do not substitute for production's untracked script.
# No host prepare/finalize adapter exists to rotate the exact collector identity.
# The workflow remains disabled and still invokes the old untracked entrypoint.
printf '%s\n' 'SaaS Vendedor release refused: host integration for exact-ID handoff is not installed.' >&2
exit 78
