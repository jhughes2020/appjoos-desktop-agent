# GitHub Setup Guide

This guide explains the simplest way to get this project into GitHub.

## 1) Create a new repository on GitHub

Suggested name:

```text
desktop-agent-v0-1
```

You can make it private first, then switch to public later if you want to share it.

## 2) Open a terminal in the project folder

Example:

```bash
cd desktop_agent_v0_1
```

## 3) Initialize Git

```bash
git init
```

## 4) Add files

```bash
git add .
```

## 5) Create your first commit

```bash
git commit -m "Initial Desktop Agent v0.1 scaffold"
```

## 6) Connect the local project to GitHub

Replace the URL below with your own repo URL.

HTTPS example:

```bash
git remote add origin https://github.com/YOUR_USERNAME/desktop-agent-v0-1.git
```

SSH example:

```bash
git remote add origin git@github.com:YOUR_USERNAME/desktop-agent-v0-1.git
```

## 7) Push the project

```bash
git branch -M main
git push -u origin main
```

## 8) Improve the repository page

Add these next:
- a short project description
- one screenshot of the app window
- a short roadmap section
- a Releases section later when you start packaging executables

## Suggested commit pattern for juniors

Use small, clear commits such as:

```text
Add live metric cards
Add SQLite snapshot storage
Add markdown report generator
Refactor analyzer thresholds into settings
```

## Suggested GitHub roadmap section

```markdown
## Roadmap

- [x] v0.1 live system dashboard
- [x] v0.1 SQLite snapshot storage
- [x] v0.1 markdown report generation
- [ ] v0.2 trend charts
- [ ] v0.3 Ollama local summaries
- [ ] v0.4 plugins and custom profiles
```
