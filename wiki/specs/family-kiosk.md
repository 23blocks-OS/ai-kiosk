# Spec — Family kiosk (working name; Juan to name it)

- **Issue:** [https://github.com/23blocks-OS/ai-kiosk/issues/54](https://github.com/23blocks-OS/ai-kiosk/issues/54)
- **Date:** 2026-11-09. **Status:** draft, waits for Juan's approval.
- **Request:** Juan, 2026-11-09: "lets build the family AI Agent. another option on the original screen. that agent will know everything about a family and answers stuff like what activities kids have tomorrow? what is the doctors name? when we need to renew the insurance of the house. etc. does it make sense as use case?"

## Does it make sense?
Yes, and it is the best fit so far for the 4B model on 8 GB. A family holds a small set of facts (about 50 to 150 lines). They fit in the prompt, so no search engine is needed. The questions are lookups ("who is the doctor") and date questions ("what is tomorrow"). The date questions are where a small model fails, so code does the date work and the model only words the answer.

One rule decides the design: **a real family's data is private.** This kiosk is public (`twofourai.com`, `ciaocorp.com`). The demo uses a **fictional family** (the Rivera family, Boulder). A real family would run its own copy, on the tailnet only, with its own data file.

## Goal
A visitor opens "Family", asks a question about the fictional Rivera family, and gets a short answer from the family record, or "I don't have that in the family record". The answer names the record it came from.

## Not in scope (Phase 1)
Writing to the record by chat ("add soccer on Friday"). Reminders, push or email. Calendar sync. Real family data. Login per family member. Voice-only mode beyond what the other kiosks have.

## Approach
1. **Family record.** One file, `family/record.json`, fictional. Each entry has a `kind`, a `text` and structured fields:
   - `people`: names, ages, school, allergies, doctor.
   - `events`: one-off (date, time, who, place) and weekly (weekday, time, who, place, from, until). Example: "Mateo, soccer, Tuesday 16:30, Mesa Park, until 2026-12-10".
   - `contacts`: doctor, dentist, school, plumber (name, role, phone).
   - `renewals`: house insurance, car registration, passports (name, due date, provider, policy number as a fake value).
   - `notes`: wifi name, trash day, pet vet. No real secrets.
2. **Code does the dates.** The backend takes today's date (Mountain time) and builds a short block: today, tomorrow, the next 7 days of events in order, and each renewal with "in N days". The model never computes a date.
3. **Prompt.** The record block (people, contacts, notes, that date block, the renewals block) plus rules: answer only from the record; say "I don't have that in the family record" otherwise; name the person and the time; never invent a phone number or a date; answer in the language of the question, in short sentences.
4. **Route.** `kiosk: "family"` and the same `/api/chat` path. The existing semaphore, timeout and key rules apply (`app:family` key, usable only by this kiosk). The record block is about 1,500 tokens, so a reply costs about 10 s warm.
5. **Page.** Copy of the Raft page shell: question buttons ("What do the kids have tomorrow?", "Who is the doctor?", "When does the house insurance renew?", "What is the wifi?"), a card showing which record lines the answer used, no Spanish toggle until the record has Spanish text (Raft lesson). Launcher gets a fourth card.
6. **Why not retrieval.** At 150 lines the whole record fits. Retrieval (the Raft engine) is added only if the record grows past about 300 lines. Considered and dropped for Phase 1.

## Where
`services/agent-backend/family/{__init__,record.json,dates.py,prompt.py}`, `main.py` (`PROMPTS`, `_family_answer`), `apps/kiosk-family/*`, `apps/launcher/*`, `tests/test_family.py`, `api-keys.json` on Aurelium (`app:family`, generated there, never printed), wiki pages.

## Steps
1. Juan approves and names it. 2. `ciao-kiosk` writes the record (about 60 lines, fictional, marked as fictional on screen). 3. `dates.py` with tests. 4. Prompt, route, key. 5. Page and launcher card. 6. Deploy; read back through both hostnames.

## Tests
- `dates`: tomorrow, weekly event on the right weekday, event past its end date is dropped, renewal in N days, leap year and month edge, Mountain time at 23:30.
- A question about tomorrow puts tomorrow's events in the prompt (fake model, check the prompt).
- Unknown kiosk key cannot use `family`; the family key cannot use other kiosks.
- Page and launcher link exist; page says the family is fictional.
- Live check on Aurelium: five fixed questions with known answers, results written in the Result section.

## Deploy and rollback
Same as Raft: PR, merge, pull on Aurelium, restart `ai-kiosk`. Rollback: revert the PR. Memory: one more prompt, no new model; no new load on the 8 GB board.

## Risks and open questions
- The 4B model may mix up two children's events. Mitigation: the date block lists one line per event with the name first. We measure on the five questions.
- Spanish answers: the 4B model drifts to Spanish on short text (seen on Intercambio). The family kiosk is English-only in Phase 1.
- **Juan decides:** the name; whether the demo family is the Riveras or another; whether a real-family private copy (tailnet only) is a Phase 2.

## Result
Not built.
