#!/usr/bin/env python3
"""Startup test to verify tool handlers are working."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests


async def test_tool_handlers():
    """Test that tool handlers are actually registered and callable."""

    print("Testing tool handlers...")

    # Test 1: Check if server is running
    try:
        response = requests.get("http://localhost:8004/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
        print("✅ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

    # Test 2: Check public tools endpoint
    try:
        response = requests.get("http://localhost:8004/mcp/tools/public", timeout=5)
        if response.status_code != 200:
            print(f"❌ Tools endpoint failed: {response.status_code}")
            return False

        tools_data = response.json()
        tools = [t["name"] for t in tools_data.get("tools", [])]
        print(f"✅ Found {len(tools)} tools: {tools}")

        # Test 3: Try to call get_pipeline_stages
        if "get_pipeline_stages" not in tools:
            print("❌ get_pipeline_stages not found in tools list")
            return False

        print("✅ get_pipeline_stages is available, testing actual call...")

        # Test 4: Make actual tool call
        tool_response = requests.post(
            "http://localhost:8004/mcp/tools/call",
            json={"name": "get_pipeline_stages", "arguments": {}},
            headers={"Content-Type": "application/json", "X-API-Token": "test-token"},
            timeout=10,
        )

        if tool_response.status_code == 200:
            result = tool_response.json()
            if "error" in result:
                print(f"❌ Tool call returned error: {result['error']}")
                return False
            else:
                print("✅ Tool call succeeded")
                return True
        else:
            print(f"❌ Tool call failed with status: {tool_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tool_handlers())
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Tests failed!")
        sys.exit(1)
