"""
Fixed Pipedrive client that works around the broken python-pipedrive package.
The original package has a hardcoded bug using 'app.pipedrive.com' instead of 'api.pipedrive.com'
"""

import logging
import json
from urllib.parse import urlencode
import requests

logger = logging.getLogger(__name__)

# HTTP method constants
GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"


class PipedriveFixed:
    """Fixed Pipedrive client that properly uses api.pipedrive.com"""

    GET = GET
    POST = POST
    PUT = PUT
    DELETE = DELETE

    def __init__(self, token):
        self._token = token
        # Fixed: Use the correct API base URL instead of the broken 'app.pipedrive.com'
        self._origin = "https://api.pipedrive.com"
        logger.info(
            "Pipedrive client initialized with correct base URL: " + self._origin
        )

    def request(self, method, path, data=None):
        """
        Make HTTP request to Pipedrive API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., '/v1/users')
            data: Request data dictionary

        Returns:
            Response JSON dict
        """
        if data is None:
            data = {}

        # Ensure path starts with /v1
        if not path.startswith("/v1"):
            path = "/v1" + path

        url = self._origin + path + "?api_token=%s" % self._token

        if method == GET and data:
            url += "&" + urlencode(data)

        logger.debug(f"Making request: {method} {url}")

        r = requests.request(
            method,
            url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        response = r.json()

        if not response.get("success", True) and "error" in response:
            logger.error(f"Pipedrive API error: {response.get('error')}")

        return response

    def __getattr__(self, name):
        """
        Handle dynamic method calls like get_users(), create_deals(), etc.

        Examples:
            pipedrive.get_users() -> GET /v1/users
            pipedrive.create_deals({'title': '...'}) -> POST /v1/deals
            pipedrive.update_deals({'id': 1, 'title': '...'}) -> PUT /v1/deals/1
        """

        def wrapper(data=None):
            if data is None:
                data = {}

            try:
                action, raw_path = name.split("_", 1)
            except ValueError:
                raise AttributeError(f"Invalid method name: {name}")

            # Map action to HTTP method
            method_map = {
                "get": GET,
                "create": POST,
                "update": PUT,
                "delete": DELETE,
            }

            if action not in method_map:
                raise AttributeError(f"Invalid action: {action}")

            method = method_map[action]
            path = raw_path.replace("_", "/")

            # Handle PUT requests with ID
            if method == PUT:
                if "id" not in data:
                    raise ValueError("PUT requests require an 'id' field in data")
                id_val = data.pop("id")
                path = "%s/%d" % (path, id_val)

            # Make the request with /v1 prefix
            r_data = self.request(method, "/v1/" + path, data)

            if "error" in r_data:
                error_msg = r_data.get("error", "Unknown error")
                raise Exception(f"Pipedrive API Error: {error_msg}")

            return r_data

        return wrapper

    class Error(Exception):
        """Pipedrive error"""

        def __init__(self, response):
            self.response = response

        def __str__(self):
            return self.response.get("error", "No error provided")
