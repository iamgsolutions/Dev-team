# SKILL: Systematic debugging — diagnosis before patch

1. **Reproduce first**: without a reliable repro there is no reliable fix.
   Reduce to the minimal case (does it fail with a single record? without auth?).
2. **Read the WHOLE error**: the last line of the traceback says WHAT, the
   first ones say WHERE it started. The real error is usually the FIRST in the
   chain, not the last symptom.
3. **One hypothesis at a time**: state it ("the 404 comes from X because Y"),
   verify with ONE change/log, rule it out or confirm. Changing 5 things at
   once = not knowing which one fixed (or broke) what.
4. **Bisection**: did it work before? `git log` on the file; isolate the commit.
   Does the layer below work? Test the query/the service directly without the router.
5. **The fixed bug demands**: (a) understanding WHY it happened (not "it no
   longer happens"), (b) a regression test, (c) searching for the SAME pattern in
   the rest of the code (bugs come in families).
6. **If 30 min without progress**: stop, write in NOTES.md what you tried and what
   you ruled out, and rethink (is the base assumption false?). Pushing blindly
   burns tokens without new information.
