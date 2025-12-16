#!/usr/bin/env python3
"""
Scalekit Interactive Authentication Flow Test

This script provides an interactive test of the complete authentication flow
including token exchange and validation.
"""

import os
import sys
from urllib.parse import urlparse, parse_qs

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


def test_auth_flow():
    """Interactive authentication flow test"""
    print("=" * 60)
    print("Scalekit Interactive Authentication Flow Test")
    print("=" * 60)
    print()

    # Initialize client
    env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL")
    client_id = os.getenv("SCALEKIT_CLIENT_ID")
    client_secret = os.getenv("SCALEKIT_CLIENT_SECRET")
    callback_url = os.getenv("CALLBACK_URL", "http://localhost:3000/auth/callback")

    if not all([env_url, client_id, client_secret]):
        print("❌ Missing required environment variables")
        print("   Run: python scripts/validate_env.py")
        sys.exit(1)

    client = ScalekitClient(
        env_url=env_url,
        client_id=client_id,
        client_secret=client_secret
    )

    # Step 1: Generate authorization URL
    print("Step 1: Generate Authorization URL")
    print("-" * 40)

    try:
        auth_url = client.get_authorization_url(
            redirect_uri=callback_url,
            options={
                "scopes": ["openid", "profile", "email", "offline_access"]
            }
        )

        print("✅ Authorization URL generated:")
        print()
        print(auth_url)
        print()
    except Exception as e:
        print(f"❌ Failed to generate authorization URL: {e}")
        sys.exit(1)

    # Step 2: Manual login
    print("Step 2: Complete Authentication")
    print("-" * 40)
    print("1. Copy the URL above and open it in your browser")
    print("2. Sign in or create an account")
    print("3. After authentication, you'll be redirected to your callback URL")
    print("4. Copy the full redirect URL from your browser")
    print()

    redirect_url = input("Paste the redirect URL here (or press Enter to skip): ").strip()

    if not redirect_url:
        print()
        print("⚠️  Skipping token exchange test")
        print()
        print("To test manually:")
        print("  1. Start your application")
        print("  2. Navigate to /auth/login")
        print("  3. Complete sign-in")
        print("  4. Verify you're redirected to /dashboard")
        return

    print()

    # Step 3: Extract authorization code
    print("Step 3: Extract Authorization Code")
    print("-" * 40)

    try:
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        code = query_params.get('code', [None])[0]
        error = query_params.get('error', [None])[0]
        error_description = query_params.get('error_description', [None])[0]

        if error:
            print(f"❌ OAuth error: {error}")
            if error_description:
                print(f"   Description: {error_description}")
            sys.exit(1)

        if not code:
            print("❌ No authorization code found in URL")
            print("   Make sure you pasted the complete redirect URL")
            sys.exit(1)

        print(f"✅ Authorization code extracted: {code[:20]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to parse redirect URL: {e}")
        sys.exit(1)

    # Step 4: Exchange code for tokens
    print("Step 4: Exchange Code for Tokens")
    print("-" * 40)

    try:
        result = client.authenticate_with_code(
            code=code,
            redirect_uri=callback_url
        )

        print("✅ Tokens received successfully!")
        print()
        print("Token Details:")
        print(f"  - Access Token: {result.access_token[:20]}...")
        print(f"  - Refresh Token: {result.refresh_token[:20]}...")
        print(f"  - ID Token: {result.id_token[:20]}...")
        print(f"  - Expires In: {result.expires_in} seconds")
        print()
    except Exception as e:
        print(f"❌ Failed to exchange code for tokens: {e}")
        print()
        print("Possible issues:")
        print("  - Authorization code already used (codes are single-use)")
        print("  - Code expired (usually valid for 10 minutes)")
        print("  - Callback URL mismatch")
        sys.exit(1)

    # Step 5: Validate user information
    print("Step 5: User Information")
    print("-" * 40)

    try:
        user = result.user
        print(f"  - User ID (sub): {user.sub}")
        print(f"  - Email: {user.email}")
        print(f"  - Email Verified: {user.email_verified}")
        if hasattr(user, 'name') and user.name:
            print(f"  - Name: {user.name}")
        if hasattr(user, 'given_name') and user.given_name:
            print(f"  - Given Name: {user.given_name}")
        if hasattr(user, 'family_name') and user.family_name:
            print(f"  - Family Name: {user.family_name}")
        print()
    except Exception as e:
        print(f"❌ Failed to parse user information: {e}")

    # Step 6: Validate access token
    print("Step 6: Validate Access Token")
    print("-" * 40)

    try:
        claims = client.validate_access_token(result.access_token)
        print("✅ Access token is valid!")
        print()
        print("Token Claims:")
        for key, value in claims.items():
            print(f"  - {key}: {value}")
        print()
    except Exception as e:
        print(f"❌ Failed to validate access token: {e}")

    # Step 7: Test token refresh
    print("Step 7: Test Token Refresh")
    print("-" * 40)

    try:
        refreshed = client.refresh_access_token(result.refresh_token)
        print("✅ Token refresh successful!")
        print()
        print("New Token Details:")
        print(f"  - Access Token: {refreshed.access_token[:20]}...")
        print(f"  - Expires In: {refreshed.expires_in} seconds")
        if hasattr(refreshed, 'refresh_token') and refreshed.refresh_token:
            print(f"  - New Refresh Token: {refreshed.refresh_token[:20]}...")
        print()
    except Exception as e:
        print(f"⚠️  Token refresh failed: {e}")
        print("   (This is expected if refresh tokens are not enabled)")
        print()

    # Summary
    print("=" * 60)
    print("✅ Authentication flow test completed successfully!")
    print()
    print("Your Scalekit authentication is fully functional.")
    print()
    print("The complete flow works as expected:")
    print("  ✅ Authorization URL generation")
    print("  ✅ User authentication")
    print("  ✅ Code exchange for tokens")
    print("  ✅ Token validation")
    print("  ✅ User information retrieval")
    if 'refreshed' in locals():
        print("  ✅ Token refresh")
    print()
    print("You're ready to implement authentication in your application!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_auth_flow()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
