# SCIENTIA NEET (UG) India — Basic OMR Portal

**Separate new project. Does not modify or connect to the existing JEE portal or its database.**

## Features
- NEET (UG) mock response sheet: Physics 45, Chemistry 45, Botany 45, Zoology 45 (Biology 90); 180 questions / 180 minutes.
- Student registration and unique registration code.
- Autosaved A/B/C/D answers and two-step submission.
- Teacher password login, student list, answer sheets, and CSV export.
- Mobile-friendly SCIENTIA navy/gold design (CSS logo placeholder; replace with licensed original logo if desired).
- **No questions are supplied**: teacher provides a separate numbered question paper.
- **No answer keys, grading, marks or scorecards** in this basic edition.

## Deploy as a NEW Render service
1. Create a **new GitHub repository** (for example `scientia-neet-mock-test`). Upload the project files preserving the `templates/` and `static/` folders.
2. Create a **new Render PostgreSQL database** and record its **internal** database URL. Do not reuse the JEE database URL.
3. Create a **new Render Web Service** connected to the new GitHub repository. Runtime: Python. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app`.
4. Add environment variables: `DATABASE_URL` = new database URL, `SECRET_KEY` = long random secret, `ADMIN_PASSWORD` = strong unique password, `COOKIE_SECURE` = `1` for Render HTTPS.
5. Deploy, register a test student, submit answers, log in at `/admin/login`, verify the answer sheet, and download `/admin/export.csv`.
6. Keep backups of the new database and exported CSV. Render free databases can expire; verify current Render terms.

## Important notes
- Do not reuse your existing JEE database: that would risk affecting old student records.
- Server controls the 180-minute limit; browser timer is only a display.
- This is an OMR **response collection** tool, not a full question-delivery or proctoring system.
- Basic starter build: review security and load testing before high-stakes or large-group use. No per-user authentication beyond the student's browser session. The server does not implement CSRF tokens or request rate limiting; add these before public launch.
- If students close the browser or switch devices, they cannot resume unless a secure resume/login feature is added.
