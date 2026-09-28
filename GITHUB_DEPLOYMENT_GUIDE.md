# GITHUB_DEPLOYMENT_GUIDE.md

This guide details the process of setting up your GitHub repository for the Monico-iOS application, including copying production files, initializing Git, and configuring GitHub Actions for CI/CD.

## Phase 1: GitHub Setup (Today - 30 minutes)

This phase involves preparing your application files, initializing a Git repository, pushing your code to GitHub, and setting up a Continuous Integration/Continuous Deployment (CI/CD) workflow using GitHub Actions.

### Step 1: Verify the app files

The repository is already live at `https://github.com/jaykk99/monico-ios-v25`.
`app.py`, `pyproject.toml`, and `resources/ui/index.html` are the source of
truth — there is no separate "production copy" step. Do **not** overwrite them
with placeholder files.

### Step 2: Initialize Git Repository and Push to GitHub

Now, you will initialize a new Git repository, add all your project files, commit them, and push them to a new repository on GitHub. **Remember to replace `YOUR_USERNAME` with your actual GitHub username in the `git remote add origin` command.**

```bash
git init
git add .
git commit -m "Initial: MONICO iOS v2.5"
git remote add origin https://github.com/YOUR_USERNAME/monico-ios.git
git push -u origin main
```

This sequence of commands will:

1.  `git init`: Create a new empty Git repository in your current directory.
2.  `git add .`: Stage all changes in the current directory for the next commit.
3.  `git commit -m "Initial: MONICO iOS v2.5"`: Record the staged changes to the repository with a descriptive message.
4.  `git remote add origin https://github.com/YOUR_USERNAME/monico-ios.git`: Add a new remote repository named `origin` with the specified URL. You will need to create this repository on GitHub first.
5.  `git push -u origin main`: Push your committed changes from your local `main` branch to the `main` branch of your `origin` remote repository. The `-u` flag sets the `origin/main` as the upstream branch, allowing you to use `git push` and `git pull` without specifying the remote and branch in the future.

### Step 3: GitHub Actions Workflow

The CI/CD workflow already lives at `.github/workflows/ios_build.yml` and runs
the iOS build on `macos-latest` on every push. No setup step needed — just push:

```bash
git add -A
git commit -m "Your change"
git push
```

After these steps, your GitHub repository will be fully set up, and the GitHub Actions workflow will be ready to build your Monico-iOS application automatically.
