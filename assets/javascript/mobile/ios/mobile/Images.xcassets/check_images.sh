#!/bin/bash

echo "🔍 Checking iOS Icon Images..."
echo ""

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON_COUNT=0
MISSING_COUNT=0

echo "Checking icon imagesets in: $BASE_DIR"
echo ""

# Check each imageset
for imageset in "$BASE_DIR"/icon-*.imageset; do
    if [ -d "$imageset" ]; then
        ICON_NAME=$(basename "$imageset" .imageset)
        ICON_COUNT=$((ICON_COUNT + 1))
        
        # Check for required files
        HAS_2X=false
        HAS_3X=false
        HAS_JSON=false
        
        if [ -f "$imageset/${ICON_NAME}@2x.png" ]; then
            HAS_2X=true
        fi
        if [ -f "$imageset/${ICON_NAME}@3x.png" ]; then
            HAS_3X=true
        fi
        if [ -f "$imageset/Contents.json" ]; then
            HAS_JSON=true
        fi
        
        if [ "$HAS_2X" = true ] && [ "$HAS_3X" = true ] && [ "$HAS_JSON" = true ]; then
            echo "✅ $ICON_NAME - Complete"
        else
            echo "❌ $ICON_NAME - Missing files:"
            [ "$HAS_2X" = false ] && echo "   - Missing @2x.png"
            [ "$HAS_3X" = false ] && echo "   - Missing @3x.png"
            [ "$HAS_JSON" = false ] && echo "   - Missing Contents.json"
            MISSING_COUNT=$((MISSING_COUNT + 1))
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "  Total icons: $ICON_COUNT"
echo "  Complete: $((ICON_COUNT - MISSING_COUNT))"
echo "  Missing files: $MISSING_COUNT"
echo ""

if [ $MISSING_COUNT -eq 0 ]; then
    echo "✅ All icons are complete!"
    echo ""
    echo "Next steps:"
    echo "1. Open Xcode: open ../mobile.xcworkspace"
    echo "2. Check Images.xcassets in the Project Navigator"
    echo "3. Verify icons are visible in Xcode's asset catalog"
else
    echo "⚠️  Some icons are missing files"
    echo "Run: python3 generate_icons.py to regenerate"
fi

