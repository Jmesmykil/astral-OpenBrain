# Audit of the grant application, 2026-09-04

Audited against three sources: the form's own prompts and preamble (what OpenHome asks for
under each question, the five criteria, the five milestone stages), OpenHome's grant
announcement (innovation, impact, technical feasibility; Discord engagement; previous
projects; the ability to work independently and meet milestones; up to $15,000 in AWS
credits), and ordinary grant practice (a clear ask, a budget that includes the applicant's
time, a timeline, named risks, no overclaims, no inside jargon, consistent numbers).

## What the program is, in their words

A $50,000 program for "novel, human-centered AI-powered voice applications", judged on
technical advancement, impact, intuitiveness, delight and interaction. Their stages:
Dev Kit tier, community development (public repo, Discord, updates), completed demo
(working prototype and open-source code), live integration (code review into core
OpenHome), critical selected feature. Applications are reviewed on a rolling basis.

## Findings, ranked

1. **Open source is a stated deliverable and the engine is compiled.** The public
   repository holds the ability, the deploy scripts and the documents; the local loop and
   the kernel sources are in a private repository and ship as a compiled wheel. The old
   text said "MIT shim" without saying what is not open. The new text states what is
   open (everything that runs inside OpenHome's runtime) and what is compiled, and points
   at the boundary document. Opening the local loop's source under the grant would make
   the application stronger against their "open-source code" milestone. That is a product
   decision and it is yours.
2. **The public repository had no licence file** while the text and BOUNDARY.md call the
   ability MIT. Added LICENSE (MIT, 2026, Jamesmykil Weber) at the repository root.
3. **The budget paid for hardware and not for you.** Every milestone said "cost: my time"
   as if time were free. A $50,000 application is expected to fund the developer. The new
   budget puts developer time at $32,000 over six months, the workstation at list price,
   test hardware, evaluation, part-time packaging help and a contingency, and shows what
   $10,000 buys. The numbers are proposals; change any of them.
4. **No timeline.** Their milestones imply one. Added six months from award, with each of
   the five milestones placed in it and mapped to their stage names (live integration,
   critical selected feature).
5. **The human side was missing.** Their criteria are intuitive, delightful, interactive.
   The old description led with the router and the passage count. The new one leads with
   what it is like to use: ask and it answers, follow up without the wake word, riddles
   and quizzes, a page read from a book, and it says why when it cannot help.
6. **Related work was thin.** Home Assistant alone. Added Open Voice OS (the Mycroft
   successor) and Rhasspy as the closest relatives, Kiwix for offline reference, and the
   cloud assistants, and stated precisely what none of them do.
7. **Copyright risk in milestone 3.** "The encyclopedias I own on the card, shipped
   built" reads as redistributing copyrighted volumes. The design already separates the
   owner's own books (indexed on the owner's card) from what ships (the indexer and an
   openly licensed starter shelf). The text now says so, under Ethics and in milestone 3.
8. **The "Nothing" tier and "I'm a student with no income".** Both read as appeals rather
   than a plan. Removed the "Nothing" line. The constraint is stated once, plainly, where
   it belongs: the machine is the one thing I cannot buy on my own timeline.
9. **Fourteen unrelated projects in the experience answer.** A crypto research desktop,
   two games and an animated series dilute the case and one of them invites the wrong
   question. Kept what bears on this project: the OpenHome work, the harness, the two
   engines (Slate runs on the device), and three pieces of constrained-hardware work.
   Links to the public ones stay under question 17. Restore any you want back.
10. **Numbers were stale.** 3,630 checks in 26 suites became 3,868 in 27 after today's
    merges. "65 DK volumes went on today" became a dated fact.
11. **Inside jargon without definition:** "the ladder", "rung", "mechanical assistant",
    "no-silent-failure suite", "runbook", "kernel wheel". Each is now either defined on
    first use or replaced with plain words.
12. **Fragments.** The earlier register produced sentence fragments ("The time, arithmetic,
    unit conversions."). Grant readers read fragments as haste. Rewritten as sentences,
    still first person and plain, mean 19 words a sentence, no em dashes, no semicolons.
13. **AWS credits.** The announcement offers up to $15,000 in AWS credits. A reviewer will
    ask why buy a machine when credits exist. The text now says credits would fund the
    training and evaluation runs, and the machine is for the in-house rung, which by
    design cannot be a cloud.
14. **Their three deliverables were never named.** Added a paragraph under Methodology
    that maps the project to each stage: DevKit in hand, public repository and Discord,
    demo by voice with a transcript, version 1 merged as PR #361, the critical feature.
15. **"Anything else" now answers every example they list:** how I heard and who
    referred me, affiliation, previous AI projects, presentations (the demo call and the
    handout in the repository), publications (none), references (none claimed).
16. **Fields 1 to 8.** Name, email, referrer, location, GitHub and Discord are right. The
    phone number is formatted to match question 18. The mailing address was reordered and
    capitalised; it has no ZIP code, which you should add.

## Decisions that are yours

- Open the local loop's source under the grant, or keep the compiled boundary (finding 1).
- The budget numbers, especially developer time and the part-time help (finding 3).
- The six-month timeline (finding 4).
- Which projects to list beyond the ones that bear on this device (finding 9).
- Whether to name your university under Affiliation.
- The ZIP code in the mailing address.

## What did not change

Every measured number (397,706 passages, 682 facts, PR #361 on 2026-08-31, the 57/24/13
review, the machine's prices), the phone number, the contact line, the five milestones
themselves, and the funding levels you set ($50,000 and $10,000, with a line for a smaller
award).
