## Why
Implement proper JWT authentication to secure MCP server endpoints and enable multi-tenancy as required for production deployment with Layer55 integration.

## What Changes
- Implement JWT validation middleware for all MCP endpoints
- Add Layer55 API client for OAuth token retrieval
- Create user context management for multi-tenancy
- Add authentication error handling
- Implement rate limiting per user
- Add API token management service

**BREAKING**: All MCP endpoints will require valid JWT tokens.

## Impact
- Affected specs: authentication, security
- Affected code: src/main.py, new auth services
- Enables secure Layer55 integration
- Provides user data isolation
- Implements production security requirements