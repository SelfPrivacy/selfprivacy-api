# SelfPrivacy API contributors guide

Instructions for [VScode](https://code.visualstudio.com) or [VScodium](https://github.com/VSCodium/vscodium) under Unix-like platform.

1. **To get started, create an account for yourself on the** [**SelfPrivacy Gitea**](https://git.selfprivacy.org/user/sign_up). Proceed to fork
the [repository](https://git.selfprivacy.org/SelfPrivacy/selfprivacy-rest-api), and clone it on your local computer:

    ```git clone https://git.selfprivacy.org/your_user_name/selfprivacy-rest-api```

2. **Install Nix**

    ```sh <(curl -L https://nixos.org/nix/install)```

    For detailed installation information, please review and follow: [link](https://nixos.org/manual/nix/stable/installation/installing-binary.html#installing-a-binary-distribution).

3. **Change directory to the cloned repository and start a nix development shell:**

    ```cd selfprivacy-rest-api && nix develop```

    Nix will install all of the necessary packages for development work, all further actions will take place only within nix-shell.

4. **Install these plugins for VScode/VScodium**

    Required: ```ms-python.python```, ```ms-python.vscode-pylance```

    Optional, but highly recommended: ```ms-python.black-formatter```, ```bbenoist.Nix```, ```ryanluker.vscode-coverage-gutters```

5. **Set the path to the python interpreter from the nix store.** To do this, execute the command:

    ```whereis python```

    Copy the path that starts with ```/nix/store/``` and ends with ```env/bin/python```

    ```/nix/store/???-python3-3.10.??-env/bin/python```

    Click on the python version selection in the lower right corner, and replace the path to the interpreter in the project with the one you copied from the terminal.

6. **Congratulations :) Now you can develop new changes and test the project locally in a Nix environment.**

## What do you need to know before starting development work?
- RestAPI is no longer utilized, the project has moved to [GraphQL](https://graphql.org), however, the API functionality still works on Rest


## What to do after making changes to the repository?

**Run unit tests** using ```pytest-vm``` inside of the development shell. This will run all the test inside a virtual machine, which is necessary for the tests to pass successfully.
Make sure that all tests pass successfully and the API works correctly.

The ```pytest-vm``` command will also print out the coverage of the tests. To export the report to an XML file, use the following command:

```coverage xml```


Next, use the recommended extension ```ryanluker.vscode-coverage-gutters```, navigate to one of the test files, and click the "watch" button on the bottom panel of VScode.

**Format (linting) code**, we use [black](https://pypi.org/project/black/) formatting, enter
```black .``` to automatically format files, or use the recommended extension.

**And please remember, we have adopted** [**commit naming convention**](https://www.conventionalcommits.org/en/v1.0.0/), follow the link for more information.

Please request a review from at least one of the other maintainers. If you are not sure who to request, request a review from SelfPrivacy/Devs team.

## Helpful links!

**SelfPrivacy Contributor chat :3**

- [**Telegram:** @selfprivacy_dev](https://t.me/selfprivacy_dev)
- [**Matrix:** #dev:selfprivacy.org](https://matrix.to/#/#dev:selfprivacy.org)

**Helpful material to review:**

- [GraphQL Query Language Documentation](https://graphql.org/)
- [Documentation Strawberry - python library for working with GraphQL](https://strawberry.rocks/docs/)
- [Nix Documentation](https://nixos.org/guides/ad-hoc-developer-environments.html)

### Track your time

If you are working on a task, please track your time and add it to the commit message. For example:

```
feat: add new feature

- did some work
- did some more work

fixes #4, spent @1h30m
```

[Timewarrior](https://timewarrior.net/) is a good tool for tracking time.
