<!-- omit in toc -->
# Contributing to TTS-Wrapper

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution.

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
>
> - Star the project
> - If you use TTS-Wrapper, refer this project in your project's readme

<!-- omit in toc -->
## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
  - [Setup with VS Code and DevContainer](#setup-with-vs-code-and-devcontainer)
- [Styleguides](#styleguides)
  - [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://github.com/mediatechlab/tts-wrapper).

Before you ask a question, it is best to search for existing [Issues](https://github.com/mediatechlab/tts-wrapper/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/mediatechlab/tts-wrapper/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (nodejs, npm, etc), depending on what seems relevant.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
>
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://github.com/mediatechlab/tts-wrapper). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/mediatechlab/tts-wrapperissues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Python version
  - Can you reliably reproduce the issue? And can you also reproduce it with older versions?

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to <giuliobottari@gmail.com>.
<!-- You may add a PGP key to allow the messages to be sent encrypted as well. -->

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/mediatechlab/tts-wrapper/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for TTS-Wrapper, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://github.com/mediatechlab/tts-wrapper) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/mediatechlab/tts-wrapper/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/mediatechlab/tts-wrapper/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- **Explain why this enhancement would be useful** to most TTS-Wrapper users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

### Your First Code Contribution

After cloning the project, install the dependencies with Poetry or Pip.

```bash
poetry install
```

or

```bash
pip install -r requirements.txt -r requirements.dev.txt
```

Remember that most TTS services require credentials to work and thus you must bring your own to the project. To make testing easier, create a file named `.secrets/.env` like the one below:

```bash
POLLY_REGION=
POLLY_AWS_KEY_ID=
POLLY_AWS_ACCESS_KEY=

MICROSOFT_TOKEN=
MICROSOFT_REGION=

GOOGLE_SA_PATH=.secrets/google.json
GOOGLE_SA_FILE_B64=

WATSON_API_KEY=
WATSON_REGION=
WATSON_INSTANCE_ID=

ELEVENLABS_API_KEY=
WITAI_TOKEN=
PLAYHT_API_KEY=
PLAYHT_USER_ID=
UPLIFTAI_KEY=
MODELSLAB_API_KEY=
```

For PicoTTS you also need to install the package for your system. Check the documentation for how to do that.

<!-- omit in toc -->
### Testing

There are two kinds of tests: offline tests and online tests. The former will mock server responses while the latter will actually use the credentials to perform requests. To perform them, use the Makefile.

Offline:

```bash
make tests
```

Both:

```bash
make all_tests
```

You don't actually need to run tests for all services if you don't want to. Since they are divided by folder, you can tell `pytest` to run all tests from a single engine:

```Python
source .secrets/.env && \
  export POLLY_REGION POLLY_AWS_KEY_ID POLLY_AWS_ACCESS_KEY && \
  pytest tests/engines/test_polly.py
```

### Setup with VS Code and [DevContainer](https://code.visualstudio.com/docs/remote/containers)

- Clone the repository
- Install the [Remote Container](https://github.com/microsoft/vscode-dev-containers) extension in Visual Code
- Click on the ![devcontainer-button](https://user-images.githubusercontent.com/2154092/179066283-efc659da-02ab-4fb5-86ca-763557f56f0d.png) icon in the bottom left corner and select `Reopen in Container` or look for `Reopen in Container` in the command panel (Ctrl+Shift+P)
- Wait for the containers to build and install all the dependencies using Poetry
- Open a terminal from VS Code and run `make tests` to check everything went right


<!-- omit in toc -->
## Attribution

This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
