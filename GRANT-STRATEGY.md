# Grant strategy, version 3 (2026-09-04)

## The pitch in one sentence

Astral for OpenHome already answers on the device. Under the grant it becomes the voice front
end to the AI tools on a developer's own computer: a bridge from the DevKit to any harness on
the local network, with spoken consent for each action, an audit the device reads back, and
nothing leaving the house.

## Why this framing is the most likely to be accepted

- It is their criteria, met by construction. The form asks for "novel, human-centered
  AI-powered voice applications" judged on technical advancement, impact, intuitiveness,
  delight and interaction. A developer talking to their own computer is the most human
  interaction that a community of "developers and designers" lacks today, and it is
  bidirectional by design, because the harness asks questions back.
- It is their last stage. Four of the five stages are already met by phase 1: the DevKit,
  the public repository and the Discord, the demo by voice, and version 1 merged as PR #361.
  The bridge is the "critical selected feature" they name as the fifth. The application says
  so in their words.
- It is a platform feature, not one application. One open protocol that every harness author
  can support gives OpenHome leverage that a single app never does.
- It is backed by evidence. A month of shipped work, a merged pull request and 3,884 checks
  make "I can build this" a record rather than a promise.

## What OpenHome gets, whatever happens to the engine

The MIT ability and the MIT bridge protocol with a reference adapter for an open-source
harness, the DevKit as the reference device for talking to your computer, a consent and audit
pattern other abilities can copy, and a demo in which the DevKit does real work.

## Risks, and how the application handles each

1. "Full access to your computer" reads as a security story before it reads as a feature.
   The application leads with pairing, per-project scopes, spoken confirmation, the audit,
   "stop everything" by voice, and the local network only. The power comes after the rules.
2. Reviewers expecting consumer applications. The details section opens with four spoken
   exchanges a person would have, not with the protocol.
3. The deterministic engine is ambitious. It is phase 3, beyond the grant, named once as the
   applicant's longer road, with the fallback stated plainly: the bridge is model-agnostic and
   delivers its value with whatever model the harness runs.
4. Open source. Stated once and plainly: everything inside OpenHome's runtime and the protocol
   are MIT, and the engine is the applicant's product and ships compiled.
5. Solo capacity. Phase 1 shipped alone in a month, and phase 2 is bounded to the bridge, two
   adapters, the suites, a demo and the review.
6. Over-justifying. Version 2 carried a month-by-month plan and a budget to the dollar. Version
   3 has three phases and a budget in three lines.

## Decisions for the owner to confirm

- The bridge's public name (drafted as "the Astral bridge").
- Which open-source harness gets the reference adapter (drafted as "one open-source coding
  harness", to be named at integration time).
- Naming the Astral Brain Engine as the first harness bridged (drafted as named).
- The three budget lines and the workstation.
- Whether to keep the one sentence that calls phase 3 a business.
