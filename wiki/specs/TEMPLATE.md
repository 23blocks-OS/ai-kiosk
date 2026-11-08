# Spec NNN — Title

Copy this file to `specs/issue-<N>-short-title.md`. Write it **before** any code, when Juan decides to work on the item. Fill every section. Write "none" instead of leaving one empty.

- **Issue:** link
- **Date:** YYYY-MM-DD. **Status:** draft | approved | building | done.
- **Approved by:** Juan, with his words and the date.

## Goal
One or two sentences: what is true after this work that is not true now.

## Context
Why now. What we saw (evidence, with dates and numbers). Links to decisions and issues.

## Not in scope
What we will not do in this work.

## Approach
How it works, in plain words. Why this way. The other ways we considered and why we dropped them.

## Where
Every file, function and setting that changes or is added. Paths and line ranges.

## Steps
Numbered, in order, each one small enough to check. Say who does each step (`ciao-kiosk`, or Juan for sudo or dashboard steps).

## Tests
Each test: name, what it does, what it must show. Say which test fails on today's code.

## How we check it live
The commands or clicks that prove it works on the real system (URLs, expected codes). A result counts only after it is read back from outside.

## Deploy and rollback
How it gets to Aurelium. How we undo it. What can break.

## Risks and open questions
What could go wrong. What we still need from Juan.

## Result
Filled after the work. What shipped (PR links, commit), what we measured, what differed from this spec.
