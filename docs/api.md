# BrandSentinel REST API Reference

The BrandSentinel backend provides a RESTful API compliant with OpenAPI 3.1. Interactive Swagger documentation is accessible at `http://localhost:8000/docs` when the server is running.

---

## 1. Authentication Endpoints

### `POST /auth/login`
Authenticates a user and issues a signed JWT access token.

- **Request Body:**
  ```json
  {
    "email": "creator1@novafit.local",
    "password": "Demo@12345"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1...",
    "token_type": "bearer",
    "user": {
      "id": 4,
      "email": "creator1@novafit.local",
      "name": "NovaFit Creator1",
      "role": "creator",
      "workspace_id": 1
    }
  }
  ```

### `GET /auth/me`
Returns the active session's user profile and permissions.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** `UserResponse`

---

## 2. Knowledge Base Endpoints

### `GET /kb/rules`
Lists approved brand guidelines for the active workspace.
- **Query Params:** `category` (optional), `kb_version_id` (optional)
- **Response (200 OK):** Array of `Rule` objects.

### `POST /kb/rules`
Creates a new brand guideline (Admin only).
- **Request Body:**
  ```json
  {
    "code": "NF-TONE-02",
    "category": "tone",
    "text": "Speak directly to customer achievements.",
    "severity_default": "medium",
    "examples_good": ["You crushed your session!"],
    "examples_bad": ["You survived."]
  }
  ```

### `POST /kb/import`
Atomises unstructured brand policy text into discrete candidate rules (Admin only).
- **Request Body:** `{"raw_text": "All marketing graphics must adhere to WCAG AA..."}`
- **Response (200 OK):** `{"candidate_rules": [...]}`

### `POST /kb/versions`
Snapshots the active knowledge base into an immutable version.
- **Request Body:** `{"label": "Q3 2026 Brand Standards"}`
- **Response (201 Created):** `{"id": 2, "label": "Q3 2026 Brand Standards", "is_active": true}`

---

## 3. Content Governance & Workflow Endpoints

### `POST /content/`
Drafts new brand content.
- **Request Body:**
  ```json
  {
    "title": "Summer Campaign Email",
    "type": "text",
    "body": "Push until you collapse! Get your Nova Watch for 20 bucks."
  }
  ```
- **Response (201 Created):** `{"content_id": 1, "version_id": 1, "status": "draft"}`

### `POST /content/upload`
Uploads and parses a DOCX or plain text document.
- **Multipart Form:** `file: UploadFile`, `title: string`

### `POST /content/{id}/review`
Executes pre-publication verification review across the active knowledge base.
- **Response (202 Accepted):**
  ```json
  {
    "review_run_id": 12,
    "status": "completed",
    "risk_level": "high",
    "escalate_to": "reviewer",
    "findings": [
      {
        "id": 101,
        "category": "terminology",
        "severity": "major",
        "span": {"start": 32, "end": 42, "text": "Nova Watch"},
        "reason": "Banned terminology 'Nova Watch' used.",
        "suggestion": "Replace with approved term 'NovaBand Pro'."
      }
    ]
  }
  ```

### `POST /content/{id}/submit`
Submits content for governance review.
- **Response (200 OK):** `{"status": "submitted"}`

### `POST /content/{id}/approve`
Signs and approves content (Manager or Authorised Reviewer).
- **Enforcement:** Enforces no-self-approval rule and role permissions.
- **Request Body:** `{"comment": "Verified against Q3 compliance schedule."}`
- **Response (200 OK):**
  ```json
  {
    "status": "approved",
    "approval_id": 3,
    "signature_hash": "a8fbc39..."
  }
  ```

### `POST /content/{id}/accept`
Accepts an AI suggestion, splicing the fix into the content body and creating a new content version.
- **Request Body:** `{"finding_id": 101}`

### `POST /content/{id}/dismiss`
Dismisses a finding with a required human rationale.
- **Request Body:** `{"finding_id": 101, "reason": "Authorized exception for historical campaign quote."}`

---

## 4. Vision & Contrast Endpoints (Improvement I-2)

### `POST /vision/analyze`
Inspects brand imagery for palette compliance and WCAG contrast.
- **Multipart Form:** `image: UploadFile`
- **Response (200 OK):**
  ```json
  {
    "dominant_colors": ["#FF5722", "#212121", "#FFFFFF"],
    "closest_palette_matches": [
      {"extracted": "#FF5722", "brand": "#FF5722", "delta_e": 0.0, "match": true}
    ],
    "contrast_evaluation": {
      "contrast_ratio": 5.4,
      "wcag_aa_compliant": true,
      "wcag_aaa_compliant": false
    }
  }
  ```

---

## 5. Audit & Compliance Endpoints

### `GET /audit/trail`
Retrieves chronological audit events for the active workspace.
- **Response (200 OK):** Array of `AuditEvent` records.

### `GET /audit/verify`
Performs end-to-end cryptographic verification of the SHA-256 hash chain.
- **Response (200 OK):**
  ```json
  {
    "verified": true,
    "chain_length": 48,
    "latest_hash": "5d9c12...",
    "corrupted_event_id": null
  }
  ```

---

## 6. Insights & Analytics Endpoints (Improvement I-3)

### `GET /insights/summary`
Returns aggregate workspace governance metrics.
- **Response (200 OK):**
  ```json
  {
    "total_contents": 42,
    "total_reviews": 89,
    "clean_pass_rate": 78.4,
    "average_latency_ms": 1.2
  }
  ```

### `GET /insights/ambiguity`
Returns rules identified as ambiguous due to excessive creator dismissals (> 40%).
- **Response (200 OK):**
  ```json
  {
    "flagged_rules": [
      {
        "rule_code": "AU-TONE-01",
        "dismissal_rate": 0.52,
        "total_findings": 25,
        "dismissals": 13,
        "recommendation": "Review tone guidance wording to clarify acceptable academic colloquialisms."
      }
    ]
  }
  ```
