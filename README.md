# 🗳️ Campus Election 2.0

### Secure, Auditable & Tamper-Evident Digital Election Platform

Campus Election 2.0 is a full-stack digital election platform designed for **college and university elections**.

The project was inspired by a simple real-world observation: college elections are sometimes conducted using basic online forms where voter eligibility, duplicate voting prevention, ballot privacy, and post-election data integrity can be difficult to independently verify.

Campus Election 2.0 explores how these problems can be addressed through **proper authentication, authorization, secure voting workflows, cryptographic integrity verification, and tamper-evident audit logs**.

> **Important:** This is an academic/software-engineering project and is not intended to certify or replace legally regulated election systems.

---

## 🎯 Problem Statement

A basic online voting form can provide a convenient way to collect votes, but a complete election system requires more than collecting responses.

A secure campus election system should consider:

* Who is eligible to vote?
* Can one person vote more than once?
* Can unauthorized users access the election?
* Can election configuration be changed after voting begins?
* Can election records be modified after being stored?
* Can administrators alter data without leaving evidence?
* Can election activity be audited?
* Can voter identity be separated from ballot choice?
* Can the system detect unauthorized modification?

Campus Election 2.0 aims to address these concerns through a structured full-stack architecture.

---

# 🚀 Project Objectives

### Primary Objectives

* Build a secure digital campus election platform.
* Implement authenticated and authorized voting.
* Prevent duplicate voting.
* Separate voter eligibility from ballot information wherever possible.
* Maintain a tamper-evident audit trail.
* Detect unauthorized modification of election records.
* Provide election administration and auditing dashboards.
* Maintain clear election lifecycle states.
* Provide transparent integrity verification.

---

# ⭐ Key Features

## 👨‍🎓 Voter

* Secure login
* Voter eligibility verification
* View active elections
* View candidate information
* Cast a ballot
* Prevent duplicate voting
* Receive vote confirmation
* View election status
* View published results after election closure

---

## 🛠️ Election Administrator

* Create elections
* Configure election dates
* Add/edit candidates before election lock
* Import/manage eligible voters
* Open and close elections
* Monitor participation statistics
* Publish results
* View election audit logs
* Run election integrity verification

---

## 🔍 Auditor

The auditor role is designed to independently verify election-system integrity without unnecessarily exposing confidential ballot information.

Features:

* View election integrity status
* Verify audit chain
* View audit events
* Detect broken hash chains
* Identify suspicious modifications
* Verify election configuration history
* Review election lifecycle transitions

---

# 🛡️ Tamper-Evident Audit System

One of the core features of Campus Election 2.0 is a **cryptographically linked audit ledger**.

Important election events are recorded as audit events.

Example:

```text
Election Created
       ↓
Candidate Added
       ↓
Election Scheduled
       ↓
Election Opened
       ↓
Vote Cast
       ↓
Vote Cast
       ↓
Election Closed
       ↓
Results Published
```

Each audit event contains a cryptographic reference to the previous event.

Conceptually:

```text
Event 1
   │
   └── Hash: A91F8C...

Event 2
   │
   ├── Previous Hash: A91F8C...
   └── Hash: 72B4E1...

Event 3
   │
   ├── Previous Hash: 72B4E1...
   └── Hash: 91D2AC...
```

If historical data is modified, the calculated hash will no longer match the recorded hash.

The system can therefore report:

```text
Election Integrity Verification

Event #1841     ✓
Event #1842     ✓
Event #1843     ❌ HASH MISMATCH

⚠ Possible data tampering detected.
```

### Important Design Principle

This project does **not** require storing votes on a public blockchain.

The objective is to implement a **tamper-evident audit mechanism** using cryptographic hashing and a controlled backend architecture.

---

# 🔐 Ballot Privacy

Security is not only about preventing modification.

The system must also avoid unnecessarily exposing the relationship between:

```text
Student → Candidate Choice
```

The architecture should therefore distinguish between:

### Eligibility

```text
Student
   ↓
Is this student allowed to vote?
```

and:

### Ballot

```text
Anonymous/Protected Ballot
   ↓
Candidate Choice
```

The exact implementation will be finalized during system design.

---

# 🔄 Election Lifecycle

An election follows a controlled state machine:

```text
DRAFT
  ↓
SCHEDULED
  ↓
OPEN
  ↓
CLOSED
  ↓
RESULTS_PUBLISHED
```

Invalid state transitions should be rejected.

For example:

```text
DRAFT → OPEN              ❌
OPEN → DRAFT              ❌
CLOSED → OPEN             ❌
RESULTS_PUBLISHED → OPEN  ❌
```

unless an explicitly defined administrative recovery process exists.

Every important state transition should generate an audit event.

---

# 🏗️ System Architecture

```text
                    ┌───────────────────────┐
                    │      React Client     │
                    │                       │
                    │  Voter Dashboard      │
                    │  Admin Dashboard      │
                    │  Auditor Dashboard    │
                    └───────────┬───────────┘
                                │
                             REST API
                                │
                    ┌───────────▼───────────┐
                    │    Django Backend     │
                    │                       │
                    │ Django REST Framework │
                    │ Authentication        │
                    │ Authorization         │
                    │ Election Logic        │
                    │ Voting Logic          │
                    │ Audit System          │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │      PostgreSQL       │
                    │                       │
                    │ Users                 │
                    │ Elections             │
                    │ Candidates            │
                    │ Ballots               │
                    │ Audit Events          │
                    └───────────────────────┘
```

---

# 🧰 Technology Stack

## Frontend

* React
* Vite
* React Router
* Axios
* Tailwind CSS
* Recharts

## Backend

* Python
* Django
* Django REST Framework
* JWT Authentication

## Database

* PostgreSQL

## Security

* Password hashing
* JWT authentication
* Role-Based Access Control
* Cryptographic hashing
* Tamper-evident audit logging
* API validation
* Rate limiting

## Development Tools

* Git
* GitHub
* VS Code
* Postman / Bruno

---

# 🗄️ Initial Data Model

The exact schema will be finalized during development.

Initial entities:

```text
User
 │
 ├── StudentProfile
 │
 └── Role

Election
 │
 ├── Candidate
 ├── EligibleVoter
 ├── Ballot
 └── AuditEvent
```

### Candidate

Stores information about candidates participating in an election.

### EligibleVoter

Determines whether a user is allowed to participate in a particular election.

### Ballot

Stores the election choice while following the project's privacy requirements.

### AuditEvent

Stores security-sensitive election events.

Example fields:

```text
id
event_type
timestamp
previous_hash
event_hash
metadata
```

---

# 🔌 Planned API Structure

```text
/api/auth/
/api/users/

/api/elections/
/api/elections/{id}/

/api/candidates/

/api/voters/

/api/ballots/

/api/results/

/api/audit/

/api/audit/verify/
```

Example endpoints:

```text
POST   /api/auth/login/
POST   /api/auth/logout/

GET    /api/elections/
POST   /api/elections/

GET    /api/elections/{id}/
PATCH  /api/elections/{id}/

GET    /api/elections/{id}/candidates/

POST   /api/elections/{id}/vote/

GET    /api/elections/{id}/results/

GET    /api/elections/{id}/audit/

POST   /api/elections/{id}/audit/verify/
```

The final API specification will be documented before frontend-backend integration.

---

# 📊 Admin Dashboard

The administrator dashboard should provide information such as:

```text
Election: Student Council Election 2026

Status:
● LIVE

Eligible Voters:     1,284
Votes Cast:            937
Turnout:             72.97%

Audit Events:        4,821

Integrity:
✓ VERIFIED
```

Candidate vote counts should only be exposed according to the election's configured result-publication policy.

---

# 🚨 Tampering Detection Demo

The project should include a controlled demonstration showing what happens when election data is modified outside the expected workflow.

Example:

Original:

```text
Candidate A → 152 votes
```

Simulated unauthorized modification:

```text
Candidate A → 252 votes
```

Integrity verification:

```text
Verifying audit chain...

Event #1841 ✓
Event #1842 ✓
Event #1843 ❌

Expected Hash:
91AF72...

Calculated Hash:
BC192A...

⚠ POSSIBLE DATA TAMPERING DETECTED
```

This demonstration will be one of the major project showcases.

---

# 👥 Team Structure

Suggested division of responsibilities:

### Member 1 — Backend & Security

* Django project setup
* REST APIs
* Authentication
* Authorization
* Election lifecycle
* Voting logic

### Member 2 — Frontend

* React setup
* Routing
* Login/register UI
* Voter dashboard
* Voting interface
* Admin dashboard

### Member 3 — Database & Audit System

* PostgreSQL schema
* Database relationships
* Audit-event system
* Hash-chain implementation
* Integrity verification

### Member 4 — Testing & Integration

* API testing
* Security testing
* Frontend/backend integration
* Edge cases
* Documentation
* Deployment

> Responsibilities can overlap. Every team member should understand the complete system architecture rather than only their assigned module.

---

# 📅 Development Roadmap

## Phase 1 — System Design

* [ ] Finalize requirements
* [ ] Create architecture diagram
* [ ] Design ER diagram
* [ ] Define election lifecycle
* [ ] Define security model
* [ ] Define API specification

## Phase 2 — Backend

* [ ] Django setup
* [ ] PostgreSQL setup
* [ ] User authentication
* [ ] Role-based authorization
* [ ] Election CRUD
* [ ] Candidate management
* [ ] Voter eligibility
* [ ] Voting API

## Phase 3 — Audit & Security

* [ ] Audit event model
* [ ] Hash generation
* [ ] Hash chaining
* [ ] Integrity verification
* [ ] Tampering simulation
* [ ] Rate limiting
* [ ] Security testing

## Phase 4 — Frontend

* [ ] React setup
* [ ] Authentication screens
* [ ] Voter dashboard
* [ ] Election page
* [ ] Voting interface
* [ ] Admin dashboard
* [ ] Auditor dashboard
* [ ] Integrity visualization

## Phase 5 — Integration

* [ ] Connect React + Django
* [ ] API error handling
* [ ] Authentication integration
* [ ] Role-based routing
* [ ] End-to-end testing

## Phase 6 — Deployment

* [ ] Production database
* [ ] Backend deployment
* [ ] Frontend deployment
* [ ] Environment variables
* [ ] Security configuration
* [ ] Final documentation

---

# 🌿 Git Workflow

Do not directly push development work to `main`.

Recommended workflow:

```text
main
 │
 ├── develop
 │
 ├── feature/authentication
 ├── feature/election-management
 ├── feature/voting
 ├── feature/audit-ledger
 └── feature/frontend-dashboard
```

### Commit examples

```text
feat: add election creation API
feat: implement voter eligibility
feat: add audit hash chain
fix: prevent duplicate voting
test: add election lifecycle tests
docs: update API documentation
```

---

# 🔒 Security Principles

The project should follow these principles:

1. **Never trust the frontend.**
2. Validate all important operations on the backend.
3. Enforce authorization server-side.
4. Never store plaintext passwords.
5. Never expose secrets in source code.
6. Do not unnecessarily expose voter identity alongside ballot choice.
7. Record security-sensitive actions in the audit system.
8. Validate election state before accepting operations.
9. Rate-limit sensitive endpoints.
10. Treat audit logs as security-critical data.

---

# 🧪 Testing Requirements

Testing should cover:

### Authentication

* Valid login
* Invalid login
* Expired token
* Unauthorized API access

### Voting

* Eligible voter
* Ineligible voter
* Duplicate voting attempt
* Election not open
* Election already closed

### Election Management

* Invalid state transition
* Unauthorized modification
* Candidate changes after election lock

### Audit System

* Valid hash chain
* Modified event
* Deleted event
* Reordered event
* Invalid previous hash

---

# 📁 Proposed Repository Structure

```text
campus-election-2.0/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   └── package.json
│
├── backend/
│   ├── config/
│   ├── accounts/
│   ├── elections/
│   ├── voting/
│   ├── audit/
│   ├── requirements.txt
│   └── manage.py
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── security.md
│   └── database.md
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# 🧑‍💻 Local Development

## Backend

```bash
git clone <repository-url>
cd campus-election-2.0

cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Backend:

```text
http://127.0.0.1:8000/
```

## Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173/
```

---

# ⚙️ Environment Variables

Never commit `.env` files containing secrets.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=your-postgresql-url

JWT_SECRET=your-jwt-secret

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Use `.env.example` for team members.

---

# 🎯 Definition of Done

The project will be considered complete when a user can:

```text
Create Election
      ↓
Register/Import Eligible Voters
      ↓
Add Candidates
      ↓
Schedule Election
      ↓
Open Election
      ↓
Authenticate Voter
      ↓
Verify Eligibility
      ↓
Cast Vote
      ↓
Generate Audit Event
      ↓
Close Election
      ↓
Verify Integrity
      ↓
Publish Results
```

And the system can demonstrate:

> **If protected election data is modified outside the intended workflow, the integrity verification mechanism detects the inconsistency.**

---

# 💡 Future Enhancements

Possible future versions may include:

* Institution SSO
* QR-based voter verification
* Email/SMS notifications
* Digital signatures
* Hardware/security-key authentication
* Multi-factor authentication
* Independent election observer dashboard
* Advanced anomaly detection
* Distributed audit storage
* Accessibility improvements
* Mobile application

---

# ⚠️ Disclaimer

Campus Election 2.0 is an academic software project intended to explore secure digital voting architecture.

It should **not** be considered a certified voting system or used for legally regulated public elections without extensive independent security audits, formal verification, privacy review, accessibility testing, operational controls, and compliance with applicable laws and regulations.

---

# 👨‍💻 Team

**Campus Election 2.0**

Built as a collaborative full-stack software engineering project using:

**React + Django + PostgreSQL + Cryptographic Integrity Verification**

---

## ⭐ Project Vision

> **Make digital campus elections more accountable, auditable, privacy-conscious, and resistant to unauthorized modification.**

---
