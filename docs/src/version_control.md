# Version Control

## Conventional Commits

A [specification](https://www.conventionalcommits.org/en/v1.0.0) for adding human and machine readable meaning to commit messages.

**Format**: <type>[optional scope]: <description>

Example `feat: allow provided config object to extend other configs`
Example `fix: fixed the bug in issue #123`

**Advantage**: Automated SemVer version management (major.minor.patch), and automated changelogs.

## Commitizen CLI

[Commitizen](https://commitizen-tools.github.io/commitizen) is a Python tool to help with creating **conventional commits** and automating version control.

### Install

`pip install commitizen`

### Commiting Code

- Instead of `git commit` use `cz commit` and follow the prompts.
- You can select the type of commit, plus additional metadata.

### Bumping a Version

- When you decide it is time to create a new version:

1. Create a new branch

`git checkout -b bump/new_release`

2. Bump the version and push

```bash
pip install commitizen # (if not installed)

cz bump

git push
```

This will:
- Update the SemVer version number in locations specific in `pyproject.toml`, throughout the codebase.
  - If a `feat` commit is included, the version is bumped by a minor increment (0.x.0), if only `fix` is included a patch will be used (0.0.x).
- Automatically update CHANGELOG.md with all changes since the last version.
- Create a tag matching the version number.

> Note: in a repo where you have direct push access, you would simply update on develop and push. As we are using Git-Flow, a PR is necessary.

## Creating Releases

1. Update the version throughout the code ([Bumping a Version](#bumping-a-version)).
2. Click `Draft a new release`.
3. Click `Choose a tag`, then input the current version number and press enter (this will automatically create a matching tag for your release).
4. Set the `Release title` to `x.x.x`, replacing with your version number.
5. Add a description if possible, then release.

