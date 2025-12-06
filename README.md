# Pipedrive MCP Server

A production-ready MCP (Model Context Protocol) server for Pipedrive CRM integration with Layer55 authentication.

## Overview

This MCP server enables secure access to Pipedrive CRM data through the Layer55 platform. It implements:

- **JWT Authentication**: Validates requests from Layer55 API using JWT tokens
- **Multi-tenancy**: Strict data isolation between users
- **OAuth Token Management**: Retrieves user-specific Pipedrive OAuth tokens from Layer55 API
- **Comprehensive Tools**: 15+ tools for deals, contacts, companies, activities, and users

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Layer55 API   │◄────────┤  Pipedrive MCP   │◄────────┤  Pipedrive API  │
│ (api.layer55.eu)│  JWT +  │     Server       │  OAuth  │                 │
│                 │  user_id│  (port 8002)     │  Token  │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Authentication Flow

1. Layer55 API calls MCP server with JWT token
2. MCP server validates JWT and extracts user_id
3. MCP server fetches user's Pipedrive OAuth tokens from Layer55 API
4. MCP server calls Pipedrive API with OAuth token
5. Results returned to Layer55 API

## Data Retrieval Logging

This server includes comprehensive data retrieval logging for debugging and monitoring. See [DATA_LOGGING.md](DATA_LOGGING.md) for details on:

- What gets logged (API requests, responses, tool execution)
- How to disable logging (environment variable or code changes)
- Log format and security considerations
- Performance impact

## Available Tools

### Deal Management
- `get_deals` - List deals with filters (status, stage, pipeline)
- `get_deal` - Get single deal details
- `create_deal` - Create new deal
- `update_deal` - Update deal fields
- `get_deal_activities` - Get deal activities
- `get_deal_notes` - Get deal notes

### Contact Management
- `get_persons` - List contacts
- `get_person` - Get contact details
- `create_person` - Create new contact
- `update_person` - Update contact

### Company Management
- `get_organizations` - List companies
- `get_organization` - Get company details
- `create_organization` - Create new company

### Activity Management
- `get_activities` - List activities
- `create_activity` - Create new activity

### User Management
- `get_users` - List team members
- `get_user` - Get user details

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for deployment)
- Access to Layer55 API
- JWT secret key (shared with Layer55 API)

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the server**:
```bash
cd src
python main.py
```

The server will start on `http://localhost:8002`

### Docker Deployment

The server is designed to run as a Docker container alongside Layer55 services.

1. **Build image**:
```bash
docker build -t pipedrive-mcp:latest .
```

2. **Run container**:
```bash
docker run -p 8002:8002 \
  -e LAYER55_API_URL=http://api:8066 \
  -e JWT_SECRET_KEY=your-secret \
  pipedrive-mcp:latest
```

### Integration with Layer55

Add to your `docker-compose.yml`:

```yaml
pipedrive-mcp:
  build:
    context: ./mcp/pipedrive
    dockerfile: Dockerfile
  container_name: pipedrive-mcp
  ports:
    - "8002:8002"
  environment:
    - LAYER55_API_URL=http://api:8066
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  networks:
    - default
  restart: unless-stopped
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LAYER55_API_URL` | URL of Layer55 API | Yes | - |
| `JWT_SECRET_KEY` | Shared secret for JWT validation | Yes | - |
| `MCP_SERVER_PORT` | Port to run server on | No | 8002 |
| `LOG_LEVEL` | Logging level | No | INFO |
| `ENVIRONMENT` | Environment (development/production) | No | development |

## API Endpoints

### Health Check
```
GET /health
```
Returns server health status (no authentication required).

### Server Info
```
GET /
```
Returns server information (no authentication required).

### MCP Initialize
```
POST /mcp/initialize
Authorization: Bearer <jwt_token>
```
Initialize MCP session.

### List Tools
```
GET /mcp/tools
Authorization: Bearer <jwt_token>
```
List all available Pipedrive tools.

### Call Tool
```
POST /mcp/tools/call
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "get_deals",
  "arguments": {
    "status": "open",
    "limit": 50
  }
}
```
Execute a specific tool.

## Security

- **JWT Validation**: All MCP endpoints require valid JWT tokens
- **Multi-tenancy**: User data strictly isolated using user_id from JWT
- **Token Security**: OAuth tokens never cached, fetched fresh per request
- **No Token Logging**: Sensitive tokens never appear in logs
- **HTTPS**: Recommended for production deployment

## Development

### Project Structure

```
mcp/pipedrive/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── auth/
│   │   ├── jwt_validator.py # JWT validation
│   │   └── layer55_client.py # Token retrieval
│   ├── pipedrive/
│   │   ├── client.py        # Pipedrive API client
│   │   └── tools.py         # MCP tool implementations
│   └── mcp/
│       └── protocol.py      # MCP protocol handlers
├── tests/
├── requirements.txt
├── Dockerfile
└── README.md
```

### Running Tests

```bash
pytest tests/
```

### Code Style

- Follow PEP 8
- No silent failures (avoid bare try-except)
- Comprehensive error handling
- Log errors with context (without exposing tokens)

## Troubleshooting

### JWT Validation Fails
- Verify `JWT_SECRET_KEY` matches Layer55 API configuration
- Check token expiration time
- Ensure `sub` claim contains valid user_id

### Token Retrieval Fails
- Verify `LAYER55_API_URL` is correct
- Check network connectivity between services
- Ensure user has OAuth tokens configured for Pipedrive

### Pipedrive API Errors
- Check OAuth token validity
- Verify Pipedrive API rate limits
- Review Pipedrive API status

## License

Proprietary - Layer55

## Support

For issues or questions, contact the Layer55 team.
