# Healthcare.ai Backend

FastAPI backend for **Kara**, a voice AI healthcare receptionist. It exposes the booking APIs and the agent tools the voice agent calls (`identify_user`, `fetch_slots`, `book_appointment`, `retrieve_appointments`, `cancel_appointment`, `modify_appointment`, `end_conversation`), a reminder notification scheduler, and an embedding-based text-to-SQL assistant with a self-healing query loop.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2.0 on SQLite
- Pydantic v2 / pydantic-settings
- NumPy (hashing embeddings + in-memory vector index)

## Running locally

Requires Python 3.10 – 3.13.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On startup the app creates the SQLite database, seeds demo patients and appointments, trains the query engine, runs a self-check and starts the notification scheduler. When everything works you will see:

```
Healthcare.ai backend is ready
```

Interactive docs: http://127.0.0.1:8000/docs

## Project layout

```
app/
  agent/        voice agent tool registry
  api/          routers and dependencies
  core/         settings, constants, exceptions, logging
  db/           engine, session, schema creation and seeding
  models/       SQLAlchemy models
  schemas/      Pydantic request/response models
  services/     booking, slots, notifications, embeddings, query engine
```

## Key endpoints (prefix `/api/v1`)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/patients` | Register a patient |
| GET | `/patients/{phone}` | Identify a patient |
| GET | `/appointments/slots` | Free slots for a department and date |
| POST | `/appointments` | Book an appointment |
| GET | `/appointments?phone=` | List a patient's appointments |
| PATCH | `/appointments/{id}` | Reschedule |
| DELETE | `/appointments/{id}` | Cancel |
| GET | `/notifications?phone=` | Patient reminders |
| POST | `/notifications/{id}/read` | Mark a reminder as read |
| GET | `/assistant/tools` | Registered agent tools |
| POST | `/assistant/tools/{name}` | Invoke an agent tool |
| POST | `/assistant/query` | Ask a natural-language question about the data |
