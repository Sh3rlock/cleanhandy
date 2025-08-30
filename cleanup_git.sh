#!/bin/bash

echo "🧹 Cleaning up git repository..."

# Remove any cached files that should be ignored
echo "📁 Removing cached files that should be ignored..."
git rm -r --cached . 2>/dev/null || true
git add .

# Clean up any untracked files
echo "🗑️ Cleaning untracked files..."
git clean -fd

# Check for any large files that might cause issues
echo "🔍 Checking for large files..."
find . -type f -size +50M -not -path "./.git/*" -not -path "./venv/*" -not -path "./staticfiles/*" -not -path "./media/*" 2>/dev/null || true

# Check git status
echo "📊 Current git status:"
git status

echo "✅ Cleanup complete!"
echo ""
echo "If you still have issues, try:"
echo "1. git add ."
echo "2. git commit -m 'Your commit message'"
echo "3. git push origin main"
