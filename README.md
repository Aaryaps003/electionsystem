# Campus Election 2.0

A full-stack campus election application built with React, Vite, Django, and Django REST Framework.

## Features

- Administrator login
- Voter management and password resets
- Candidate management
- Voter login and ballot access
- Vote submission with duplicate-voting prevention
- Election results and turnout statistics
- XML results export
- Live result updates using Django Channels

## Technology Stack

**Frontend:** React, Vite, JavaScript, CSS

**Backend:** Python, Django, Django REST Framework, Django Channels

**Database:** SQLite for local development

## Prerequisites

- Python compatible with the installed Django version
- Node.js and npm

## Run the Backend

Open PowerShell in the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

Backend URL: http://127.0.0.1:8000/

## Run the Frontend

Open a second terminal in the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, usually http://localhost:5173/.

## Important Security Notes

- Configure secrets through environment variables.
- Change any default administrator credentials before deployment.
- Use production-grade settings, HTTPS, and an appropriately configured database before deployment.
- The current application is an academic project, not a certified election system.

## Repository Structure

```text
backend/
  config/
  election/
  manage.py
  requirements.txt

frontend/
  public/
  src/
  package.json

docs/
README.md
.gitignore
```
