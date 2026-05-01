# GITHUB_DEPLOYMENT_GUIDE.md

This guide details the process of setting up your GitHub repository for the Monico-iOS application, including copying production files, initializing Git, and configuring GitHub Actions for CI/CD.

## Phase 1: GitHub Setup (Today - 30 minutes)

This phase involves preparing your application files, initializing a Git repository, pushing your code to GitHub, and setting up a Continuous Integration/Continuous Deployment (CI/CD) workflow using GitHub Actions.

### Step 1: Copy Production Files

Before pushing to GitHub, ensure that your production-ready application files are in their correct locations. This involves copying the `app_production.py`, `index_production.html`, and `pyproject_production.toml` files.

```bash
cp app_production.py app.py
cp index_production.html resources/ui/index.html
cp pyproject_production.toml pyproject.toml
```

*   `app.py`: This will be the main Python application file.
*   `resources/ui/index.html`: This file contains the user interface for your application.
*   `pyproject.toml`: This file holds the project configuration, particularly for Briefcase, which is used for packaging the iOS app.

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

### Step 3: Add GitHub Actions Workflow

To automate the build process and enable Continuous Integration, you will add a GitHub Actions workflow. This workflow will automatically build your iOS application whenever changes are pushed to the `main` branch or a pull request is opened against it.

```bash
mkdir -p .github/workflows
cp .github_workflows_build.yml .github/workflows/build.yml
git add .github/workflows/build.yml
git commit -m "Add CI/CD"
git push
```

This will:

1.  `mkdir -p .github/workflows`: Create the necessary directory structure for GitHub Actions workflows.
2.  `cp .github_workflows_build.yml .github/workflows/build.yml`: Copy the provided CI/CD workflow file into the GitHub Actions directory.
3.  `git add .github/workflows/build.yml`: Stage the new workflow file.
4.  `git commit -m "Add CI/CD"`: Commit the workflow file with a message indicating the addition of CI/CD.
5.  `git push`: Push the new commit to your GitHub repository.

After these steps, your GitHub repository will be fully set up, and the GitHub Actions workflow will be ready to build your Monico-iOS application automatically.
