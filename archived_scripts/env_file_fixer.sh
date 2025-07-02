#!/bin/bash
# Fix .env file parsing issues

echo "🔍 Checking .env file for parsing issues..."
echo "=============================================="

# Show line numbers with content
echo "📄 .env file content with line numbers:"
cat -n .env

echo ""
echo "🔍 Checking for common .env parsing issues:"

# Check for lines with issues
echo ""
echo "📋 Line 8 specifically:"
sed -n '8p' .env

echo ""
echo "🔍 Common issues to look for:"
echo "   - Missing quotes around values with spaces"
echo "   - Special characters not escaped"
echo "   - Lines with = but no value"
echo "   - Comments not starting with #"
echo "   - Windows line endings (CRLF instead of LF)"

echo ""
echo "🔧 Checking for specific issues:"

# Check for missing values
echo "Lines with missing values after =:"
grep -n "=$" .env || echo "   ✅ No missing values found"

# Check for unquoted spaces
echo "Lines with unquoted spaces:"
grep -n "=[^\"'][^=]*\s" .env || echo "   ✅ No unquoted spaces found"

# Check for Windows line endings
echo "Checking for Windows line endings:"
file .env | grep -q CRLF && echo "   ❌ Windows line endings detected" || echo "   ✅ Unix line endings OK"

echo ""
echo "🔧 RECOMMENDED FIXES:"
echo "1. Check line 8 for syntax issues"
echo "2. Ensure all values with spaces are quoted"
echo "3. Remove any trailing spaces after values"
echo "4. Convert Windows line endings to Unix if needed"

echo ""
echo "📝 To fix common issues, run:"
echo "   # Remove Windows line endings:"
echo "   dos2unix .env"
echo ""
echo "   # Remove trailing spaces:"
echo "   sed -i 's/[[:space:]]*$//' .env"