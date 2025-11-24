# Data Retrieval Logging

This MCP server includes comprehensive data retrieval logging to help with debugging and monitoring. The logging captures:

## What Gets Logged

### API Request Logging
- HTTP method and endpoint
- Full URL (with API token masked)
- Request parameters and data
- Response status code
- Success/failure status
- Number of items returned

### Tool Execution Logging
- Tool name and arguments
- Number of records retrieved
- Sample record data (first record)
- Key fields for common data types:
  - **Deals**: ID, title, value
  - **Persons**: ID, name, email
  - **Organizations**: ID, name
  - **Activities**: ID, type, subject
- Total deal value (for deal queries)
- Pagination information
- API errors

## How to Disable Logging

### Method 1: Environment Variable (Recommended)
Set the environment variable to disable logging:

```bash
export ENABLE_DATA_RETRIEVAL_LOGGING=false
```

### Method 2: Code Comment Out
Comment out the logging call in `src/main.py`:

```python
# In execute_tool function, comment out this line:
# _log_data_retrieval(tool_name, args, result)
```

### Method 3: Configuration Flag
Change the flag at the top of `src/main.py`:

```python
ENABLE_DATA_RETRIEVAL_LOGGING = False
```

## Log Format

All logging entries are clearly marked with:
- `=== DATA RETRIEVAL LOG ===` for tool execution
- `=== API REQUEST LOG ===` for API requests  
- `=== API RESPONSE LOG ===` for API responses

This makes it easy to filter or search for these entries in log files.

## Security Note

- API tokens are partially masked in logs
- Only sample data (first record) is logged in detail
- Sensitive fields are not explicitly logged
- Logging can be completely disabled for production environments

## Performance Impact

The logging has minimal performance impact:
- Only processes results after successful API calls
- Uses efficient string operations
- Can be completely disabled if needed
- Errors in logging won't affect main functionality