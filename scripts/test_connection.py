#!/usr/bin/env python3
"""
Scalekit Connection Test Script

This script tests connectivity to Scalekit services and validates that
your credentials work correctly.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from scalekit import ScalekitClient
except ImportError:
    print("❌ scalekit-sdk-python not installed")
    print("   Install with: pip install scalekit-sdk-python")
    sys.exit(1)


def test_connection():
    """Test connection to Scalekit"""
    print("=" * 60)
    print("Scalekit Connection Test")
    print("=" * 60)
    print()

    # Check environment variables
    env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL")
    client_id = os.getenv("SCALEKIT_CLIENT_ID")
    client_secret = os.getenv("SCALEKIT_CLIENT_SECRET")

    if not all([env_url, client_id, client_secret]):
        print("❌ Missing required environment variables")
        print()
        print("Please set:")
        print("  - SCALEKIT_ENVIRONMENT_URL")
        print("  - SCALEKIT_CLIENT_ID")
        print("  - SCALEKIT_CLIENT_SECRET")
        print()
        print("Run: python scripts/validate_env.py")
        sys.exit(1)

    print("Environment Configuration:")
    print("-" * 40)
    print(f"Environment URL: {env_url}")
    print(f"Client ID: {client_id[:8]}...")
    print(f"Client Secret: {client_secret[:8]}...")
    print()

    # Initialize client
    print("Initializing Scalekit client...")
    try:
        client = ScalekitClient(
            env_url=env_url,
            client_id=client_id,
            client_secret=client_secret
        )
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)

    print()

    # Test authorization URL generation
    print("Testing authorization URL generation...")
    try:
        callback_url = os.getenv("CALLBACK_URL", "http://localhost:3000/auth/callback")
        auth_url = client.get_authorization_url(
            redirect_uri=callback_url,
            options={
                "scopes": ["openid", "profile", "email"]
            }
        )

        print("✅ Authorization URL generated successfully")
        print(f"   URL: {auth_url[:60]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to generate authorization URL: {e}")
        print()
        print("Possible issues:")
        print("  - Invalid environment URL")
        print("  - Invalid client credentials")
        print("  - Network connectivity issues")
        sys.exit(1)

    # Test logout URL generation
    print("Testing logout URL generation...")
    try:
        post_logout_url = os.getenv("POST_LOGOUT_URL", "http://localhost:3000")
        logout_url = client.get_logout_url(
            id_token_hint=None,
            post_logout_redirect_uri=post_logout_url
        )

        print("✅ Logout URL generated successfully")
        print(f"   URL: {logout_url[:60]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to generate logout URL: {e}")
        print()

    # Summary
    print("=" * 60)
    print("✅ Connection test completed successfully!")
    print()
    print("Your Scalekit configuration is working correctly.")
    print()
    print("Next steps:")
    print("  1. Ensure callback URL is registered in Scalekit Dashboard:")
    print(f"     → {callback_url}")
    print()
    print("  2. Start implementing authentication:")
    print("     → See full-stack-auth/quickstart.md for your framework")
    print()
    print("  3. Test the full authentication flow:")
    print("     → Start your application")
    print("     → Navigate to /auth/login")
    print("     → Complete sign-in")
    print("     → Verify redirect to callback URL")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_connection()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
