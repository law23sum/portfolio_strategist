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
