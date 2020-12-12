# Xbox-Smartglass-Nano


[![PyPi version](https://pypip.in/version/xbox-smartglass-nano/badge.svg)](https://pypi.python.org/pypi/xbox-smartglass-nano)
[![Docs](https://readthedocs.org/projects/xbox-smartglass-nano-python/badge/?version=latest)](http://xbox-smartglass-nano-python.readthedocs.io/en/latest/?badge=latest)
[![Build status](https://img.shields.io/github/workflow/status/OpenXbox/xbox-smartglass-nano-python/build?label=build)](https://github.com/OpenXbox/xbox-smartglass-nano-python/actions?query=workflow%3Abuild)
[![Discord chat](https://img.shields.io/discord/338946086775554048)](https://openxbox.org/discord)

The gamestreaming part of the smartglass library, codename NANO.

Currently supported version:

* NANO v2

XCloud and new XHome streaming are Nano v3!

For in-depth information, check out the documentation: (https://openxbox.github.io)


## Features

* Stream from your local Xbox-family console (Xbox One OG/S/X, Xbox Series S/X)


## Dependencies

* Python >= 3.7
* xbox-smartglass-core
* pyav (https://mikeboers.github.io/PyAV/installation.html)
* pysdl2 (http://pysdl2.readthedocs.io/en/rel_0_9_4/install.html)


## Install

  pip install xbox-smartglass-nano

## How to use

```text
xbox-nano-client
```

## Known issues

* Video / Audio / Input is not smooth yet
* ChatAudio and Input Feedback not implemented

## Development workflow

Ready to contribute? Here's how to set up `xbox-smartglass-nano-python` for local development.

1. Fork the `xbox-smartglass-nano-python` repo on GitHub.
2. Clone your fork locally

```text
git clone git@github.com:your_name_here/xbox-smartglass-nano-python.git
```

3. Install your local copy into a virtual environment. This is how you set up your fork for local development

```text
python -m venv ~/pyvenv/xbox-smartglass
source ~/pyvenv/xbox-smartglass/bin/activate
cd xbox-smartglass-nano-python
pip install -e .[dev]
```

5. Create a branch for local development::

```text
git checkout -b name-of-your-bugfix-or-feature
```

6. Make your changes.

7. Before pushing the changes to git, please verify they actually work

```text
pytest
```

8. Commit your changes and push your branch to GitHub::

```text
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

9. Submit a pull request through the GitHub website.

### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. Code includes unit-tests.
2. Added code is properly named and documented.
3. On major changes the README is updated.
4. Run tests / linting locally before pushing to remote.


## Credits

This package uses parts of [Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage project template](https://github.com/audreyr/cookiecutter-pypackage)
