# WA-contested-divorce-without-children-mediation-to-end
AI-driven SDD wizard guiding Washington State contested no-children divorce cases from mandatory settlement conference to final decree.

## Repository workflow

Read the applicable specification in `specs/` before making changes. Run baseline
checks with `bash harness/validate.sh`. To run another command and capture its
output, invocation, timestamp, and exit status, use
`bash harness/validate.sh -- <command> [arguments...]`. The harness appends each
execution to `interactions/00-initialization/response-00-init.md`.
