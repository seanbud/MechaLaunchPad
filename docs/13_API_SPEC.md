# 13 — API Spec

All API interactions use the **GitLab REST API v4**. MechaLaunchPad does not expose its own API — it is a client.

---

## Base URL

```
{GITLAB_URL}/api/v4/projects/{PROJECT_ID}
```

All requests include the header:
```
PRIVATE-TOKEN: {GITLAB_PAT}
```

---

## Endpoints Used

### 1. List Pipelines

**Purpose**: Populate the CI Status tab.

```
GET /pipelines?ref={branch}&per_page=20&order_by=updated_at&sort=desc
```

**Response** (array):
```json
[
  {
    "id": 42,
    "iid": 42,
    "status": "success",
    "ref": "submit/LeftArm/v001",
    "sha": "abc123",
    "created_at": "2025-03-15T10:30:00Z",
    "updated_at": "2025-03-15T10:32:45Z",
    "web_url": "https://gitlab.example.com/project/-/pipelines/42"
  }
]
```

---

### 2. Get Pipeline Details

**Purpose**: Show per-stage results when a pipeline is selected.

```
GET /pipelines/{pipeline_id}
```

**Response**:
```json
{
  "id": 42,
  "status": "failed",
  "detailed_status": {
    "text": "failed",
    "label": "failed",
    "icon": "status_failed"
  },
  "stages": ["validate", "unity_ingest", "report"]
}
```

---

### 3. List Pipeline Jobs

**Purpose**: Show status per stage.

```
GET /pipelines/{pipeline_id}/jobs
```

**Response** (array):
```json
[
  {
    "id": 101,
    "name": "validate",
    "stage": "validate",
    "status": "failed",
    "started_at": "2025-03-15T10:30:10Z",
    "finished_at": "2025-03-15T10:30:45Z",
    "duration": 35.2,
    "web_url": "https://gitlab.example.com/project/-/jobs/101"
  },
  {
    "id": 102,
    "name": "unity_ingest",
    "stage": "unity_ingest",
    "status": "skipped"
  }
]
```

---

### 4. Get Job Log (Trace)

**Purpose**: Display failure details when an artist clicks "View Full Log".

```
GET /jobs/{job_id}/trace
```

**Response**: Plain text (raw job log output).

Parse for lines matching the validation error format:
```
RULE_ID: message
```

---

### 5. Download Job Artifacts

**Purpose**: Retrieve `validation_report.json`, thumbnails, and prefabs.

```
GET /jobs/{job_id}/artifacts
```

**Response**: ZIP archive containing all artifacts from that job.

To download a specific file:
```
GET /jobs/{job_id}/artifacts/{artifact_path}
```

**Example**:
```
GET /jobs/101/artifacts/validation_report.json
```

**Response**: Raw JSON file content.

---

### 6. Get Latest Artifact by Branch (convenience)

```
GET /jobs/artifacts/{branch_ref}/raw/{artifact_path}?job=validate
```

**Example**:
```
GET /jobs/artifacts/submit%2FLeftArm%2Fv001/raw/validation_report.json?job=validate
```

---

## Error Handling

| HTTP Status | Meaning | Tool Action |
|---|---|---|
| `200` | Success | Process response |
| `401` | Invalid/expired token | Show "Authentication failed — check PAT" |
| `404` | Pipeline/job not found | Show "No pipeline found for this branch" |
| `429` | Rate limited | Back off, retry after `Retry-After` header |
| `500+` | Server error | Show "GitLab server error — try again" |

---

## Rate Limiting

GitLab allows ~2000 requests/hour for PAT-authenticated users. The tool polls at most every 5 seconds during active monitoring, which stays well within limits.

---

## Client Wrapper Summary

```python
class GitLabClient:
    def list_pipelines(self, ref: str, per_page: int = 20) -> list[dict]
    def get_pipeline(self, pipeline_id: int) -> dict
    def list_jobs(self, pipeline_id: int) -> list[dict]
    def get_job_trace(self, job_id: int) -> str
    def download_artifact(self, job_id: int, path: str) -> bytes
    def get_latest_artifact(self, ref: str, job: str, path: str) -> bytes
```
