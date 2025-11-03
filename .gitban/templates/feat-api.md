
## Description

[What API feature we're building - REQUIRED]

[API endpoint or feature name - REQUIRED]

[Clear description of the API feature and its purpose]

**Value**: [Business value and API purpose - REQUIRED]

**Target Consumers**: [Who will use this API] [frontend team, external partners, mobile app, etc.]

---

## API Specification

[Endpoint, method, basic request/response - REQUIRED]

**Endpoint**: `/api/v2/[resource-name]/[action]`

**Method**: [HTTP method] [GET/POST/PUT/PATCH/DELETE]

**Content-Type**: `application/json`

**Request Schema**:
```json
{
  "field1": "string",
  "field2": 123
}
```

**Response Schema (200)**:
```json
{
  "data": {...},
  "meta": {...}
}
```

**Error Responses**: [Common error codes] (optional)
- 400: Bad Request (optional)
- 401: Unauthorized (optional)
- 404: Not Found (optional)
- 500: Internal Server Error (optional)

---

## Acceptance Criteria

[Success criteria - REQUIRED]

- [ ] Endpoint implements core functionality
- [ ] Request/response validation works
- [ ] Authentication/authorization enforced
- [ ] Error handling implemented
- [ ] API documentation created (optional)
- [ ] Rate limiting configured (optional)

---

## Implementation Plan

[How to build it - REQUIRED]

**Overview**: [High-level implementation summary]

**Implementation steps**:
1. [Implementation step 1]
2. [Implementation step 2]
3. [Implementation step 3]

**Database changes**: [if any] (optional)

**External dependencies**: [third-party APIs, services] (optional)

---

## Authentication/Authorization (optional)

[May not apply to all endpoints]

**Auth method**: [Bearer token/API key/OAuth2] (optional)

**Required scopes**: [read:resource, write:resource] (optional)

**Rate limit**: [requests/hour per user] (optional)

---

## Infrastructure as Code (optional)

[IaC details - only for backend/infra features]

**Infrastructure requirements**:
- [ ] Infrastructure defined in code (Terraform/CloudFormation/Pulumi/CDK) (optional)
- [ ] Environment configs: [dev, staging, production] (optional)
- [ ] Resource provisioning automated (optional)

**Resources needed**:
- Compute: [Lambda, ECS, EC2, Cloud Run] (optional)
- Storage: [S3, DynamoDB, RDS, CloudSQL] (optional)
- Networking: [VPC, ALB, API Gateway] (optional)

---

## API Documentation (optional)

[OpenAPI spec - nice but optional for card]

- [ ] OpenAPI/Swagger spec updated (optional)
- [ ] Postman collection created (optional)
- [ ] Client SDK updated (optional)
- [ ] Changelog entry added (optional)

**Suggested documents**:
- API documentation using `docs-api.md` template
- Architecture decision using `docs-adr.md` if making design choices

---

## Testing Strategy (optional)

**Test pyramid for APIs**:
- [ ] Unit: Business logic, validators, handlers (optional)
- [ ] Integration: Database, external services (optional)
- [ ] Contract: API spec compliance (optional)
- [ ] E2E: Full request/response flows (optional)

**TDD approach** (optional):
- [ ] OpenAPI spec written first (contract-first design) (optional)
- [ ] Integration tests written against spec (optional)
- [ ] Mock server from spec (Prism, Mockoon) (optional)

---

## Additional Notes (optional)

📝 FREEFORM SECTION - Add anything project-specific

[Any other relevant information]
