# 16 — Security & Permissions

## Token Handling

### Personal Access Token (PAT)

| Property | Detail |
|---|---|
| **Stored in** | `.env` file (MVP) / OS keyring (future) |
| **Git-ignored** | `.env` must be in `.gitignore` |
| **Required scopes** | `api`, `write_repository` |
| **Expiry** | Recommend 90-day rotation |

### `.env` Security

- File permissions should be user-read-only (`chmod 600 .env` on *nix; NTFS ACL on Windows).
- Never commit `.env` to source control.
- The app checks on startup that `.env` is not tracked by Git and warns if it is.

### Future: OS Keyring

```python
import keyring

def store_pat(token: str):
    keyring.set_password("mechalaunchpad", "gitlab_pat", token)

def get_pat() -> str:
    return keyring.get_password("mechalaunchpad", "gitlab_pat")
```

---

## Repository Permissions

| Role | Repo | Access Level | Purpose |
|---|---|---|---|
| **Artist** | `mech-assets` | Developer (push to `submit/*` branches) | Publish assets |
| **Artist** | `mechalaunchpad-tool` | Reporter (read only) | Download tool |
| **Artist** | `mech-unity` | None | No direct access needed |
| **CI Bot** | `mech-assets` | Reporter | Read assets for validation |
| **CI Bot** | `mech-unity` | Developer | Push prefabs (future) |
| **Admin/Dev** | All repos | Maintainer | Merge to `main`, manage CI |

### Protected Branches

| Repo | Branch | Protection |
|---|---|---|
| `mech-assets` | `main` | No direct push; merge only via CI-passing MR |
| `mech-assets` | `submit/*` | Push allowed for Developer role |
| `mech-unity` | `main` | Push allowed for CI Bot only |

---

## CI Bot User

A dedicated GitLab bot account (`mech-ci-bot`) runs CI jobs that need write access.

| Property | Value |
|---|---|
| Username | `mech-ci-bot` |
| Email | `mech-ci-bot@noreply.local` |
| PAT scope | `api`, `write_repository` |
| Group membership | Developer on `mech-unity` |

The bot's PAT is stored as a **CI/CD variable** (`CI_BOT_PAT`) in GitLab project settings, masked and protected.

---

## Data in Transit

| Connection | Protocol | Notes |
|---|---|---|
| App → GitLab API | HTTPS | TLS 1.2+ |
| App → Git remote | SSH or HTTPS | SSH key or PAT |
| CI → Unity runner | Local | Runs on same machine |

---

## Local Data

| Data | Location | Sensitivity |
|---|---|---|
| `.env` (PAT) | Tool directory | **High** — treat as credential |
| Local repo clone | `~/.mechalaunchpad/mech-assets/` | Medium — contains asset FBX files |
| Log file | `~/.mechalaunchpad/logs/` | Low — no secrets logged |
| Preview renders | Temp directory | Low — transient |

### No Secrets in Logs

The logging module must never log:
- PAT values
- Full API URLs with tokens in query strings
- Git remote URLs with embedded credentials
