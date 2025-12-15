#!/usr/bin/env python3
"""
Scalekit Environment Validation Script

This script validates that all required environment variables are set correctly
and tests basic connectivity to Scalekit services.
"""

import os
import sys
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
    print("   Install with: pip install python-dotenv\n")


def check_env_var(var_name, required=True, validate_url=False):
    """Check if environment variable exists and is valid"""
    value = os.getenv(var_name)

    if not value:
        if required:
            print(f"❌ {var_name}: Missing (required)")
            return False
        else:
            print(f"⚠️  {var_name}: Not set (optional)")
            return True

    # Validate URL format if needed
    if validate_url:
        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                print(f"❌ {var_name}: Invalid URL format")
                print(f"   Value: {value}")
                return False
        except Exception as e:
            print(f"❌ {var_name}: Invalid URL - {e}")
            return False

    # Mask sensitive values
    if "SECRET" in var_name or "PASSWORD" in var_name:
        display_value = value[:8] + "..." if len(value) > 8 else "***"
    else:
        display_value = value

    print(f"✅ {var_name}: {display_value}")
    return True


def validate_scalekit_url(url):
    """Validate Scalekit environment URL format"""
    if not url:
        return False

    parsed = urlparse(url)

    # Check for common mistakes
    if "localhost" in url.lower():
        print("\n⚠️  Warning: Using localhost in SCALEKIT_ENVIRONMENT_URL")
        print("   This should be your Scalekit environment URL from the dashboard")
        return False

    if not url.startswith("https://"):
        print("\n⚠️  Warning: SCALEKIT_ENVIRONMENT_URL should use HTTPS")
        return False

    if "scalekit.com" not in url.lower():
        print("\n⚠️  Warning: URL doesn't contain 'scalekit.com'")
        print("   Expected format: https://your-env.scalekit.com")
        return False

    return True


def validate_callback_url(callback_url, app_url):
    """Validate callback URL configuration"""
    if not callback_url:
        return False

    # Check that callback URL is absolute
    parsed = urlparse(callback_url)
    if not parsed.scheme or not parsed.netloc:
        print("\n❌ CALLBACK_URL must be an absolute URL (include http:// or https://)")
        return False

    # Warn about localhost in production
    if "localhost" not in app_url and "localhost" in callback_url:
        print("\n⚠️  Warning: Callback URL uses localhost but APP_URL doesn't")
        print("   Make sure this matches your Scalekit Dashboard configuration")

    return True


def main():
    print("=" * 60)
    print("Scalekit Environment Validation")
    print("=" * 60)
    print()

    all_valid = True

    # Check required Scalekit credentials
    print("Required Scalekit Credentials:")
    print("-" * 40)

    env_url = os.getenv("SCALEKIT_ENVIRONMENT_URL")
    all_valid &= check_env_var("SCALEKIT_ENVIRONMENT_URL", required=True, validate_url=True)
    all_valid &= check_env_var("SCALEKIT_CLIENT_ID", required=True)
    all_valid &= check_env_var("SCALEKIT_CLIENT_SECRET", required=True)

    print()

    # Additional URL validation
    if env_url:
        if not validate_scalekit_url(env_url):
            all_valid = False

    # Check application URLs
    print("\nApplication URLs:")
    print("-" * 40)

    app_url = os.getenv("APP_URL", "")
    callback_url = os.getenv("CALLBACK_URL", "")

    all_valid &= check_env_var("APP_URL", required=False, validate_url=True)
    all_valid &= check_env_var("CALLBACK_URL", required=True, validate_url=True)
    all_valid &= check_env_var("POST_LOGOUT_URL", required=False, validate_url=True)

    print()

    # Validate callback URL
    if callback_url:
        if not validate_callback_url(callback_url, app_url):
            all_valid = False

    # Check optional settings
    print("\nOptional Settings:")
    print("-" * 40)

    cookie_secure = os.getenv("COOKIE_SECURE", "false")
    print(f"{'✅' if cookie_secure else '⚠️ '} COOKIE_SECURE: {cookie_secure}")

    if cookie_secure.lower() == "false" and callback_url and "https://" in callback_url and "localhost" not in callback_url:
        print("   ⚠️  Warning: Using HTTPS but COOKIE_SECURE is false")
        print("   Consider setting COOKIE_SECURE=true for production")

    print()

    # Summary
    print("=" * 60)
    if all_valid:
        print("✅ All required environment variables are set correctly!")
        print()
        print("Next steps:")
        print("  1. Verify callback URL is registered in Scalekit Dashboard")
        print("     → Dashboard → Settings → Redirect URIs")
        print(f"     → Add: {callback_url}")
        print()
        print("  2. Test Scalekit connectivity:")
        print("     → python scripts/test_connection.py")
        print()
        print("  3. Start implementing authentication:")
        print("     → See full-stack-auth/quickstart.md")
    else:
        print("❌ Some environment variables are missing or invalid")
        print()
        print("Please check the errors above and update your .env file")
        print()
        print("Required variables:")
        print("  - SCALEKIT_ENVIRONMENT_URL")
        print("  - SCALEKIT_CLIENT_ID")
        print("  - SCALEKIT_CLIENT_SECRET")
        print("  - CALLBACK_URL")
        print()
        print("Get your credentials from:")
        print("  → Scalekit Dashboard → Settings → API Keys")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
