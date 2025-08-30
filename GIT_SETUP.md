# 🚀 Git Setup and Troubleshooting Guide

## 📋 **Common Git Upload Issues & Solutions**

### **1. Large File Issues**
- **Problem**: Files larger than 100MB can cause git push failures
- **Solution**: Use `.gitignore` to exclude large files (already configured)

### **2. Binary File Handling**
- **Problem**: Binary files being treated as text
- **Solution**: `.gitattributes` file already configured for proper binary handling

### **3. Database Files**
- **Problem**: `db.sqlite3` should not be in version control
- **Solution**: Already in `.gitignore`

### **4. Media and Static Files**
- **Problem**: User uploads and collected static files
- **Solution**: Already in `.gitignore`

## 🛠️ **Quick Fix Commands**

### **Clean Repository:**
```bash
# Remove cached files that should be ignored
git rm -r --cached .
git add .

# Clean untracked files
git clean -fd

# Check status
git status
```

### **Reset and Start Fresh:**
```bash
# If you have serious issues, reset to last good commit
git reset --hard HEAD~1
git clean -fd
git add .
git commit -m "Clean commit"
```

## 📁 **Files to Check**

### **✅ Should be tracked:**
- `*.py` (Python source files)
- `*.html` (Django templates)
- `*.css`, `*.js` (Static files)
- `*.md` (Documentation)
- `requirements.txt`
- `manage.py`
- `settings.py`, `urls.py`

### **❌ Should NOT be tracked:**
- `db.sqlite3` (Database)
- `__pycache__/` (Python cache)
- `venv/` (Virtual environment)
- `media/` (User uploads)
- `staticfiles/` (Collected static)
- `.DS_Store` (macOS files)
- `*.log` (Log files)

## 🔧 **Requirements.txt Issues**

### **Current Issues Fixed:**
1. **weasyprint**: Commented out (can cause installation issues)
2. **Version conflicts**: All versions are compatible
3. **Missing dependencies**: Core Django dependencies included

### **If you need weasyprint:**
```bash
# Install system dependencies first (Ubuntu/Debian)
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Then uncomment in requirements.txt
# weasyprint==65.0
```

## 🚨 **Emergency Git Reset**

If everything is broken:

```bash
# Backup your changes first
cp -r . ../cleanhandy_backup

# Reset to remote
git fetch origin
git reset --hard origin/main
git clean -fd

# Re-add your changes
git add .
git commit -m "Restored changes"
```

## 📝 **Best Practices**

### **Before Committing:**
1. Check `git status`
2. Ensure no large files
3. Verify `.gitignore` is working
4. Test your changes locally

### **Commit Messages:**
```bash
git commit -m "feat: add commercial booking support"
git commit -m "fix: resolve template syntax errors"
git commit -m "docs: update git setup guide"
```

## 🆘 **Still Having Issues?**

1. **Check file sizes**: `find . -type f -size +10M`
2. **Check git status**: `git status --ignored`
3. **Check remote**: `git remote -v`
4. **Check branch**: `git branch -a`

### **Common Error Messages:**
- **"File too large"**: Use `.gitignore` to exclude
- **"Authentication failed"**: Check your git credentials
- **"Push rejected"**: Pull latest changes first
- **"Merge conflicts"**: Resolve conflicts manually

## 📞 **Need Help?**

Run the cleanup script:
```bash
./cleanup_git.sh
```

This will automatically clean up common issues and show you the current git status.
