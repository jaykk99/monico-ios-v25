# QUICKSTART.md

This guide provides a 3-step setup process to get your Monico-iOS project ready for deployment.

## Step 1: Prepare Production Files

First, copy the production-ready files to their active locations:

```bash
cp app_production.py app.py
cp index_production.html resources/ui/index.html
cp pyproject_production.toml pyproject.toml
```

## Step 2: Initialize and Push to GitHub

Next, initialize your Git repository, add your files, commit them, and push to GitHub. **Remember to replace `YOUR_USERNAME` with your actual GitHub username.**

```bash
git init
git add .
git commit -m "Initial: MONICO iOS v2.5"
git remote add origin https://github.com/YOUR_USERNAME/monico-ios.git
git push -u origin main
```

## Step 3: Add CI/CD Workflow

Finally, set up your GitHub Actions workflow for continuous integration and deployment:

```bash
mkdir -p .github/workflows
cp .github_workflows_build.yml .github/workflows/build.yml
git add .github/workflows/build.yml
git commit -m "Add CI/CD"
git push
```

Your GitHub repository is now set up with your Monico-iOS app and CI/CD!
