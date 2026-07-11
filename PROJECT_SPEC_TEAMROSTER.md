# Project Spec: "TeamRoster" — Team Member Registration App

**Purpose of this document:** Locked-scope spec for a course final project. If a feature isn't listed under "In Scope," don't build it. This spec follows the same simplicity philosophy as the EventReg demo, but the CRUD target here is a **list of members belonging to a team captain**, not the captain's own profile.

**Stack:** FastAPI (Python) + React (Vite) + Tailwind + shadcn/ui + SQLAlchemy + PostgreSQL (Neon) + JWT auth + monorepo (no CORS) + DigitalOcean deployment.

---

## 1. What This App Is

A team roster registration site. A visitor can:
1. Sign up as a **Team Captain**, naming their team at signup
2. Log in
3. See a dashboard listing all **Members** they've added to their team
4. **Create, Read, Update, and Delete** individual member records (NISN, Full Name, Birthdate, Gender)

That's the entire product. One captain account = one team = an unlimited list of members, fully CRUD-able. There is no admin panel, no cross-team visibility, no member login of their own (members are just records the captain manages — they don't have accounts).

---

## 2. Explicit Non-Goals (Do Not Build These)

- ❌ Admin dashboard / admin authorization / admin roles
- ❌ Member accounts or member login — members are data records only, not users
- ❌ Multiple teams per captain — one captain, one team, set at signup
- ❌ Password reset / forgot password flow
- ❌ Email verification or sending emails of any kind
- ❌ OAuth / social login
- ❌ File uploads (no member photos)
- ❌ Pagination, search, or filtering of the member list
- ❌ Real-time features (websockets, polling, notifications)
- ❌ Payment processing
- ❌ Viewing or editing other captains' teams — strictly scoped to `current_user`
- ❌ CORS configuration in the deployed version — same-origin, per Section 5
- ❌ Refresh tokens / token rotation — single JWT, fixed expiry
- ❌ Testing frameworks, CI/CD pipelines, Docker
- ❌ State management libraries — `useState`/`useContext` only
- ❌ TypeScript — plain JavaScript only

---

## 3. User-Facing Pages (Frontend Scope)

| Route | Page | Auth required? | Purpose |
|---|---|---|---|
| `/` | Home / Landing | No | Static page introducing the app, with a shadcn `Button` linking to `/register`. |
| `/register` | Sign Up | No | Form: **team name**, email, password. On submit, calls signup endpoint. On success, redirect to `/login`. |
| `/login` | Log In | No | Form: email, password. On submit, stores JWT in `localStorage`, redirects to `/dashboard`. |
| `/dashboard` | Team Dashboard | Yes | Shows the team name and a `Card`/table listing all members (Full Name, NISN, Gender, Birthdate) with **Edit** and **Delete** buttons per row, plus an "Add Member" `Button`. Empty state: "No members yet — add your first one." |
| `/members/new` | Add Member | Yes | `AddMember.jsx` — form with the four fields (see 4.1), all starting blank. On submit, `POST`s to create the member and redirects to `/dashboard`. |
| `/members/:id/edit` | Edit Member | Yes | `EditMember.jsx` — its own component, not shared with Add. On mount, `GET /api/members/{id}` to pre-fill the four fields. On submit, `PUT`s to update and redirects to `/dashboard`. Must verify the member belongs to the logged-in captain (403 otherwise). |

**Navigation:** Shared `Navbar`. Logged-out: Home, Login, Register. Logged-in: Dashboard, Logout (show team name in the navbar too, e.g. "Team: Garuda FC").

**Delete confirmation:** Use a plain `window.confirm("Delete this member?")` — no shadcn `Dialog`, to keep the component list at five (see Section 7).

**Routing library:** `react-router-dom` with a `<ProtectedRoute>` wrapper for `/dashboard`, `/members/new`, `/members/:id/edit` — redirects to `/login` if no token in `localStorage`.

---

## 4. Backend Scope (API)

Two resources: `User` (the captain) and `Member`.

### 4.1 Data Models (SQLAlchemy)

**User** (Team Captain)
| Field | Type | Notes |
|---|---|---|
| id | Integer, PK | autoincrement |
| team_name | String | required, set at signup |
| email | String | required, unique |
| hashed_password | String | bcrypt via `passlib` |
| created_at | DateTime | default `now()` |

**Member**
| Field | Type | Notes |
|---|---|---|
| id | Integer, PK | autoincrement |
| captain_id | Integer, FK → User.id | owner — every query filters on this |
| nisn | String | required, **unique** (a real NISN belongs to one student, so it's unique across the whole table — not just within a team) |
| full_name | String | required |
| birthdate | Date | required |
| gender | String | required — radio input, values `"male"` / `"female"` |
| created_at | DateTime | default `now()` |

`nisn` gets a `unique=True` constraint at the database level. `POST /api/members` and `PUT /api/members/{id}` return **400** if the NISN is already taken by another member (any team) — this also teaches students how to surface a DB `IntegrityError` as a clean 400 response instead of a 500.

### 4.2 Endpoints

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| POST | `/api/auth/signup` | No | `{team_name, email, password}` | `{id, team_name, email}` (201) or 400 if email taken |
| POST | `/api/auth/login` | No | `{email, password}` | `{access_token, token_type}` (200) or 401 if invalid |
| GET | `/api/members` | Yes | — | List of members where `captain_id == current_user.id` |
| POST | `/api/members` | Yes | `{nisn, full_name, birthdate, gender}` | Created member (201) |
| GET | `/api/members/{id}` | Yes | — | Single member (404/403 if not found or not owned) — powers the edit form |
| PUT | `/api/members/{id}` | Yes | `{nisn, full_name, birthdate, gender}` | Updated member — 403 if not owned |
| DELETE | `/api/members/{id}` | Yes | — | 204 on success — 403 if not owned |

This is genuinely "full CRUD" on `Member` (unlike EventReg's deliberately partial CRUD) — that's the point of the assignment. Every member endpoint must filter/check by `captain_id` server-side; don't trust the frontend to only show the right rows.

### 4.3 Auth Mechanism — JWT

Same pattern as EventReg:
- `python-jose` or `pyjwt`, secret key from env var
- Token expiry: 24 hours
- Payload: `{sub: user_id, exp: ...}`
- Frontend stores token in `localStorage`, sends `Authorization: Bearer <token>` on every `/api/members*` and `/api/me`-style call
- Backend `get_current_user` dependency decodes token, loads the `User`, and every member route uses that `User.id` to scope the query — this is the actual "auth logic" lesson of the project (ownership checks, not just "is logged in")
- Same XSS-in-localStorage caveat as EventReg — worth repeating to students as a teaching moment, not hiding it

---

## 5. Monorepo Architecture (No CORS)

Identical pattern to EventReg — FastAPI serves the built React static files in production; CORS middleware exists only as pre-written boilerplate for local dev (`localhost:5173` ↔ `localhost:8000`).

```
teamroster/
├── backend/
│   ├── main.py
│   ├── models.py             # User, Member
│   ├── schemas.py            # Pydantic schemas incl. MemberCreate/MemberOut
│   ├── auth.py                # password hashing, JWT create/decode
│   ├── database.py
│   ├── routers/
│   │   ├── auth.py            # signup, login
│   │   └── members.py         # GET/POST /api/members, GET/PUT/DELETE /api/members/{id}
│   ├── requirements.txt
│   └── .env                  # DATABASE_URL, JWT_SECRET (gitignored)
└── frontend/
    ├── src/
    │   ├── pages/              # Home, Register, Login, Dashboard, AddMember.jsx, EditMember.jsx
    │   ├── components/         # Navbar.jsx, ProtectedRoute.jsx, MemberRow.jsx
    │   ├── lib/api.js          # fetch wrapper, reads token from localStorage
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

`AddMember.jsx` and `EditMember.jsx` are separate components with their own copies of the form JSX. This duplicates markup, but it's the simpler version for a final project: each page only has to reason about one HTTP verb (`POST` vs `PUT`) and Edit is the only one that needs a `useEffect` to fetch-and-prefill — students can build and test Add fully before touching Edit at all, rather than juggling an `isEditing` conditional inside one shared component from the start.

---

## 6. Environment & Config

Same as EventReg — `.env` in `backend/`, never committed:
```
DATABASE_URL=postgresql://<neon-connection-string>
JWT_SECRET=<random-secret-string>
```

---

## 7. Styling Scope (Tailwind + shadcn)

Six-component budget (one more than EventReg's five, since this project has a real use for `RadioGroup`):

- `Button` — every page
- `Input` + `Label` — Register/Login/AddMember/EditMember (including the birthdate `<input type="date">`)
- `Card` — wraps each page's main content, and the Dashboard's member list
- `Badge` — used on Dashboard for gender (e.g. "Male" / "Female" badge next to each name)
- `RadioGroup` (+ `RadioGroupItem`) — used on AddMember/EditMember for the gender field, two options: Male / Female

No `Dialog`, `Toast`, `Tabs`, `DropdownMenu`, or `Table` component — the member list is a `Card` containing plain `<div>` rows, and delete confirmation stays a plain `window.confirm(...)` (Section 3), same "keep it minimal" philosophy as EventReg.

---

## 8. Deployment Scope (DigitalOcean)

Identical to EventReg Section 8 — DigitalOcean App Platform, same build/run commands, same env vars, one app/one environment/one URL.

---

## 9. Definition of Done

Complete when a brand-new visitor can, in this order, on the deployed URL:
1. Land on `/`, click through to `/register`
2. Sign up with a team name, email, and password
3. Get redirected to `/login` and log in
4. Land on `/dashboard`, see their team name and an empty member list
5. Click "Add Member," fill in NISN / Full Name / Birthdate / Gender, submit
6. Get redirected back to `/dashboard`, see the new member in the list
7. Click "Edit" on that member, change a field, save, see the update reflected
8. Add a second member, then click "Delete" on the first — confirm it's gone and the second remains
9. Refresh the page — still logged in, member list persists
10. Log out, get redirected to `/`, confirm `/dashboard` is no longer reachable without logging back in


