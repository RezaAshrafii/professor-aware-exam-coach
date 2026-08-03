# Update the existing GitHub repository to v0.7.0

The safest update artifact is `ACOS_v0.7.0.bundle`. It carries the exact commits and tag without replacing your `.git` folder.

From the existing repository root:

```powershell
git status
git fetch .\ACOS_v0.7.0.bundle main:v0.7-update
git checkout main
git merge --ff-only v0.7-update
git push origin main
git push origin --tags
git branch -d v0.7-update
```

Then run:

```powershell
.\start_product_windows.bat
```

The dependency bootstrap may run once because backend requirements changed. Future launches skip installation unless dependency files change again.
