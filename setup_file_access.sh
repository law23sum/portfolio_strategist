#!/bin/bash

# Script to set up file access permissions for Cursor AI in Docker containers
# This script ensures proper permissions for local and cloud drive access

set -o errexit
set -o pipefail
set -o nounset

echo "Setting up file access for Cursor AI..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if directory exists and is accessible
check_directory() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $name found: $dir"
        # Try to set permissions (may require sudo on some systems)
        chmod -R u+rwX "$dir" 2>/dev/null || echo -e "${YELLOW}⚠${NC}  Could not modify permissions for $name (may require sudo)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC}  $name not found: $dir (will be created when mounted)"
        return 1
    fi
}

# Check and set permissions for home directory
echo ""
echo "Checking local drive access..."
check_directory "$HOME" "Home directory"

# Check and set permissions for common cloud drive locations
echo ""
echo "Checking cloud drive access..."
check_directory "$HOME/Library/CloudStorage" "iCloud/CloudStorage"
check_directory "$HOME/Google Drive" "Google Drive"
check_directory "$HOME/Dropbox" "Dropbox"
check_directory "$HOME/OneDrive" "OneDrive"
check_directory "$HOME/iCloud Drive" "iCloud Drive"

# Check common document locations
echo ""
echo "Checking document locations..."
check_directory "$HOME/Documents" "Documents"
check_directory "$HOME/Desktop" "Desktop"
check_directory "$HOME/Downloads" "Downloads"

# Create a test script that can be run inside the container
echo ""
echo "Creating test script for container access..."
cat > test_file_access.sh << 'EOF'
#!/bin/bash
# Test script to verify file access from within Docker container

echo "Testing file access from Docker container..."
echo "============================================"

test_path() {
    local path=$1
    local name=$2
    
    if [ -d "$path" ]; then
        if [ -r "$path" ] && [ -w "$path" ]; then
            echo "✓ $name: READ/WRITE access OK"
            ls -ld "$path" | head -1
            return 0
        else
            echo "✗ $name: Permission denied"
            return 1
        fi
    else
        echo "⚠ $name: Directory not found (may not be mounted)"
        return 2
    fi
}

echo ""
echo "Testing host mount points..."
test_path "/host/home" "Home directory"
test_path "/host/cloudstorage" "Cloud Storage"
test_path "/host/googledrive" "Google Drive"
test_path "/host/dropbox" "Dropbox"
test_path "/host/onedrive" "OneDrive"
test_path "/host/iclouddrive" "iCloud Drive"
test_path "/host/documents" "Documents"
test_path "/host/desktop" "Desktop"
test_path "/host/downloads" "Downloads"

echo ""
echo "Testing write access..."
TEST_FILE="/host/home/.cursor_ai_test_$(date +%s).txt"
if touch "$TEST_FILE" 2>/dev/null; then
    echo "✓ Write test successful: $TEST_FILE"
    rm -f "$TEST_FILE"
else
    echo "✗ Write test failed - cannot create files"
fi

echo ""
echo "File access test complete!"
EOF

chmod +x test_file_access.sh
echo -e "${GREEN}✓${NC} Test script created: test_file_access.sh"
echo ""
echo "To test file access from within a container, run:"
echo "  docker compose exec web bash test_file_access.sh"
echo ""
echo "Setup complete!"
echo ""
echo "Note: Some directories may require additional permissions."
echo "If you encounter permission issues, you may need to:"
echo "  1. Run this script with sudo (for system directories)"
echo "  2. Adjust Docker volume mount permissions"
echo "  3. Check macOS privacy settings for Docker"



