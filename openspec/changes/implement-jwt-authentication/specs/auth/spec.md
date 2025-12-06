## ADDED Requirements
### Requirement: JWT Authentication
All MCP endpoints SHALL require valid JWT token authentication.

#### Scenario: Valid JWT token
- **WHEN** request includes valid JWT in Authorization header
- **THEN** request is processed successfully
- **AND** user_id is extracted from token subject
- **AND** user context is available to services

#### Scenario: Invalid JWT token
- **WHEN** request includes invalid JWT token
- **THEN** HTTP 401 Unauthorized response is returned
- **AND** error message does not reveal token details
- **AND** request is not processed

#### Scenario: Missing JWT token
- **WHEN** request lacks Authorization header
- **THEN** HTTP 401 Unauthorized response is returned
- **AND** error indicates authentication required

#### Scenario: Expired JWT token
- **WHEN** JWT token is expired
- **THEN** HTTP 401 Unauthorized response is returned
- **AND** error indicates token expiration

### Requirement: Multi-tenancy Support
The system SHALL provide strict data isolation between users.

#### Scenario: User data access
- **WHEN** authenticated user makes API request
- **THEN** only user's own Pipedrive data is accessed
- **AND** OAuth tokens are fetched for specific user_id
- **AND** no cross-user data leakage occurs

#### Scenario: User context propagation
- **WHEN** processing authenticated request
- **THEN** user_id is available to all service layers
- **AND** Pipedrive API calls use user-specific tokens
- **AND** logging includes user context for audit

### Requirement: Layer55 API Integration
The system SHALL integrate with Layer55 API for OAuth token management.

#### Scenario: Token retrieval
- **WHEN** user makes authenticated request
- **THEN** Pipedrive OAuth token is fetched from Layer55 API
- **AND** token is used for Pipedrive API calls
- **AND** tokens are not cached or stored

#### Scenario: API failure handling
- **WHEN** Layer55 API is unavailable
- **THEN** appropriate error response is returned
- **AND** user is notified of temporary issue
- **AND** retry logic is implemented

### Requirement: Rate Limiting
The system SHALL implement per-user rate limiting.

#### Scenario: Rate limit enforcement
- **WHEN** user exceeds rate limits
- **THEN** HTTP 429 Too Many Requests response is returned
- **AND** rate limit headers are included
- **AND** limits are per user_id

#### Scenario: Rate limit configuration
- **WHEN** configuring rate limits
- **THEN** different limits for read vs write operations
- **AND** global limits are enforced
- **AND** configuration is environment-specific