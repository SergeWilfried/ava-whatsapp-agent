#!/usr/bin/env python3
"""
Test script for conversation sync integration.

This script tests the conversation state synchronization endpoints
to ensure they're working correctly before testing with live WhatsApp messages.

Run with: python scripts/test_conversation_sync.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_companion.services.conversation_sync_helper import (
    initialize_conversation_for_user,
    add_message_to_conversation,
    sync_graph_state_to_api,
)
from ai_companion.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_conversation_sync():
    """Test conversation sync integration."""

    print_section("Conversation Sync Integration Test")

    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   ENABLE_CONVERSATION_SYNC: {settings.ENABLE_CONVERSATION_SYNC}")
    print(f"   CARTAAI_API_BASE_URL: {settings.CARTAAI_API_BASE_URL}")
    print(f"   CARTAAI_SUBDOMAIN: {settings.CARTAAI_SUBDOMAIN or '❌ NOT SET'}")
    print(f"   CARTAAI_API_KEY: {'✓ Set' if settings.CARTAAI_API_KEY else '❌ NOT SET'}")

    if not settings.ENABLE_CONVERSATION_SYNC:
        print("\n⚠️  WARNING: Conversation sync is DISABLED in settings")
        print("   Set ENABLE_CONVERSATION_SYNC=true in .env to enable")
        return

    if not settings.CARTAAI_SUBDOMAIN:
        print("\n❌ ERROR: CARTAAI_SUBDOMAIN not set in .env")
        print("   Please set CARTAAI_SUBDOMAIN=your-subdomain in .env")
        return

    # Test phone number and subdomain
    test_phone = "+51999999999"  # Test phone number
    test_subdomain = settings.CARTAAI_SUBDOMAIN

    print(f"\n🧪 Test Parameters:")
    print(f"   Phone Number: {test_phone}")
    print(f"   Subdomain: {test_subdomain}")

    # Test 1: Initialize conversation
    print_section("Test 1: Initialize Conversation")
    try:
        session_id = await initialize_conversation_for_user(
            user_phone=test_phone,
            sub_domain=test_subdomain,
            local_id=settings.CARTAAI_LOCAL_ID
        )

        if session_id:
            print(f"✅ SUCCESS: Conversation initialized")
            print(f"   Session ID: {session_id}")
        else:
            print("⚠️  WARNING: Conversation sync appears to be disabled")
            print("   This could be because:")
            print("   - ENABLE_CONVERSATION_SYNC is false")
            print("   - API server is not running")
            print("   - Network connectivity issues")
            return
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        logger.error(f"Error initializing conversation: {e}", exc_info=True)
        return

    # Test 2: Add user message
    print_section("Test 2: Add User Message")
    try:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain=test_subdomain,
            role="user",
            content="Test message from integration script"
        )
        print("✅ SUCCESS: User message tracked")
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        logger.error(f"Error tracking user message: {e}", exc_info=True)

    # Test 3: Sync state
    print_section("Test 3: Sync Graph State")
    try:
        success = await sync_graph_state_to_api(
            session_id=session_id,
            sub_domain=test_subdomain,
            graph_state={
                "current_intent": "order",
                "order_stage": "test",
                "cart": {
                    "items": [{"name": "Test Item", "quantity": 1, "price": 10.0}],
                    "total": 10.0
                },
                "user_phone": test_phone,
                "workflow": "test"
            }
        )
        if success:
            print("✅ SUCCESS: State synced successfully")
        else:
            print("⚠️  WARNING: State sync returned False")
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        logger.error(f"Error syncing state: {e}", exc_info=True)

    # Test 4: Add bot response
    print_section("Test 4: Add Bot Response")
    try:
        await add_message_to_conversation(
            session_id=session_id,
            sub_domain=test_subdomain,
            role="bot",
            content="Test response from integration script"
        )
        print("✅ SUCCESS: Bot response tracked")
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        logger.error(f"Error tracking bot response: {e}", exc_info=True)

    # Summary
    print_section("Test Summary")
    print("\n✅ All basic tests completed!")
    print("\n📝 Next Steps:")
    print("   1. Verify conversation exists in API database")
    print("   2. Check that messages are stored correctly")
    print("   3. Verify state sync is working")
    print("   4. Test with real WhatsApp message")
    print("\n💡 To test with WhatsApp:")
    print("   1. Send a message to your WhatsApp bot")
    print("   2. Check logs for: 'Conversation session initialized'")
    print("   3. Verify messages are tracked: 'Tracked bot response'")
    print("   4. Check state sync: 'Synced state for session'")
    print("\n🔍 Debug logs:")
    print(f"   grep -i 'conversation' logs/app.log | tail -20")
    print()


async def test_service_direct():
    """Test conversation state service directly."""
    from ai_companion.services.conversation_state_service import ConversationStateService

    print_section("Direct Service Test")

    if not settings.CARTAAI_SUBDOMAIN:
        print("❌ ERROR: CARTAAI_SUBDOMAIN not set")
        return

    print(f"\n📡 Testing API connection to: {settings.CARTAAI_API_BASE_URL}")

    async with ConversationStateService(
        api_base_url=settings.CARTAAI_API_BASE_URL,
        api_key=settings.CARTAAI_API_KEY,
        timeout=settings.CONVERSATION_API_TIMEOUT
    ) as service:
        test_phone = "+51999999999"

        print(f"\n1️⃣ Testing tenant lookup for: {test_phone}")
        try:
            tenant_info = await service.lookup_tenant_by_phone(test_phone)
            if tenant_info:
                print(f"✅ Tenant found:")
                print(f"   SubDomain: {tenant_info.get('subDomain')}")
                print(f"   Bot ID: {tenant_info.get('botId')}")
                print(f"   Session ID: {tenant_info.get('sessionId')}")
                print(f"   Is Active: {tenant_info.get('isActive')}")
            else:
                print(f"ℹ️  No active conversation found for {test_phone}")
                print("   This is normal if no conversation exists yet")
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            logger.error(f"Tenant lookup failed: {e}", exc_info=True)

        print(f"\n2️⃣ Testing conversation creation")
        try:
            conversation = await service.create_conversation(
                user_id=test_phone,
                sub_domain=settings.CARTAAI_SUBDOMAIN,
                local_id=settings.CARTAAI_LOCAL_ID,
                metadata={"platform": "test_script"}
            )
            print(f"✅ Conversation created:")
            print(f"   Session ID: {conversation.sessionId}")
            print(f"   User ID: {conversation.userId}")
            print(f"   Subdomain: {conversation.subDomain}")
            print(f"   Intent: {conversation.currentIntent.value}")
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            logger.error(f"Conversation creation failed: {e}", exc_info=True)


if __name__ == "__main__":
    print("\n" + "🚀 " * 25)
    print("    Conversation Sync Integration Test Suite")
    print("🚀 " * 25)

    try:
        # Run helper-based tests
        asyncio.run(test_conversation_sync())

        # Optionally run direct service tests
        print("\n\n")
        response = input("Run direct service tests? (y/N): ")
        if response.lower() == 'y':
            asyncio.run(test_service_direct())

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {type(e).__name__}: {e}")
        logger.error(f"Test suite error: {e}", exc_info=True)
        sys.exit(1)

    print("\n" + "✨ " * 25)
    print("    Test Suite Complete")
    print("✨ " * 25 + "\n")
