# SelfPrivacy API contributors guide

## Commit messages

We follow [Convetional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Please read it before commiting.

Useful plugins for IDEs:

- [VSCode](https://marketplace.visualstudio.com/items?itemName=vivaxy.vscode-conventional-commits)
- [IntelliJ](https://plugins.jetbrains.com/plugin/13389-conventional-commit)

### Track your time

If you are working on a task, please track your time and add it to the commit message. For example:

```
feat: add new feature

- did some work
- did some more work

fixes #4, spent @1h30m
```

[Timewarrior](https://timewarrior.net/) is a good tool for tracking time.

## Code style

We use [Black](
    https://pypi.org/project/black/
) for code formatting. Please install it and run `black .` before commiting.

## Pull requests

Please request a review from at least one of the other maintainers. If you are not sure who to request, request a review from SelfPrivacy/Devs team.
