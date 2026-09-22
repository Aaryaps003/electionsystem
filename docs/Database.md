# Campus Election 2.0 — Database Design

## 1. Overview

Campus Election 2.0 uses PostgreSQL as its primary relational database.

The database is responsible for storing:

* Users
* Roles
* Elections
* Candidates
* Voter eligibility
* Ballot information
* Election results
* Audit events

The schema will be designed with particular attention to:

* Data integrity
* Referential integrity
* Election lifecycle
* Duplicate voting prevention
* Auditability
* Ballot privacy

---

# 2. High-Level ER Structure

```text
USER
 │
 ├────────── USER_ROLE
 │
 └────────── STUDENT_PROFILE
                │
                │
                ▼
          ELIGIBLE_VOTER
                │
                ▼
             ELECTION
             /      \
            /        \
           ▼          ▼
     CANDIDATE      BALLOT
           │          │
           └────┬─────┘
                │
                ▼
             RESULTS

ELECTION
   │
   ▼
AUDIT_EVENT
   │
   ├── previous_hash
   └── event_hash
```

---

# 3. Core Entities

## User

Stores authentication-related information.

Suggested fields:

```text
id
username
email
password_hash
is_active
created_at
updated_at
```

Passwords must never be stored directly.

---

# 4. User Role

Possible roles:

```text
VOTER
ADMIN
AUDITOR
```

Role-based authorization will be enforced by the backend.

---

# 5. Student Profile

Stores student-specific information.

Suggested fields:

```text
id
user_id
student_id
name
department
course
year
division
created_at
```

The `student_id` should be unique within the institution.

---

# 6. Election

Represents an individual election.

Suggested fields:

```text
id
title
description
status
start_time
end_time
created_by
created_at
updated_at
```

Possible status values:

```text
DRAFT
SCHEDULED
OPEN
CLOSED
RESULTS_PUBLISHED
```

---

# 7. Candidate

Represents a candidate participating in an election.

Suggested fields:

```text
id
election_id
name
description
department
manifesto
created_at
```

Relationship:

```text
Election 1 ───────── N Candidate
```

A candidate belongs to exactly one election.

Candidate modification should be restricted once the election enters its locked/open state.

---

# 8. Eligible Voter

Determines whether a student can participate in a specific election.

Suggested fields:

```text
id
election_id
student_id
eligible
created_at
```

Recommended constraint:

```text
UNIQUE(election_id, student_id)
```

This prevents the same student from being added multiple times to the same election's eligibility list.

---

# 9. Ballot

Stores a vote associated with an election.

The final schema must prioritize ballot privacy.

Initial conceptual fields:

```text
id
election_id
candidate_id
created_at
```

The implementation must avoid unnecessary direct exposure of:

```text
student_id → candidate_id
```

The exact ballot model will be finalized after the security review.

---

# 10. Voting Status

A separate mechanism may be used to determine whether an eligible voter has already voted.

Conceptually:

```text
Election
    │
    └── Voter Participation
            │
            ├── eligible
            └── has_voted
```

This allows duplicate voting prevention without necessarily storing the voter's candidate choice together with their identity.

---

# 11. Audit Event

Audit events are security-critical records.

Suggested fields:

```text
id
election_id
event_type
actor_id
timestamp
metadata
previous_hash
event_hash
```

Example event types:

```text
ELECTION_CREATED
ELECTION_UPDATED
CANDIDATE_ADDED
CANDIDATE_UPDATED
ELECTION_SCHEDULED
ELECTION_OPENED
VOTE_CAST
ELECTION_CLOSED
RESULTS_PUBLISHED
ADMIN_ACTION
```

---

# 12. Hash Chain

Each audit event references the hash of the previous event.

Example:

```text
Audit Event 1
previous_hash = NULL
event_hash = H1

Audit Event 2
previous_hash = H1
event_hash = H2

Audit Event 3
previous_hash = H2
event_hash = H3
```

Conceptually:

```text
H1 → H2 → H3 → H4 → H5
```

If Event 2 changes:

```text
H1 → H2' → H3 → H4
```

The stored previous hash relationship will no longer match the calculated chain.

---

# 13. Hash Generation

The hash should be generated from a canonical representation of the event.

Conceptually:

```text
event_data =
    event_type
    + timestamp
    + election_id
    + actor_id
    + metadata
    + previous_hash
```

Then:

```text
event_hash = SHA256(event_data)
```

The implementation must ensure deterministic serialization so that the same event produces the same hash.

---

# 14. Referential Integrity

Foreign keys should be used wherever appropriate.

Examples:

```text
Candidate.election_id
        ↓
Election.id
```

```text
EligibleVoter.election_id
        ↓
Election.id
```

```text
AuditEvent.election_id
        ↓
Election.id
```

Database constraints should be preferred over relying exclusively on frontend validation.

---

# 15. Important Constraints

### Candidate uniqueness

A candidate should not be duplicated within the same election where the business rules prohibit it.

### Voter eligibility

A student should have only one eligibility record per election.

```text
UNIQUE(election_id, student_id)
```

### Election dates

The system should prevent invalid configurations such as:

```text
end_time < start_time
```

### Election state

Only valid state transitions should be accepted.

---

# 16. Vote Integrity

The backend must prevent:

```text
Same eligible voter
        ↓
Vote 1 ✓
        ↓
Vote 2 ✗
```

Duplicate voting prevention must be enforced server-side.

Frontend checks alone are insufficient.

---

# 17. Data Privacy

The database design should follow the principle:

> Store only the information required for the system to function.

In particular, the system should avoid unnecessary permanent storage of:

```text
Student Identity + Candidate Choice
```

The final implementation will undergo a privacy review before the voting module is considered complete.

---

# 18. Audit Immutability

Application-level rules should prevent ordinary users from modifying audit events.

The audit system should be treated as append-oriented.

Preferred behavior:

```text
CREATE audit event ✓

UPDATE existing audit event ✗

DELETE existing audit event ✗
```

Any administrative security action should itself generate an audit event where appropriate.

---

# 19. Example Database Flow

### Election creation

```text
Admin
  ↓
Election created
  ↓
AuditEvent generated
```

### Candidate creation

```text
Admin
  ↓
Candidate added
  ↓
AuditEvent generated
```

### Vote

```text
Eligible Voter
      ↓
Eligibility checked
      ↓
Duplicate vote checked
      ↓
Ballot recorded
      ↓
Participation updated
      ↓
AuditEvent generated
```

### Election closure

```text
Admin/System
      ↓
Election CLOSED
      ↓
AuditEvent generated
      ↓
Results calculated
```

---

# 20. Proposed PostgreSQL Tables

Initial table list:

```text
users
roles
user_roles
student_profiles
elections
candidates
eligible_voters
voter_participation
ballots
audit_events
```

Additional tables may be introduced when required by the final architecture.

---

# 21. Indexing Strategy

Indexes should be considered for frequently queried fields.

Potential indexes:

```text
users.email
student_profiles.student_id
elections.status
elections.start_time
elections.end_time
candidates.election_id
eligible_voters.election_id
audit_events.election_id
audit_events.timestamp
```

Indexes should be added based on actual query patterns rather than indiscriminately.

---

# 22. Database Development Rules

1. Use migrations for schema changes.
2. Never manually modify production schema.
3. Do not commit database passwords.
4. Use meaningful foreign-key relationships.
5. Add constraints wherever possible.
6. Test migration changes.
7. Avoid storing unnecessary personal information.
8. Do not modify audit records through ordinary CRUD operations.
9. Document major schema decisions.
10. Review privacy implications before finalizing the ballot schema.

---

# 23. Future Enhancements

Possible future database improvements:

* Partitioning for large audit logs
* Database-level audit protection
* Cryptographic signatures
* Independent audit storage
* Advanced event versioning
* Institutional multi-tenancy

---

# 24. Database Design Goal

The database should support the following principle:

```text
Secure Identity
      +
Election Integrity
      +
Duplicate Vote Prevention
      +
Ballot Privacy
      +
Auditable Operations
```

without introducing unnecessary complexity.
