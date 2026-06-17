# SKILL: Data privacy (practical GDPR for B2B)

## If the project touches personal data (names, emails, location, payments,
## health), this is NOT optional — it's legal and commercial (we sell to EU enterprises).

### Privacy by design
- **Minimization**: ask for and store ONLY the data needed for the function.
  Do you need the date of birth, or is "of legal age" enough? Store the minimum.
- **Mark the PII**: in the data model, flag which columns are personal data
  (name, email, IP, location). The director must know (a business decision).
- **Legal basis**: for each piece of personal data, why is it processed?
  (consent, contract, legitimate interest). Consent = explicit, revocable, recorded.
- **Retention**: define how long each piece of data is kept and what deletes it.
  Nothing "forever by default".

### User rights (implementable)
- **Access/portability**: be able to export THEIR data (JSON).
- **Erasure** ("right to be forgotten"): be able to delete their account and data
  (hard-delete or anonymization, not just soft-delete if they asked for real deletion).
- **Rectification**: be able to correct their data.

### PII security
- Encrypted in transit (HTTPS) and, for sensitive data, at rest.
- Logs and reports NEVER contain PII in the clear (use ids).
- Don't share PII with third parties (analytics, AI) without a legal basis and notice.

### Director's rule
When you detect PII or a decision with legal implications (cookies, tracking,
minors, payments), NOTE IT in NOTES.md and escalate it to the human checkpoint.
Don't decide yourself what is the business's legal responsibility.
