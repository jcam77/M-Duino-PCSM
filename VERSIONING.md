# Versioning Guide

This is the `M-Duino-PCSM` versioning workflow.

The safe rule is:

- develop on `AI-Updates`
- release from `main`
- create the release tag from `main`

## Branch Meaning

- `AI-Updates`: development branch
- `main`: stable branch for releases

## Two Kinds of Versions in This Repo

This project currently does not use `package.json` or `npm version`.

Instead, there are two version layers:

1. Internal file revisions

- Used in filenames such as `M-Duino-PCSM_Project_Brief_v000.md`
- Used in firmware folders and files such as `M_Duino_v002/M_Duino_v002.ino`
- These help track working revisions of documents, diagrams, and firmware snapshots

2. Public release versions

- Tracked with annotated Git tags on `main`
- Use semantic versioning for releases:
  `MAJOR.MINOR.PATCH`
- Recommended tag format:
  `mduino-pcsm-vMAJOR.MINOR.PATCH`

Short version:

```text
develop on AI-Updates -> test -> commit -> merge into main -> tag on main
```

## Main Workflow

These are the steps:

1. Make changes in `AI-Updates`.
2. Test the changes in `AI-Updates`.
3. If the changes work, commit and push them to `AI-Updates`.
4. When you are ready to release, switch to `main`.
5. Pull the latest `main`.
6. Merge `AI-Updates` into `main`.
7. Push `main`.
8. Create the release tag from `main`.
9. Push the tag.

## Development Steps

Use this while building features:

```bash
git switch AI-Updates
git status --short --branch
```

Make your changes, test them, then commit and push:

```bash
git add .
git commit -m "update"
git push origin AI-Updates
```

Important:

- do not create the release tag from `AI-Updates`
- do not make the public release from `AI-Updates`

## Internal File Revision Rules

Use `_vNNN` style revisions for working artifacts stored in the repository.

Examples already present in this repo:

- `M-Duino-PCSM_Project_Brief_v000.md`
- `Trigger_Box_Controller_Explanation_v000.md`
- `trigger_box_sequence_diagram_v002.png`
- `M_Duino_v002/M_Duino_v002.ino`

Recommended rule:

- use `_v000` for the first tracked revision
- increase by one for each saved milestone: `_v001`, `_v002`, `_v003`
- keep the filename and the internal reference aligned when both exist

Example:

```text
M_Duino_v002.ino -> M_Duino_v003.ino
trigger_box_sequence_diagram_v002.png -> trigger_box_sequence_diagram_v003.png
```

Use internal file revision bumps when:

- you want to preserve a prior milestone as a separate file
- a document, diagram, or firmware snapshot has materially changed

Do not confuse internal file revisions with public release tags:

- `_v003` in a filename is not the same thing as release `0.3.0`
- release tags must still be created from `main`

## Release Steps

Use this only when you want to publish a stable project version.

### 1. Make sure the working tree is clean

Before switching branches:

```bash
git status --short --branch
```

If there are local edits, clean them first.

If you want to discard all local unstaged changes:

```bash
git restore .
```

Why this matters:

- if `git switch main` fails, you stay on the current branch
- if you stay on `AI-Updates`, the release tag can be created from the wrong branch

### 2. Switch to `main`

```bash
git switch main
git pull --ff-only origin main
git branch --show-current
```

This must print:

```text
main
```

If Git prints `Aborting`, stop there. You are not on `main`.

### 3. Merge `AI-Updates` into `main`

First switch to `main`, then merge `AI-Updates` into it:

```bash
git switch main
git merge AI-Updates
git push origin main
```

This is the step that moves the tested development work into the release branch.

If there are merge conflicts:

- resolve them first
- complete the merge
- push `main`
- only then continue

### 4. Confirm you are still on `main`

```bash
git branch --show-current
```

This must still print:

```text
main
```

### 5. Create the release tag from `main`

Use the format:

```text
mduino-pcsm-vMAJOR.MINOR.PATCH
```

Example:

```bash
git tag -a mduino-pcsm-v0.1.0 -m "mduino-pcsm-v0.1.0"
git push origin mduino-pcsm-v0.1.0
```

## Full Release Example (AI)
```bash
git switch AI-Updates
git status --short --branch
git diff                          
git add -p                        
git commit -m "Fix: Branch renaming"
git push origin AI-Updates
git switch main
git pull --ff-only origin main
git merge --squash AI-Updates
git commit -m "Release v0.1.9: Branch renaming"
git push origin main
git tag -a mduino-pcsm-v0.1.9 -m "Branch renaming"
git push origin mduino-pcsm-v0.1.9
git switch AI-Updates
git merge main
git push origin AI-Updates
```
## What To Remember

- develop in `AI-Updates`
- test in `AI-Updates`
- commit to `AI-Updates`
- merge into `main`
- tag on `main`
- use `_vNNN` for internal file milestones when needed

## What Not To Do

- do not tag from `AI-Updates`
- do not continue if `git switch main` fails
- do not ignore an `Aborting` message from Git
- do not reuse an existing tag name unless you intentionally want to replace it
- do not treat filename revisions like public release versions

## If Something Goes Wrong

### `git switch main` fails

That usually means you still have local changes.

Check:

```bash
git status --short --branch
```

Then restore, commit, or stash the blocking changes.

If you want to discard all local unstaged changes:

```bash
git restore .
```

### You created the tag from the wrong branch

Check:

```bash
git show --no-patch --decorate <tag-name>
git branch --show-current
```

If the tag was already pushed, be careful. In many cases, creating a new patch version is safer than rewriting a public tag.

## SemVer Notes

- Bug fix: increase `PATCH`
  Example: `0.1.0` -> `0.1.1`
- Backward-compatible feature: increase `MINOR`
  Example: `0.1.0` -> `0.2.0`
- Breaking change: increase `MAJOR`
  Example: `0.1.0` -> `1.0.0`

## Useful Commands

Show current branch:

```bash
git branch --show-current
```

Show current version string:

```bash
git describe --tags --always --dirty
```

List project release tags:

```bash
git tag --list 'mduino-pcsm-v*'
```
