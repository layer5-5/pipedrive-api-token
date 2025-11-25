#!/usr/bin/env python3
"""Test script for all services with real API token."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client.pipedrive_client import PipedriveClient
from src.services.deal_service import DealService
from src.services.contact_service import ContactService
from src.services.company_service import CompanyService
from src.services.activity_service import ActivityService


async def test_all_services():
    """Test all services with comprehensive data retrieval."""

    # Use the provided API token
    # API tokens come from Layer55 backend per request - no hardcoded tokens

    print("=" * 80)
    print("Testing All Pipedrive Services with Real API Token")
    print("=" * 80)
    print()

    async with PipedriveClient(API_TOKEN) as client:
        print("✓ Client initialized successfully")
        print(f"  API Base URL: {settings.pipedrive_api_base_url}")
        print()

        # Test 1: Deal Service
        print("Test 1: Deal Service")
        print("=" * 80)
        try:
            deal_service = DealService(client)

            # Test getting deals
            result = await deal_service.get_deals(limit=5)
            print(f"✓ Successfully fetched {len(result.data)} deals")

            if result.data:
                first_deal = result.data[0]
                print(f"  First deal ID: {first_deal.get('id')}")
                print(f"  First deal title: {first_deal.get('title')}")
                print(
                    f"  First deal value: {first_deal.get('value')} {first_deal.get('currency')}"
                )
            print()
        except Exception as e:
            print(f"✗ Error fetching deals: {e}")
            print()

        # Test 2: Contact Service
        print("Test 2: Contact Service")
        print("=" * 80)
        try:
            contact_service = ContactService(client)

            # Test getting persons
            result = await contact_service.get_persons(limit=5)
            print(f"✓ Successfully fetched {len(result.data)} persons")

            if result.data:
                first_person = result.data[0]
                print(f"  First person ID: {first_person.get('id')}")
                print(f"  First person name: {first_person.get('name')}")
                print(f"  First person email: {first_person.get('email', 'N/A')}")
            print()
        except Exception as e:
            print(f"✗ Error fetching persons: {e}")
            print()

        # Test 3: Company Service
        print("Test 3: Company Service")
        print("=" * 80)
        try:
            company_service = CompanyService(client)

            # Test getting organizations
            result = await company_service.get_organizations(limit=5)
            print(f"✓ Successfully fetched {len(result.data)} organizations")

            if result.data:
                first_org = result.data[0]
                print(f"  First org ID: {first_org.get('id')}")
                print(f"  First org name: {first_org.get('name')}")
                print()
        except Exception as e:
            print(f"✗ Error fetching organizations: {e}")
            print()

        # Test 4: Activity Service
        print("Test 4: Activity Service")
        print("=" * 80)
        try:
            activity_service = ActivityService(client)

            # Test getting activities
            result = await activity_service.get_activities(limit=5)
            print(f"✓ Successfully fetched {len(result.data)} activities")

            if result.data:
                first_activity = result.data[0]
                print(f" First activity ID: {first_activity.get('id')}")
                print(f" First activity subject: {first_activity.get('subject')}")
                print(f" First activity type: {first_activity.get('type')}")
                print(f" First activity done: {first_activity.get('done')}")
                print()
        except Exception as e:
            print(f"✗ Error fetching activities: {e}")
            print()

        print("=" * 80)
        print("ALL SERVICE TESTS COMPLETED!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_all_services())
