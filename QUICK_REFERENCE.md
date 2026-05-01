# QUICK_REFERENCE.md

This document provides a quick reference for common commands and important files for your Monico-iOS project.

## GitHub Commands

*   **Initialize Git repository**: `git init`
*   **Add all files**: `git add .`
*   **Commit changes**: `git commit -m "Your commit message"`
*   **Add remote origin**: `git remote add origin https://github.com/YOUR_USERNAME/monico-ios.git`
*   **Push to GitHub**: `git push -u origin main`

## Briefcase Commands (for iOS deployment)

*   **Build for device**: `briefcase build ios --device`
*   **Run on device**: `briefcase run ios --device`
*   **Build for release**: `briefcase build ios --release`

## Critical Files

*   `app.py`: Main application logic (copied from `app_production.py`)
*   `resources/ui/index.html`: User interface (copied from `index_production.html`)
*   `pyproject.toml`: Project configuration for Briefcase (copied from `pyproject_production.toml`)
*   `requirements.txt`: Python dependencies
*   `.github/workflows/build.yml`: GitHub Actions CI/CD workflow

## Deployment Phases Overview

| Phase             | Description                                      | Estimated Time |
| :---------------- | :----------------------------------------------- | :------------- |
| **GitHub**        | Repository setup, initial push, CI/CD            | 30 minutes     |
| **iPhone Testing**| Build and run on device, functional testing      | 1-2 hours      |
| **App Store**     | Release build, App Store Connect submission      | 2-3 hours      |
