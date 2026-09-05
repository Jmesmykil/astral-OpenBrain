#!/bin/zsh
# Retired: the previous workflow reset a checkout and bundled private engine source.
# Current ability shipping uses the reviewed MIT shim plus a compiled dependency.
set -eu
print -u2 -- "This source-bundling workflow is retired. No checkout was changed."
print -u2 -- "Read HANDOFF.md and RELEASE.md, validate community/astral, and ship the compiled dependency separately."
exit 2
