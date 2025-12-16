#!/usr/bin/env python3
"""
Scalekit Authentication Skill Installer

This script installs the Scalekit authentication skill to your Claude workspace
via the Anthropic API, making it available to all workspace members.
"""

import os
import sys
import zipfile
from pathlib import Path

try:
    import anthropic
    from anthropic.lib import files_from_dir
except ImportError:
    print("❌ anthropic package not installed")
    print("   Install with: pip install anthropic")
    sys.exit(1)


def get_api_key():
    """Get Anthropic API key from environment or prompt user"""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Anthropic API key not found in environment.")
        print()
        api_key = input("Enter your Anthropic API key: ").strip()

        if not api_key:
            print("❌ API key is required")
            sys.exit(1)

    return api_key


def get_skill_directory():
    """Get the skill directory path"""
    script_dir = Path(__file__).parent
    skill_dir = script_dir

    # Check if we're in the skill directory
    if not (skill_dir / "SKILL.md").exists():
        print("❌ SKILL.md not found in current directory")
        print(f"   Expected location: {skill_dir / 'SKILL.md'}")
        sys.exit(1)

    return skill_dir


def validate_skill_structure(skill_dir):
    """Validate that the skill has all required files"""
    required_files = [
        "skills/scalekit-auth/SKILL.md",
        "skills/scalekit-auth/full-stack-auth/quickstart.md",
        "skills/scalekit-auth/full-stack-auth/templates/nodejs-express.md",
        "skills/scalekit-auth/full-stack-auth/templates/nextjs.md",
        "skills/scalekit-auth/full-stack-auth/templates/python-fastapi.md",
        "skills/scalekit-auth/reference/session-management.md",
        "skills/scalekit-auth/reference/security-best-practices.md",
        "skills/scalekit-auth/scripts/validate_env.py",
        "skills/scalekit-auth/scripts/test_connection.py",
        "skills/scalekit-auth/scripts/test_auth_flow.py",
    ]

    print("Validating skill structure...")
    missing_files = []

    for file_path in required_files:
        full_path = skill_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")

    if missing_files:
        print()
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        sys.exit(1)

    print()
    return True


def create_zip_file(skill_dir):
    """Create a temporary zip file of the skill"""
    import tempfile

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    zip_path = temp_zip.name
    temp_zip.close()

    print("Creating skill package...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files except Python cache and system files
        for root, dirs, files in os.walk(skill_dir):
            # Skip __pycache__ and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.startswith('.') or file.endswith('.pyc'):
                    continue

                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_dir)

                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")

    print(f"✅ Package created: {zip_path}")
    print()
    return zip_path


def install_skill(api_key, skill_dir, method='directory'):
    """Install the skill to Claude workspace"""
    print("=" * 60)
    print("Scalekit Authentication Skill Installer")
    print("=" * 60)
    print()

    # Initialize client
    print("Initializing Anthropic client...")
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Client initialized")
    print()

    # Validate skill structure
    validate_skill_structure(skill_dir)

    # Upload skill
    print("Uploading skill to your workspace...")
    print("This may take a minute...")
    print()

    try:
        if method == 'directory':
            # Upload from directory (recommended)
            skill = client.beta.skills.create(
                display_title="Scalekit Authentication",
                files=files_from_dir(str(skill_dir)),
                betas=["skills-2025-10-02"]
            )
        else:
            # Upload as zip file
            zip_path = create_zip_file(skill_dir)
            try:
                with open(zip_path, 'rb') as f:
                    skill = client.beta.skills.create(
                        display_title="Scalekit Authentication",
                        files=[("scalekit-auth-skill.zip", f)],
                        betas=["skills-2025-10-02"]
                    )
            finally:
                # Clean up temp zip file
                os.unlink(zip_path)

        print("=" * 60)
        print("✅ Skill installed successfully!")
        print("=" * 60)
        print()
        print(f"Skill ID: {skill.id}")
        print(f"Display Title: Scalekit Authentication")
        print(f"Version: {skill.version}")
        print()
        print("The skill is now available to all members of your workspace.")
        print()
        print("Next steps:")
        print("  1. Test the skill by asking Claude to implement Scalekit authentication")
        print("  2. See TESTING.md for comprehensive testing scenarios")
        print("  3. Share with your team!")
        print()
        print("Example usage:")
        print('  "Help me implement Scalekit authentication in my Express app"')
        print('  "Add Scalekit auth to my Next.js application"')
        print('  "Implement Scalekit in FastAPI"')
        print()
        print("=" * 60)

        return skill

    except anthropic.BadRequestError as e:
        print("❌ Failed to upload skill")
        print(f"   Error: {e}")
        print()
        print("Common issues:")
        print("  - API key doesn't have permission to create skills")
        print("  - Skill files are too large")
        print("  - Invalid file format")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main installation flow"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install Scalekit Authentication Skill to Claude workspace"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY environment variable)",
        default=None
    )
    parser.add_argument(
        "--method",
        choices=["directory", "zip"],
        default="directory",
        help="Upload method: directory (faster) or zip (more compatible)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or get_api_key()

    # Get skill directory
    skill_dir = get_skill_directory()

    print(f"Skill directory: {skill_dir}")
    print(f"Upload method: {args.method}")
    print()

    # Install skill
    install_skill(api_key, skill_dir, method=args.method)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
