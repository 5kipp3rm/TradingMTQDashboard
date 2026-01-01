# Submodule Push Guide: Dashboard Changes

## Problem
When trying to push dashboard submodule changes, you encounter:
```
remote: Permission to 5kipp3rm/TradingMTQDashboard.git denied to mfinkels_cisco.
```

This happens because Git is using HTTPS authentication with the wrong GitHub account.

## Solution: Switch to SSH Authentication

### Step 1: Verify Your SSH Authentication

Check which GitHub account your SSH key is associated with:

```bash
ssh -T git@github.com
```

**Expected output:**
```
Hi mfinkelstine! You've successfully authenticated, but GitHub does not provide shell access.
```

This confirms you're authenticated as `mfinkelstine` (your personal account).

### Step 2: Navigate to the Dashboard Submodule

```bash
cd /Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ/dashboard
```

### Step 3: Check Current Remote URL

```bash
git remote get-url origin
```

**Current output:**
```
https://github.com/5kipp3rm/TradingMTQDashboard
```

This is using HTTPS, which is causing the authentication issue.

### Step 4: Switch Remote URL to SSH

```bash
git remote set-url origin git@github.com:5kipp3rm/TradingMTQDashboard.git
```

### Step 5: Verify the Change

```bash
git remote get-url origin
```

**Expected output:**
```
git@github.com:5kipp3rm/TradingMTQDashboard.git
```

### Step 6: Check Git Status

```bash
git status
```

**Expected output:**
```
On branch lovely-dashboard-refactor
Your branch is ahead of 'origin/lovely-dashboard-refactor' by 1 commit.
  (use "git push" to publish your local commits)
```

### Step 7: Push Your Changes

```bash
git push origin lovely-dashboard-refactor
```

**Expected output:**
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
...
To github.com:5kipp3rm/TradingMTQDashboard.git
   old_hash..new_hash  lovely-dashboard-refactor -> lovely-dashboard-refactor
```

### Step 8: Update Parent Repository (Optional but Recommended)

After pushing the submodule changes, update the parent repository to reference the new commit:

```bash
# Return to parent directory
cd /Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ

# Check status - should show dashboard as modified
git status

# Add the submodule reference update
git add dashboard

# Commit the update
git commit -m "Update dashboard submodule to latest commit

- Include latest dashboard changes from lovely-dashboard-refactor branch"

# Push to parent repository
git push origin feature/phase1-config-oop
```

## Complete Command Sequence

Here's the complete sequence of commands to copy and paste:

```bash
# Navigate to dashboard
cd /Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ/dashboard

# Switch to SSH
git remote set-url origin git@github.com:5kipp3rm/TradingMTQDashboard.git

# Verify the change
git remote get-url origin

# Push changes
git push origin lovely-dashboard-refactor

# Return to parent and update reference
cd ..
git add dashboard
git commit -m "Update dashboard submodule to latest commit"
git push origin feature/phase1-config-oop
```

## Troubleshooting

### Issue: SSH Key Not Added to GitHub

If you get "Permission denied (publickey)", add your SSH key to GitHub:

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_rsa.pub
   # or
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the key and save

### Issue: Wrong SSH Key Being Used

If you have multiple SSH keys, configure SSH to use the correct one:

```bash
# Edit SSH config
nano ~/.ssh/config
```

Add:
```
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_personal

Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_work
```

Then use:
```bash
git remote set-url origin git@github.com-personal:5kipp3rm/TradingMTQDashboard.git
```

### Issue: No Push Access to Repository

If `mfinkelstine` doesn't have push access to `5kipp3rm/TradingMTQDashboard`:

1. Ask the repository owner (`5kipp3rm`) to add you as a collaborator
2. Or fork the repository and push to your fork instead

## Alternative: Using Personal Access Token (PAT)

If you prefer to keep HTTPS authentication:

### Step 1: Generate PAT

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "TradingMTQ Dashboard"
4. Select scopes: `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

### Step 2: Configure Git to Use PAT

```bash
cd /Users/mfinkels/CodePlatform/PersonalCode/TradingMTQ/dashboard

# Option A: Store in credential helper (recommended)
git config credential.helper store
git push origin lovely-dashboard-refactor
# When prompted, enter:
# Username: mfinkelstine (or 5kipp3rm)
# Password: <paste your PAT>

# Option B: Include in URL (less secure)
git remote set-url origin https://YOUR_PAT@github.com/5kipp3rm/TradingMTQDashboard.git
git push origin lovely-dashboard-refactor
```

## Best Practice: SSH vs HTTPS

**SSH (Recommended):**
- ✅ More secure
- ✅ No password/token needed after setup
- ✅ Works seamlessly with multiple keys
- ✅ Better for frequent pushes

**HTTPS with PAT:**
- ✅ Works behind restrictive firewalls
- ✅ Easier for CI/CD systems
- ❌ Requires token management
- ❌ Token can expire

## Summary

1. **Problem:** HTTPS auth using wrong GitHub account (`mfinkels_cisco` instead of `mfinkelstine`)
2. **Solution:** Switch to SSH authentication which uses your existing SSH key
3. **Commands:**
   - `git remote set-url origin git@github.com:5kipp3rm/TradingMTQDashboard.git`
   - `git push origin lovely-dashboard-refactor`
4. **Follow-up:** Update parent repository to reference the new submodule commit

---

**Next Steps:**
- [ ] Switch dashboard remote to SSH
- [ ] Push dashboard changes
- [ ] Update parent repository reference
- [ ] Verify changes on GitHub
