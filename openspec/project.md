# Project Context

## Purpose
A production-ready MCP (Model Context Protocol) server for Pipedrive CRM integration with Layer55 authentication. Enables secure access to Pipedrive CRM data through the Layer55 platform with JWT-based authentication and multi-tenancy support.

## Tech Stack
- **Python 3.11+** - Primary language
- **FastAPI 0.109.0** - Web framework for REST API
- **Pydantic 2.5.3** - Data validation and settings management
- **Pipedrive SDK 0.2.0** - Official Pipedrive API client
- **python-jose[cryptography] 3.3.0** - JWT token validation
- **httpx 0.26.0** - Async HTTP client
- **Redis 5.0.1** - Caching layer (planned implementation)
- **pytest 7.4.3** - Testing framework
- **ruff 0.1.11** - Code linting and formatting
- **mypy 1.8.0** - Static type checking

## Project Conventions

### Code Style
- Follow PEP 8 Python style guidelines
- Use ruff for linting and black for formatting
- Type hints required for all functions and methods
- No silent failures (avoid bare try-except blocks)
- Comprehensive error handling with context
- Log errors without exposing sensitive tokens

### Architecture Patterns
- **Service Layer Pattern**: Business logic separated into service classes (DealService, ContactService, etc.)
- **Repository Pattern**: Data access abstracted through client classes
- **Dependency Injection**: Services initialized with required dependencies
- **Middleware Pattern**: CORS, authentication, and error handling via FastAPI middleware
- **Configuration Management**: Pydantic settings with environment variable support

### Testing Strategy
- pytest for unit and integration tests
- pytest-asyncio for async function testing
- pytest-mock for mocking external dependencies
- Test coverage with pytest-cov
- Tests organized by service layer

### Git Workflow
- Feature branches for development
- Pull requests for code review
- Conventional commit messages
- Main branch for production deployments

## Domain Context

### MCP Protocol
Implements Model Context Protocol for AI assistant integration:
- Tool discovery via `/mcp/tools/public`
- Tool execution via `/mcp/tools/call`
- JSON-RPC style request/response format

### Authentication Flow
1. Layer55 API calls MCP server with JWT token
2. MCP server validates JWT and extracts user_id
3. MCP server fetches user's Pipedrive OAuth tokens from Layer55 API
4. MCP server calls Pipedrive API with OAuth token
5. Results returned to Layer55 API

### Multi-tenancy
- Strict data isolation between users using user_id from JWT
- OAuth tokens fetched fresh per request (no caching)
- User-specific API rate limiting

## Important Constraints

### Security
- JWT secret key must be shared with Layer55 API
- OAuth tokens never cached or logged
- All MCP endpoints require valid JWT authentication
- HTTPS recommended for production deployment

### Performance
- Rate limiting: 100 requests/minute global, 20 write operations/minute
- Connection pooling with 10 concurrent connections
- 30-second request timeout
- Redis caching planned for metadata (24h TTL) and deals (5min TTL)

### Compliance
- Proprietary Layer55 software
- GDPR considerations for personal data handling
- No token logging or exposure in error messages

## External Dependencies

### Required Services
- **Layer55 API** (https://api.layer55.eu) - JWT validation and OAuth token retrieval
- **Pipedrive API** (https://api.pipedrive.com) - CRM data operations
- **Redis** (localhost:6379) - Caching layer (optional but recommended)

### Environment Variables
- `LAYER55_API_URL` - Layer55 API endpoint
- `JWT_SECRET_KEY` - Shared secret for JWT validation
- `MCP_SERVER_PORT` - Server port (default: 8002)
- `ENVIRONMENT` - development/production mode
- `ENABLE_DATA_RETRIEVAL_LOGGING` - Toggle for request/response logging
