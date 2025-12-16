#!/bin/bash
#
# Scalekit Authentication Skill - Local Installation Script
#
# This script installs the skill to your local Claude Code installation,
# making it available for your personal use.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print header
print_header() {
    echo "============================================================"
    echo "Scalekit Authentication Skill - Local Installation"
    echo "============================================================"
    echo ""
}

# Check if we're in the skill directory
check_skill_directory() {
    if [ ! -f "SKILL.md" ]; then
        print_error "SKILL.md not found in current directory"
        echo "Please run this script from the scalekit-auth-skill directory"
        exit 1
    fi
    print_success "Skill directory validated"
}

# Detect Claude Code skills directory
detect_skills_directory() {
    local skills_dir=""

    # Check for project-specific .claude/skills
    if [ -d ".claude/skills" ]; then
        skills_dir=".claude/skills"
        print_info "Found project-specific skills directory: $skills_dir"
    # Check for global ~/.claude/skills
    elif [ -d "$HOME/.claude/skills" ]; then
        skills_dir="$HOME/.claude/skills"
        print_info "Found global skills directory: $skills_dir"
    else
        # Offer to create
        print_warning "No Claude Code skills directory found"
        echo ""
        echo "Where would you like to install the skill?"
        echo "  1) Global (all projects): ~/.claude/skills/"
        echo "  2) Project-specific: .claude/skills/"
        echo ""
        read -p "Enter choice (1 or 2): " choice

        case $choice in
            1)
                skills_dir="$HOME/.claude/skills"
                ;;
            2)
                skills_dir=".claude/skills"
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac

        # Create directory
        mkdir -p "$skills_dir"
        print_success "Created skills directory: $skills_dir"
    fi

    echo "$skills_dir"
}

# Install skill
install_skill() {
    local skills_dir="$1"
    local target_dir="$skills_dir/scalekit-auth"

    echo ""
    print_info "Installing skill to: $target_dir"
    echo ""

    # Check if skill already exists
    if [ -d "$target_dir" ]; then
        print_warning "Skill already exists at $target_dir"
        read -p "Overwrite existing installation? (y/N): " overwrite

        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled"
            exit 0
        fi

        rm -rf "$target_dir"
        print_info "Removed existing installation"
    fi

    # Create target directory
    mkdir -p "$target_dir"

    # Copy files
    print_info "Copying skill files..."

    # Copy skill directory (contains SKILL.md and all templates)
    if [ -d "skills/scalekit-auth" ]; then
        cp -r skills/scalekit-auth/* "$target_dir/" && echo "  ✅ skills/scalekit-auth/"
    fi

    # Copy README.md for reference
    if [ -f "README.md" ]; then
        cp README.md "$target_dir/" && echo "  ✅ README.md"
    fi

    # Make scripts executable if they exist
    if [ -d "$target_dir/scripts" ]; then
        chmod +x "$target_dir/scripts"/*.py 2>/dev/null || true
    fi

    # Clean up Python cache files
    find "$target_dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$target_dir" -type f -name "*.pyc" -delete 2>/dev/null || true

    print_success "Skill files copied successfully"
}

# Verify installation
verify_installation() {
    local target_dir="$1"

    echo ""
    print_info "Verifying installation..."

    local required_files=(
        "SKILL.md"
        "full-stack-auth/quickstart.md"
        "full-stack-auth/templates/nodejs-express.md"
        "full-stack-auth/templates/nextjs.md"
        "full-stack-auth/templates/python-fastapi.md"
        "reference/session-management.md"
        "reference/security-best-practices.md"
        "scripts/validate_env.py"
        "scripts/test_connection.py"
        "scripts/test_auth_flow.py"
    )

    local all_present=true

    for file in "${required_files[@]}"; do
        if [ -f "$target_dir/$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (missing)"
            all_present=false
        fi
    done

    echo ""

    if [ "$all_present" = true ]; then
        print_success "All required files present"
        return 0
    else
        print_error "Some files are missing"
        return 1
    fi
}

# Print success message
print_success_message() {
    local skills_dir="$1"
    local target_dir="$skills_dir/scalekit-auth"

    echo ""
    echo "============================================================"
    print_success "Skill installed successfully!"
    echo "============================================================"
    echo ""
    echo "Installation location: $target_dir"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Test the skill with Claude Code:"
    echo "     $ claude"
    echo '     > "Help me implement Scalekit authentication in Express"'
    echo ""
    echo "  2. Run validation scripts:"
    echo "     $ cd $target_dir"
    echo "     $ python scripts/validate_env.py"
    echo ""
    echo "  3. See TESTING.md for comprehensive test scenarios"
    echo ""
    echo "Example prompts to try:"
    echo '  • "Add Scalekit auth to my Next.js app"'
    echo '  • "Implement Scalekit authentication in FastAPI"'
    echo '  • "Help me secure my Express routes with Scalekit"'
    echo ""
    echo "Documentation:"
    echo "  • Skill overview: $target_dir/README.md"
    echo "  • Quick start: $target_dir/full-stack-auth/quickstart.md"
    echo "  • Templates: $target_dir/full-stack-auth/templates/"
    echo ""
    echo "============================================================"
}

# Main installation flow
main() {
    print_header

    # Check we're in the right directory
    check_skill_directory

    # Detect or prompt for skills directory
    skills_dir=$(detect_skills_directory)

    # Install skill
    install_skill "$skills_dir"

    # Verify installation
    if verify_installation "$skills_dir/scalekit-auth"; then
        print_success_message "$skills_dir"
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

# Run main function
main
