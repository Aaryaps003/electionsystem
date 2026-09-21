
# Campus Election 2.0 — System Architecture

## 1. Overview

Campus Election 2.0 is a secure digital campus election platform built using React, Django REST Framework, and PostgreSQL.

The architecture follows a client-server model:

```text
React Frontend
      │
      │ HTTPS / REST API
      ▼
Django REST Framework
      │
      ├── Authentication
      ├── Authorization
      ├── Election Management
      ├── Voting Engine
      ├── Result Management
      └── Audit System
      │
      ▼
PostgreSQL
```

---

# 2. Major Components

## Frontend

Technology:

* React
* Vite
* React Router
* Axios
* Tailwind CSS

Responsibilities:

* User interface
* Authentication screens
* Election browsing
* Candidate display
* Voting interface
* Admin dashboard
* Auditor dashboard
* Integrity verification visualization

The frontend must never be treated as a trusted security boundary.

All security-sensitive operations must be validated by the backend.

---

# 3. Backend

Technology:

* Python
* Django
* Django REST Framework
* JWT Authentication

Backend responsibilities:

```text
Authentication
Authorization
Election lifecycle
Voter eligibility
Voting
Results
Audit logging
Integrity verification
```

The backend is responsible for enforcing business rules.

For example:

```text
Frontend:
"Vote for candidate 7"

        ↓

Backend verifies:

✓ User authenticated
✓ User eligible
✓ Election is OPEN
✓ Candidate belongs to election
✓ User has not already voted

        ↓

Accept / Reject vote
```

---

# 4. User Roles

The system initially supports three roles.

## Voter

Can:

* Login
* View eligible elections
* View candidates
* Cast vote
* View voting confirmation
* View published results

Cannot:

* Create elections
* Modify candidates
* Access audit administration
* Access other users' ballots

---

## Election Administrator

Can:

* Create elections
* Configure election
* Add candidates
* Manage eligible voters
* Open/close election
* Publish results
* View audit information

All sensitive administrative actions should generate audit events.

---

## Auditor

Can:

* View election integrity status
* Verify audit chain
* View audit events
* Investigate integrity failures

Auditors should not automatically receive access to confidential ballot information.

---

# 5. Election State Machine

Every election follows a controlled lifecycle.

```text
             ┌──────────┐
             │  DRAFT   │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │SCHEDULED │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │   OPEN   │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │  CLOSED  │
             └────┬─────┘
                  │
                  ▼
        ┌────────────────────┐
        │ RESULTS_PUBLISHED  │
        └────────────────────┘
```

Invalid transitions must be rejected by the backend.

Example:

```text
DRAFT → OPEN              INVALID
OPEN → DRAFT              INVALID
CLOSED → OPEN             INVALID
RESULTS_PUBLISHED → OPEN  INVALID
```

---

# 6. Voting Flow

```text
Student
   │
   ▼
Login
   │
   ▼
JWT Authentication
   │
   ▼
Election Selection
   │
   ▼
Eligibility Verification
   │
   ▼
Candidate Selection
   │
   ▼
Backend Validation
   │
   ├── Not eligible → Reject
   ├── Already voted → Reject
   ├── Election closed → Reject
   └── Invalid candidate → Reject
   │
   ▼
Vote Accepted
   │
   ▼
Audit Event Created
   │
   ▼
Confirmation
```

---

# 7. Tamper-Evident Audit Architecture

The audit system is one of the core security components.

Important system events are recorded.

Examples:

```text
ELECTION_CREATED
CANDIDATE_ADDED
ELECTION_SCHEDULED
ELECTION_OPENED
VOTE_CAST
ELECTION_CLOSED
RESULTS_PUBLISHED
ADMIN_ACTION
```

Each audit event contains a reference to the previous event.

Conceptually:

```text
Event 1
Hash: H1

       ↓

Event 2
Previous Hash: H1
Hash: H2

       ↓

Event 3
Previous Hash: H2
Hash: H3
```

If Event 2 is modified:

```text
Event 1
   ↓
Event 2 ❌
   ↓
Event 3 ❌
```

The integrity verifier should identify the mismatch.

---

# 8. Ballot Privacy Architecture

The system should avoid unnecessarily creating a direct relationship between:

```text
Student → Candidate Choice
```

Eligibility verification and ballot storage should therefore be treated as separate concerns.

Conceptually:

```text
              ┌──────────────────┐
              │ Student Identity │
              └────────┬─────────┘
                       │
                       ▼
                Eligibility
                  Verification
                       │
                       ▼
                 Voting Status


              ┌──────────────────┐
              │      Ballot      │
              └────────┬─────────┘
                       │
                       ▼
                Candidate Choice
```

The final privacy-preserving implementation will be decided during database and security design.

---

# 9. API Architecture

All frontend-backend communication will use REST APIs.

Base URL:

```text
/api/
```

Authentication:

```text
/api/auth/
```

Elections:

```text
/api/elections/
```

Candidates:

```text
/api/candidates/
```

Voting:

```text
/api/ballots/
```

Results:

```text
/api/results/
```

Audit:

```text
/api/audit/
```

Integrity verification:

```text
/api/audit/verify/
```

---

# 10. Security Architecture

The following principles must be followed.

### Authentication

JWT-based authentication.

### Authorization

Role-based access control.

### Password Security

Passwords must never be stored in plaintext.

### API Security

Sensitive operations must be validated server-side.

### Input Validation

All user-provided data must be validated.

### Rate Limiting

Sensitive endpoints such as login and voting should have appropriate rate limits.

### Secrets

Secrets must be stored in environment variables.

Never commit:

```text
.env
API keys
JWT secrets
database passwords
private keys
```

---

# 11. Frontend Architecture

Suggested structure:

```text
frontend/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── services/
│   ├── hooks/
│   ├── context/
│   ├── utils/
│   └── routes/
│
├── public/
└── package.json
```

Pages:

```text
Login
Dashboard
ElectionDetails
Voting
VoteConfirmation
AdminDashboard
ElectionManagement
AuditDashboard
Results
```

---

# 12. Backend Architecture

Suggested Django structure:

```text
backend/
│
├── config/
│
├── accounts/
│
├── elections/
│
├── voting/
│
├── audit/
│
├── results/
│
├── manage.py
└── requirements.txt
```

Responsibilities:

### accounts

Authentication, users and roles.

### elections

Election lifecycle and candidate management.

### voting

Eligibility and ballot processing.

### audit

Audit events, hashing and integrity verification.

### results

Vote counting and result publication.

---

# 13. Deployment Architecture

Initial deployment target:

```text
                 Internet
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
       Vercel              Backend
       React               Django
                              │
                              ▼
                         PostgreSQL
```

Environment-specific configuration should be used for development and production.

---

# 14. Development Principles

The team should follow these rules:

1. Never push directly to `main`.
2. Create feature branches.
3. Make small, meaningful commits.
4. Open pull requests for major changes.
5. Test backend changes before merging.
6. Never commit secrets.
7. Document important architectural decisions.
8. Keep frontend and backend responsibilities separate.
9. Security-sensitive logic belongs on the backend.
10. Every team member should understand the overall architecture.

---

# 15. Initial Development Order

```text
1. Project setup
       ↓
2. Database design
       ↓
3. Authentication
       ↓
4. Election management
       ↓
5. Voter eligibility
       ↓
6. Voting engine
       ↓
7. Audit system
       ↓
8. Integrity verification
       ↓
9. React dashboards
       ↓
10. Integration testing
       ↓
11. Deployment
```

---

# 16. Architecture Goal

The goal is not simply to create an online voting form.

The goal is to build a system where:

```text
Authentication
      +
Authorization
      +
Controlled Election Lifecycle
      +
Ballot Privacy
      +
Tamper-Evident Auditing
      +
Integrity Verification
```

work together as one secure election platform.
