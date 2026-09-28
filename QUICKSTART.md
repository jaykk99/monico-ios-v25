# QUICKSTART.md

This guide provides a 3-step setup process to get your Monico-iOS project ready for deployment.

## Step 1: Verify the app files

`app.py`, `pyproject.toml`, and `resources/ui/index.html` are the source of
truth — there is no separate "production copy" step and no placeholder files
to copy over them.

## Step 2: Initialize and Push to GitHub

Next, initialize your Git repository, add your files, commit them, and push to GitHub. **Remember to replace `YOUR_USERNAME` with your actual GitHub username.**

```bash
git init
git add .
git commit -m "Initial: MONICO iOS v2.5"
git remote add origin https://github.com/YOUR_USERNAME/monico-ios.git
git push -u origin main
```

## Step 3: CI/CD is already wired

The GitHub Actions workflow at `.github/workflows/ios_build.yml` builds the
iOS app on `macos-latest` on every push. Nothing to copy — just push:

```bash
git add -A
git commit -m "Your change"
git push
```

Your GitHub repository is now set up with your Monico-iOS app and CI/CD!
