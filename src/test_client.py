"""Test script for Pipedrive client with real API token."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src_v2.client.pipedrive_client import PipedriveClient
from src_v2.config import settings


async def test_client():
    """Test Pipedrive client with real API token."""

    # Use the provided API token
    API_TOKEN = "3ce8d4075347977130d420196f9f42520d813469"

    print("=" * 80)
    print("Testing Pipedrive Client with Real API Token")
    print("=" * 80)
    print()

    async with PipedriveClient(API_TOKEN) as client:
        print("✓ Client initialized successfully")
        print(f"  API Base URL: {settings.pipedrive_api_base_url}")
        print()

        # Test 1: Get deals
        print("Test 1: Getting deals...")
        try:
            response = await client.get("/v1/deals", params={"limit": 5})
            deals = response.get("data", [])
            print(f"✓ Successfully fetched {len(deals)} deals")

            if deals:
                first_deal = deals[0]
                print(f"  First deal ID: {first_deal.get('id')}")
                print(f"  First deal title: {first_deal.get('title')}")
                print(
                    f"  First deal value: {first_deal.get('value')} {first_deal.get('currency')}"
                )
            print()
        except Exception as e:
            print(f"✗ Error fetching deals: {e}")
            print()

        # Test 2: Get a specific deal (if we have one)
        if deals:
            deal_id = deals[0].get("id")
            print(f"Test 2: Getting deal {deal_id}...")
            try:
                response = await client.get(f"/v1/deals/{deal_id}")
                deal = response.get("data", {})
                print(f"✓ Successfully fetched deal {deal_id}")
                print(f"  Title: {deal.get('title')}")
                print(f"  Status: {deal.get('status')}")
                print(f"  Stage ID: {deal.get('stage_id')}")
                print(f"  Owner ID: {deal.get('owner_id')}")
                print()
            except Exception as e:
                print(f"✗ Error fetching deal: {e}")
                print()

        # Test 3: Get pipelines
        print("Test 3: Getting pipelines...")
        try:
            response = await client.get("/v1/pipelines")
            pipelines = response.get("data", [])
            print(f"✓ Successfully fetched {len(pipelines)} pipelines")

            if pipelines:
                for pipeline in pipelines:
                    print(f"  - {pipeline.get('name')} (ID: {pipeline.get('id')})")
            print()
        except Exception as e:
            print(f"✗ Error fetching pipelines: {e}")
            print()

        # Test 4: Get users
        print("Test 4: Getting users...")
        try:
            response = await client.get("/v1/users")
            users = response.get("data", [])
            print(f"✓ Successfully fetched {len(users)} users")

            if users:
                for user in users[:3]:  # Show first 3
                    print(f"  - {user.get('name')} ({user.get('email')})")
            print()
        except Exception as e:
            print(f"✗ Error fetching users: {e}")
            print()

        # Test 5: Get persons/contacts
        print("Test 5: Getting persons...")
        try:
            response = await client.get("/v1/persons", params={"limit": 5})
            persons = response.get("data", [])
            print(f"✓ Successfully fetched {len(persons)} persons")

            if persons:
                first_person = persons[0]
                print(f"  First person ID: {first_person.get('id')}")
                print(f"  First person name: {first_person.get('name')}")
                print(f"  First person email: {first_person.get('email', 'N/A')}")
            print()
        except Exception as e:
            print(f"✗ Error fetching persons: {e}")
            print()

        # Test 6: Get organizations/companies
        print("Test 6: Getting organizations...")
        try:
            response = await client.get("/v1/organizations", params={"limit": 5})
            orgs = response.get("data", [])
            print(f"✓ Successfully fetched {len(orgs)} organizations")

            if orgs:
                first_org = orgs[0]
                print(f"  First org ID: {first_org.get('id')}")
                print(f"  First org name: {first_org.get('name')}")
            print()
        except Exception as e:
            print(f"✗ Error fetching organizations: {e}")
            print()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_client())
