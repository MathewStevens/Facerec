# Face Search --- Complete Agent Implementation Plan

**Purpose:** Give an AI coding agent a complete, staged plan to build,
test, containerize, deploy, and document a face-search API from scratch.

-   **Daily time:** approximately 1 hour
-   **Target duration:** 6 weeks / 42 learning sessions; extend as
    needed
-   **Developer environment:** Windows, Git Bash, VS Code
-   **Python management:** `uv` only; prefer `uv add`, `uv run`, and
    `uv sync`
-   **Core stack:** Python 3.12, FastAPI, Pydantic Settings, SQLAlchemy,
    psycopg 3, PostgreSQL, pgvector, Alembic, InsightFace, ONNX Runtime,
    OpenCV, Docker, Docker Compose, GitHub, GitHub Actions, GitHub
    Container Registry (GHCR), Pytest, HTTPX, Ruff
-   **Deployment target:** initially a Linux VPS with Docker Compose and
    Caddy for HTTPS; select and approve any paid provider before
    provisioning
-   **Primary goal:** upload a photo and find other photos in a
    consented collection containing the same person

> Agent instruction: work incrementally. Do not generate the entire
> application in one shot. Inspect the repository and current
> environment first, explain each step in beginner-friendly language,
> make small changes, run the relevant checks, and stop when a
> prerequisite fails. Never claim a command succeeded unless its output
> confirms success.

------------------------------------------------------------------------

## 1. Current environment and immediate status

The developer reported these Git Bash outputs:

``` text
git version 2.53.0.windows.3
uv 0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)
Python 3.12.3
Docker version 29.4.1, build 055a478
Docker Compose version v5.1.3
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

Interpretation: - Git, `uv`, Python 3.12, Docker CLI, and Docker Compose
are installed. - Docker CLI cannot connect to Docker Desktop's Linux
engine. This usually means Docker Desktop is not running, is still
starting, or its WSL 2 backend needs attention. Do not reinstall Docker
as the first step. - The terminal was at `/f/Face rec`. The intended
project path previously discussed was `/f/project/FaceSearch`. **Do not
assume either location is correct or create a duplicate project. Ask the
developer to confirm the desired folder and inspect it first.**

### Immediate first actions

1.  Ask the developer to launch Docker Desktop and wait for it to finish
    starting.

2.  From Git Bash, retry:

    ``` bash
    docker info
    docker ps
    ```

3.  If Docker Desktop fails to start, ask the developer to run these
    commands in **PowerShell** and share the output:

    ``` powershell
    wsl --version
    wsl --status
    wsl --list --verbose
    ```

4.  Diagnose from the actual output before proposing changes. Avoid
    destructive WSL/Docker reset commands.

5.  Confirm the intended project folder and inspect its contents before
    running `uv init`, `git init`, or creating files. Preserve existing
    user work.

Do not block all Python/API work on Docker being fixed; the first health
endpoint and tests can run locally. Docker becomes required for the
database/Compose milestones.

------------------------------------------------------------------------

## 2. Product goal and expected behavior

A user uploads a photo. The system detects faces and generates a
512-dimensional embedding for each face. It stores photo metadata and
embeddings. A query photo is processed the same way, then pgvector
retrieves nearby embeddings. Results are grouped by photo, ranked, and
filtered using a threshold calibrated against a labeled test set.

Conceptual flow:

``` text
Photo upload
  -> validate image
  -> hash and save file
  -> detect faces
  -> create one embedding per detected face
  -> save photo metadata + face vectors in PostgreSQL/pgvector

Search photo
  -> validate image
  -> detect the largest face (initial implementation)
  -> create query embedding
  -> vector similarity search
  -> group hits by photo and keep best score per photo
  -> apply calibrated threshold
  -> return ranked matches
```

### API contract

  -----------------------------------------------------------------------------
  Method                  Endpoint                      Purpose
  ----------------------- ----------------------------- -----------------------
  `GET`                   `/api/v1/health`              Report API and database
                                                        health

  `POST`                  `/api/v1/photos`              Upload a photo and
                                                        persist its detected
                                                        faces

  `GET`                   `/api/v1/photos`              Paginated photo listing

  `DELETE`                `/api/v1/photos/{photo_id}`   Delete photo metadata,
                                                        face rows, and stored
                                                        file

  `POST`                  `/api/v1/search`              Search for photos with
                                                        similar faces
  -----------------------------------------------------------------------------

Use explicit Pydantic request/response schemas. Keep error responses
predictable and documented in Swagger (`/docs`).

### Architecture decisions

-   Use synchronous SQLAlchemy sessions and `psycopg` 3 initially; keep
    endpoints as plain `def` where appropriate.
-   Define a `FaceEmbedder` interface/protocol and provide:
    -   a real InsightFace implementation for local/manual use;
    -   a deterministic fake embedder for tests and CI.
-   Do not download or load the real model during ordinary CI tests.
-   Store image files on disk under a persistent Docker volume; store
    metadata and embeddings in PostgreSQL.
-   Use a unique content hash to prevent duplicate uploads.
-   Use Alembic for all schema changes; do not rely on `create_all()` as
    the production migration strategy.
-   No Redis, queue, distributed architecture, or complex account system
    for v1.
-   Add a simple API-key header before public production use, excluding
    health only if documented and desired.
-   Do not expose PostgreSQL publicly.
-   Treat face images and face embeddings as sensitive biometric data.

------------------------------------------------------------------------

## 3. Required safety, privacy, and engineering rules

1.  Use only images with appropriate consent or a permitted public
    dataset. Check the applicable dataset license and terms.
2.  Do not use the system for covert identification or surveillance.
    Make the collection purpose and access controls clear.
3.  Never commit `.env`, real API keys, face images, uploads, database
    dumps, private test images, or model cache artifacts.
4.  Never expose PostgreSQL to the public internet. In production, only
    the reverse proxy/web entry points should be public.
5.  Validate image type, file size, and decodeability. Do not trust a
    filename extension alone.
6.  Prevent path traversal: generate server-side storage names; do not
    join arbitrary client-supplied paths into storage paths.
7.  Delete stored files and related database records consistently.
    Handle partial failures so orphaned files/rows can be repaired or
    detected.
8.  Keep dependencies pinned by `uv.lock`; commit that lockfile.
9.  Never store production secrets in source code, Docker image layers,
    logs, README examples, or GitHub workflow files. Use server
    environment files and GitHub Secrets.
10. Avoid logging raw face embeddings, image contents, API keys, or
    unnecessary personal information.
11. Explain model limitations and do not describe similarity results as
    certain identity proof.
12. Before destructive commands (volume deletion, reset, database drop,
    force push), explain the risk and ask for explicit approval.
13. Use small, understandable changes and report exactly which files
    were created/changed and which tests were run.

------------------------------------------------------------------------

## 4. Repository layout

Build toward this structure progressively; do not create empty files for
every future feature on Day 1.

``` text
FaceSearch/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   ├── photos.py
│   │   └── search.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/
│   │   ├── photo.py
│   │   └── face.py
│   ├── schemas/
│   │   ├── photo.py
│   │   └── search.py
│   └── services/
│       ├── faces.py
│       ├── photo_service.py
│       └── search_service.py
├── evals/
│   └── labels.csv
├── scripts/
│   ├── ingest_folder.py
│   └── calibrate.py
├── tests/
│   ├── test_health.py
│   ├── test_photos.py
│   ├── test_search.py
│   └── test_db.py
├── docs/
│   ├── architecture.md
│   ├── calibration.md
│   └── deployment.md
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

------------------------------------------------------------------------

## 5. Environment setup and terminal conventions

### Use Git Bash as the primary terminal

Windows drive paths map as follows:

-   `F:\project\FaceSearch` becomes `/f/project/FaceSearch` in Git Bash.
-   Use Git Bash for Git and most `uv` commands.
-   Use PowerShell for Windows-specific diagnostic commands when
    necessary.
-   Use VS Code for editing.

Useful Git Bash commands:

``` bash
pwd
ls -la
cd /f/project/FaceSearch
mkdir -p app/api
touch app/main.py
cat .gitignore
grep -R "TODO" app
find . -maxdepth 3 -type f
```

Avoid commands that behave differently from PowerShell unless explained.
Use `rm` carefully; it deletes files. Ask before destructive operations.

### Initialize `uv` project

Only after confirming the intended folder and inspecting it:

``` bash
cd /f/project/FaceSearch
uv init
uv python pin 3.12
uv venv --python 3.12
uv add fastapi "uvicorn[standard]" pydantic-settings
uv add --dev pytest httpx ruff
```

If `uv init` reports the project already exists, inspect
`pyproject.toml` rather than overwriting it.

Add database dependencies in Week 2:

``` bash
uv add sqlalchemy "psycopg[binary]" pgvector alembic
```

Add computer vision dependencies only after confirming compatibility and
testing installation:

``` bash
uv add insightface onnxruntime opencv-python-headless
```

If the InsightFace install fails on Windows, capture the complete error
and investigate package/Python/platform compatibility before installing
build tools or changing Python versions. Do not blindly install a large
collection of dependencies.

------------------------------------------------------------------------

## 6. Six-week plan: 42 sessions

Each session is approximately one hour. A session may take longer;
correctness takes priority over the calendar. Every session must end
with a working artifact, a written finding, or a clear blocker.

### Week 1 --- Project foundation, Git Bash, FastAPI, CI

**Goal:** a tested health endpoint in GitHub with a green CI check.

#### Day 1 --- Setup and first endpoint

1.  Confirm Git, `uv`, Python, Docker CLI, Docker Compose, and the
    Docker engine status.
2.  Confirm the project folder; inspect existing contents first.
3.  Initialize `uv` if required.
4.  Add FastAPI, Uvicorn, Pydantic Settings, Pytest, HTTPX, Ruff.
5.  Create the initial `app/main.py` health route.
6.  Create `tests/test_health.py`.
7.  Add `.gitignore` before staging files.
8.  Run tests and Ruff.
9.  Make the first Git commit.

Initial `app/main.py`:

``` python
from fastapi import FastAPI

app = FastAPI(
    title="Face Search API",
    description="Find photos containing similar faces in a permitted collection.",
    version="0.1.0",
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

Initial `tests/test_health.py`:

``` python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Run:

``` bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/api/v1/health` and
`http://127.0.0.1:8000/docs`. Stop the server with Ctrl+C.

Then run:

``` bash
uv run pytest -v
uv run ruff check .
```

Recommended initial `.gitignore`:

``` gitignore
.venv/
__pycache__/
*.py[cod]
.env
.env.*
!.env.example
photos/
uploads/
*.pkl
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.idea/
.vscode/
```

Initial Git workflow:

``` bash
git init
git branch -M main
git status
git add .
git diff --staged
git commit -m "chore: initialize Face Search API"
git log --oneline
```

Do not run `git init` again without checking whether a repository
already exists.

**Done when:** health endpoint and Swagger work, tests and Ruff pass,
and the first commit exists.

#### Day 2 --- Git Bash filesystem skills

Learn `pwd`, `ls`, `cd`, `mkdir`, `touch`, `cat`, `grep`, `find`,
relative vs absolute paths, and the Git Bash mapping of Windows drive
paths.

Practice inside a disposable `~/git-practice` folder, not inside the
real project.

**Done when:** developer can navigate and create files from Git Bash.

#### Day 3 --- Git staging and history

Practise `status`, `diff`, `add`, `diff --staged`, `commit`,
`log --oneline`, `.gitignore`, and safe use of `restore`.

**Done when:** developer can explain working tree, staging area, and
commit.

#### Day 4 --- Branches and GitHub

Create a feature branch, create/connect a GitHub repository, push the
branch, open a pull request, review it, and merge it. Protect `main`
once repository rules permit.

**Done when:** one PR has been merged successfully.

#### Day 5 --- Configuration

Create `app/core/config.py` with Pydantic Settings. Add `.env.example`
with placeholders. Keep actual `.env` untracked. Make configuration easy
to test and avoid scattered environment reads.

**Done when:** settings load from environment and missing required
settings produce clear errors.

#### Day 6 --- Continuous integration

Create `.github/workflows/ci.yml` to install the project with `uv`, run
Ruff, and run Pytest on pull requests and pushes. Pin actions to
appropriate versions and use least-privilege permissions.

**Done when:** GitHub Actions is green.

#### Day 7 --- Review and recovery

Intentionally break a test, read and fix its error, create a branch,
practise a small merge, and practise `git restore` on a disposable
change.

**Done when:** developer can explain the failure and fix without losing
unrelated work.

------------------------------------------------------------------------

### Week 2 --- Docker, PostgreSQL, pgvector, SQLAlchemy, Alembic

**Goal:** a persistent PostgreSQL database with versioned schema
migrations and database health reporting.

#### Day 8 --- Docker fundamentals

Learn image vs container, port mapping, volume vs bind mount,
environment variables, logs, and container lifecycle.

``` bash
docker info
docker ps
docker images
docker run --rm hello-world
```

If Docker cannot connect, stop here and troubleshoot Docker Desktop/WSL.
Do not reset WSL or delete volumes as a first response.

#### Day 9 --- Compose database

Create `compose.yaml` using `pgvector/pgvector:pg16`. Configure a
database, named volume, health check, and environment variables. Use a
local `.env` that is excluded from Git. Avoid publishing the database
port publicly.

**Done when:** `docker compose up -d`, `docker compose ps`, and the
database health check succeed.

#### Day 10 --- SQLAlchemy and psycopg

Install:

``` bash
uv add sqlalchemy "psycopg[binary]"
```

Create a SQLAlchemy engine, session factory, and FastAPI session
dependency. Explain connection pooling and session lifecycle. Do not
create one global session shared across requests.

**Done when:** app can open and close a database session and run a
simple query.

#### Day 11 --- pgvector and Alembic setup

Install:

``` bash
uv add pgvector alembic
```

Configure the pgvector SQLAlchemy type and Alembic to read application
configuration safely. Keep migration generation/review separate from
migration application.

**Done when:** Alembic connects to the database and detects model
metadata.

#### Day 12 --- Models

Create `Photo` and `Face` models.

`photos` fields: - `id` - `filename` - `stored_path` - unique
`content_hash` - `uploaded_at`

`faces` fields: - `id` - `photo_id` foreign key to photos with
`ON DELETE CASCADE` - `embedding vector(512)` - bounding-box fields -
`det_score`

Add suitable indexes and constraints, and use UTC-aware timestamps
consistently.

**Done when:** schema design and relationships are documented and
reviewed.

#### Day 13 --- Migrations

Create a migration that enables the vector extension:

``` sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Create tables and indexes. Test:

``` bash
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

Do not downgrade a database with valuable data without a backup and
explicit approval.

**Done when:** migration up/down/up works on disposable development
data.

#### Day 14 --- DB health and persistence

Update `/api/v1/health` to check the database and report a
degraded/unavailable state appropriately. Restart Compose and verify
data persists. Document backup/restore basics. If feasible, deploy the
health-only app to a cloud environment; select the provider and approve
cost before provisioning.

**Done when:** database health is tested and persistent data survives a
normal container restart.

------------------------------------------------------------------------

### Week 3 --- Face embeddings, upload/list/delete

**Goal:** safely process and persist images with face records.

#### Day 15 --- Embeddings and abstraction

Explain face detection vs face recognition embeddings, vector
dimensions, bounding boxes, detection confidence, and model limitations.
Define `FaceEmbedder` interface in `app/services/faces.py`.

**Done when:** model implementation can be swapped without rewriting
routes.

#### Day 16 --- Fake embedder and unit tests

Create a deterministic fake embedder. Tests must not download a model.
Test valid dimensions, empty face results, exceptions, and threshold
helpers.

**Done when:** fast tests pass without InsightFace.

#### Day 17 --- Real model experiment

Install and try InsightFace with ONNX Runtime and OpenCV. Prefer CPU
inference initially and test on a small, permitted sample set. Verify
the embedding shape is 512 if that is the selected model's output. Avoid
assuming every model has the same dimension.

**Done when:** a local script prints detected face count, embedding
shape, bounding boxes, and confidence without exposing private images in
logs.

#### Day 18 --- Validation and duplicate detection

Implement: - JPEG/PNG allowlist; - maximum upload size; - decodeability
check; - SHA-256 content hash; - duplicate upload response; - generated
server-side filename; - safe storage path.

**Done when:** invalid and oversized inputs are rejected, duplicate
uploads are recognized, and no arbitrary client path is trusted.

#### Day 19 --- `POST /api/v1/photos`

Implement route → schema/validation → service → repository/session. Save
file, run embedding, and persist photo and faces with sensible
transaction/error handling. If no face is detected, return HTTP 422 and
avoid leaving orphan files or rows.

**Done when:** valid image produces one photo row and the correct number
of face rows.

#### Day 20 --- List and delete

Implement paginated `GET /api/v1/photos`. Implement
`DELETE /api/v1/photos/{photo_id}`. Ensure face rows cascade and the
stored image is removed. Handle filesystem/database partial failures and
missing files.

**Done when:** list pagination works and deletion removes both database
and file data.

#### Day 21 --- Bulk ingestion

Write `scripts/ingest_folder.py` with clear progress/error reporting and
duplicate handling. Use only consented/permitted sample photos. Group
photos should create multiple face records.

**Done when:** target collection loads reproducibly and API tests use
fake embeddings.

------------------------------------------------------------------------

### Week 4 --- Search and ML evaluation

**Goal:** working vector search with a documented, measured decision
threshold.

#### Day 22 --- Similarity and distance

Explain cosine distance, vector normalization, nearest-neighbor
retrieval, and why distance is not automatically a probability of
identity. Confirm the metric used by the selected pgvector operator.

#### Day 23 --- Query embedding

Implement query image validation and extraction of the largest detected
face for the initial version. Return a clear error when no face is
detected.

#### Day 24 --- Vector SQL query

Use pgvector's cosine distance operator (`<=>`) or another deliberately
selected metric. Rank face rows, group by photo, and retain the best
face match per photo. Ensure query parameters are safely bound and not
interpolated into SQL strings.

#### Day 25 --- Threshold and response

Implement configurable threshold behavior and return ranked photo
results with a documented score/distance, filename, and relevant
bounding box. Make the meaning and direction of the score explicit.

#### Day 26 --- Labeled evaluation set

Create `evals/labels.csv` for a small permitted collection of 5--10
people. Avoid leakage between query and gallery data where it would make
results misleading. Record data limitations.

#### Day 27 --- Calibration script

Implement `scripts/calibrate.py`. Evaluate candidate thresholds in the
planned range 0.2--0.7 only if those values are meaningful for the
chosen metric/score. Calculate precision, recall, false matches, and
missed matches. If threshold semantics differ, adapt the range and
document why.

#### Day 28 --- Analysis and performance

Record threshold results in `docs/calibration.md`. Test sunglasses, side
angles, blur, low light, and tiny background faces. Check query plan and
indexes before adding performance complexity.

**Done when:** developer can state the measured precision and recall for
the test set and explain the selected threshold and limitations.

------------------------------------------------------------------------

### Week 5 --- Production Docker and manual cloud deployment

**Goal:** full application accessible over HTTPS with persistent storage
and tested backup/restore.

#### Day 29 --- Production Dockerfile

Create a multi-stage or otherwise appropriately minimal Dockerfile using
`uv` and the lockfile. Use `opencv-python-headless` in the server
container. Run as a non-root user where feasible. Avoid embedding
`.env`, uploads, credentials, or private data in the image.

Investigate model licensing and distribution requirements before baking
model weights into an image. Pre-download weights during image build
only if licensing, download reliability, and size make this appropriate;
otherwise document a safe model cache/mount strategy.

#### Day 30 --- Compose application stack

Add the app service to `compose.yaml`, connect it to PostgreSQL on a
private Compose network, configure named volumes for database and
uploads, and pass environment settings securely. Add health checks and
appropriate restart policies.

**Done when:** a clean local `docker compose up --build` runs the
complete stack.

#### Day 31 --- Production readiness tests

Test startup, shutdown, migration execution, environment validation,
container rebuilds, persistent data, and model loading. Ensure
application starts with a clear error if required configuration is
missing.

#### Day 32 --- Cloud provider decision

Compare suitable VPS providers and actual current prices, region, RAM,
storage, bandwidth, backups, and payment requirements before
recommending a purchase. A starting server may need 2--4 GB RAM, but
real inference measurements determine the requirement. Obtain explicit
approval before spending money.

For a VPS route, provision Ubuntu and configure SSH keys. Do not disable
the only working access method before verifying key-based login.

#### Day 33 --- Manual server deployment

Create a non-root deployment user, install Docker using official
instructions, clone the repo, create a production `.env`, and launch
services. Run Alembic migrations in a controlled step. Keep PostgreSQL
private; do not open port 5432 publicly.

#### Day 34 --- HTTPS with Caddy

Configure Caddy as reverse proxy for the app. A real domain/subdomain
pointing to the server is typically needed for automatic public HTTPS.
Expose only SSH and HTTP/HTTPS as necessary, with firewall restrictions
and SSH-key authentication.

#### Day 35 --- Backup and live test

Create a `pg_dump` backup procedure and test restoring into a separate
disposable database. Verify uploaded files are also backed up; a
database dump alone does not back up photo files. Test upload and search
on the live service.

**Done when:** live HTTPS `/docs`, upload, search, and backup restore
all work.

------------------------------------------------------------------------

### Week 6 --- CI/CD, security, documentation, release

**Goal:** a merge to protected `main` triggers verified automated
deployment.

#### Day 36 --- Broader automated tests

Test: - configuration; - image validation and size limits; - duplicate
uploads; - no-face input; - fake embedder behavior; - list pagination; -
delete cleanup; - threshold filtering; - API key authorization.

#### Day 37 --- PostgreSQL integration tests

Run migrations and vector-query tests against a disposable pgvector
PostgreSQL service in CI. Keep integration tests distinct from fast unit
tests. Ensure the fake embedder is used unless a separately configured
real-model test is intended.

#### Day 38 --- Hardening

Add API-key header protection to all appropriate endpoints except health
if intentionally public. Add request limits/timeouts, structured logging
with request IDs, safe error messages, and privacy-aware logging. Never
log secrets or raw embeddings.

#### Day 39 --- GHCR image publishing

Create GitHub Actions workflow to build and push a versioned image to
GitHub Container Registry after checks pass. Use GitHub Actions
permissions and secrets with least privilege. Pin actions to trusted
versions.

#### Day 40 --- Automated deployment

After successful CI and merge to `main`, deploy over SSH: 1.
authenticate safely; 2. pull the intended image version; 3. run database
migrations in a controlled step; 4. restart the application; 5. run a
health check; 6. report failure and retain a recovery path.

Do not delete the previous working image or database backups before the
new version is verified. Avoid running migrations concurrently from
multiple app replicas.

#### Day 41 --- Recovery and documentation

Test deployment failure/recovery, verify secrets, document rollback
limitations, and complete README sections: - purpose and architecture; -
setup with `uv`; - Docker Compose instructions; - environment variable
reference; - API examples using curl; - test commands; - threshold
evaluation results; - deployment and backup/restore; - limitations and
privacy notes.

#### Day 42 --- Release

Run full acceptance tests, verify live HTTPS behavior, create a `v1.0.0`
tag and release notes. Confirm a new developer can follow the README
without hidden manual steps.

------------------------------------------------------------------------

## 7. Testing strategy

  -----------------------------------------------------------------------
  Test type               Examples                Where
  ----------------------- ----------------------- -----------------------
  Unit                    Config, validation,     Local and CI
                          hash deduplication,     
                          fake embedder,          
                          threshold helper        

  API                     Upload, search, delete, CI with fake embedder
                          pagination, invalid     
                          files, no-face,         
                          oversized files         

  Integration             Alembic migrations,     CI with pgvector
                          PostgreSQL constraints, service
                          pgvector query and      
                          cascade delete          

  Real model              Face detection and      Local/manual or a
                          embedding on permitted  separate configured job
                          sample images           

  Deployment smoke        HTTPS health check, API After deployment
                          startup, database       
                          connection              

  Backup restore          Restore database dump   Staging/manual
                          and verify files        procedure
                          separately              
  -----------------------------------------------------------------------

Every bug should have a regression test when practical. Tests must be
deterministic, must not rely on production data, and must not require
paid external services.

------------------------------------------------------------------------

## 8. Docker and Git commands to learn

### Docker

``` bash
docker info
docker ps
docker images
docker run --rm hello-world
docker compose up -d
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
```

Warnings: - `docker compose down -v` deletes named volumes and can
destroy development data. Do not run without explicit approval and a
backup. - Never publish PostgreSQL publicly for convenience. - Container
persistence and backup are different: volumes protect against ordinary
container replacement, but not disk loss.

### Git

``` bash
git status
git diff
git add .
git diff --staged
git commit -m "feat: add photo upload"
git log --oneline --graph --decorate
git branch
git switch -c feature/example
git fetch
git pull
git push -u origin feature/example
git restore <file>
git stash
git revert <commit>
git tag v1.0.0
```

Teach commands with a safe practice repository first when they could
discard work. Explain the distinction between `restore`, `revert`,
`reset`, and `reflog`; do not use destructive recovery commands without
confirming the goal.

------------------------------------------------------------------------

## 9. Final folder structure target

``` text
FaceSearch/
├── .github/workflows/ci.yml
├── .github/workflows/deploy.yml
├── alembic/versions/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── docs/
├── evals/
├── scripts/
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

------------------------------------------------------------------------

## 10. Definition of done

The project is complete when:

-   [ ] Fresh setup is documented and uses `uv`.
-   [ ] Git history is clean and feature work uses pull requests.
-   [ ] CI runs Ruff, unit tests, and PostgreSQL integration tests.
-   [ ] Docker Compose starts the API and pgvector database.
-   [ ] Alembic migrations work and data persists across ordinary
    container restarts.
-   [ ] Upload, list, delete, and search endpoints work and have tests.
-   [ ] The real model works on permitted sample data.
-   [ ] CI uses a fake embedder and does not download the model
    unnecessarily.
-   [ ] Search thresholds are supported by documented evaluation
    results.
-   [ ] Cloud deployment uses HTTPS and keeps PostgreSQL private.
-   [ ] Database and photo-file backups have both been considered and a
    restore test succeeds.
-   [ ] Secrets and private images are excluded from Git and logs.
-   [ ] Merging a PR triggers CI/CD, and a health check verifies
    deployment.
-   [ ] README enables a fresh developer to run and understand the
    project.
-   [ ] `v1.0.0` is tagged with release notes.

------------------------------------------------------------------------

## 11. Optional stretch goals (after v1.0.0)

Choose one at a time: 1. Cluster stored faces with HDBSCAN to discover
groups without a query photo. 2. Benchmark 100,000 synthetic embeddings
and compare brute-force search with an HNSW index. 3. Evaluate model
performance across relevant groups using a permitted public test set and
careful methodology. 4. Build a Flutter upload-and-results client. 5.
Benchmark CPU inference and smaller model variants. 6. Add
authentication and user-level data isolation if the project needs
multiple users.

Do not add these before the core project is working, tested, and
deployed.

------------------------------------------------------------------------

## 12. How the AI coding agent should work with the developer

At the start of each session:

1.  Read this plan and inspect the actual repository state.
2.  Ask for the current terminal output if the environment status is
    unknown.
3.  Identify the current day/session and prerequisites.
4.  State the objective, explain the concepts in beginner-friendly
    terms, and give one small step at a time.
5.  Prefer Git Bash commands and `uv`; use PowerShell only for
    Windows-specific tasks and label it clearly.
6.  Explain the purpose of every important command and file.
7.  Never assume a command succeeded; ask for or inspect output.
8.  Before modifying existing code, inspect it and preserve working
    behavior.
9.  Run relevant tests and report exact results.
10. If blocked, diagnose the actual error before proposing alternate
    tools or broad reinstallations.
11. Do not move to the next phase until the current phase's completion
    criteria are met.
12. Keep a brief progress log in `docs/progress.md` or the conversation,
    including completed tasks, commands, tests, decisions, and blockers.
13. Do not provision paid resources, create external accounts, push
    code, publish images, or deploy changes without the user's explicit
    authorization.
14. Do not claim cloud deployment, tests, or security measures are
    complete unless verified.

### First response the agent should give

Start by acknowledging that Git, `uv`, Python 3.12, Docker CLI, and
Compose are installed, but Docker cannot reach its Linux engine. Guide
the developer to open Docker Desktop and retry `docker info` and
`docker ps`. If that fails, ask for `wsl --version`, `wsl --status`, and
`wsl --list --verbose` from PowerShell. Confirm whether `/f/Face rec` is
the intended project folder or whether `/f/project/FaceSearch` should be
used. Inspect before creating or overwriting files. Then begin Day 1.
