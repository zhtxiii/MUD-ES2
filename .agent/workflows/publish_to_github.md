---
description: Initialize a git repository and publish it to a new GitHub remote
---

This workflow helps you upload the current project to GitHub.

1. Initialize Git Repository
   // turbo
   git init

2. Add all files to staging
   // turbo
   git add .

3. Commit files
   // turbo
   git commit -m "Initial commit" || echo "Nothing to commit"

4. Rename branch to main
   // turbo
   git branch -m master main 2>/dev/null || true

5. Configure Remote and Push
   Ask the user for the GitHub Repository URL if you don't have it.
   Then run:
   git remote add origin <URL>
   git push -u origin main
