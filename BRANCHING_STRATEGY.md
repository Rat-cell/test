# Campus Locker System - Branching Strategy

## Safe Development Workflow 🛡️

**Golden Rule: NEVER push directly to `main` branch!**

## Branch Structure

- **`main`** - Production-ready code only (protected)
- **`develop`** - Integration branch for testing features together
- **`feature/*`** - New features (e.g., `feature/new-dashboard`)
- **`bugfix/*`** - Bug fixes (e.g., `bugfix/fix-login-error`)
- **`hotfix/*`** - Emergency fixes (e.g., `hotfix/security-patch`)

## Typical Workflow

### 1. Starting New Work
```bash
# Make sure you're on latest develop
git checkout develop
git pull origin develop

# Create your feature branch
git checkout -b feature/your-feature-name
```

### 2. Working on Your Branch
```bash
# Make your changes, then:
git add .
git commit -m "Clear description of what you changed"

# Push to your branch (not main!)
git push origin feature/your-feature-name
```

### 3. Testing Your Changes
```bash
# Run tests locally before pushing
make test
make lint
make security

# Or run everything at once
make all
```

### 4. Getting Your Code to Main
- Push your branch to GitHub
- Create a Pull Request from your branch → `develop`
- CI/CD will run automatically and check everything
- After review, merge to `develop`
- Later, create PR from `develop` → `main` for releases

## What Happens When You Push

### Push to Your Branch (feature/*, bugfix/*, etc.)
✅ **CI runs**: Tests, linting, security checks
✅ **Safe**: Your experiments won't affect anyone else
✅ **Backup**: Your work is saved on GitHub

### Pull Request to `main` or `develop`
✅ **Full CI pipeline**: All checks run automatically
✅ **Review opportunity**: You can see exactly what will change
✅ **Safety net**: Nothing merges until everything passes

## Quick Commands

```bash
# Check which branch you're on
git branch

# Switch to develop
git checkout develop

# Create new feature branch
git checkout -b feature/my-new-feature

# See what changed
git status
git diff

# Safe commit and push
git add .
git commit -m "Add new feature"
git push origin feature/my-new-feature
```

## Benefits of This Approach

- 🛡️ **Main branch is always stable**
- 🧪 **Test changes safely on branches**
- 👥 **Easy collaboration with team members**
- 🔄 **Clear history of what changed when**
- ⚡ **Fast to rollback if something goes wrong**

## Emergency: If You Accidentally Push to Main

```bash
# Don't panic! You can undo it:
git log --oneline -5  # Find the commit before your changes
git reset --hard <commit-hash>
git push --force-with-lease origin main  # Use with extreme caution!
```

Better yet: Set up branch protection in GitHub to prevent this entirely! 