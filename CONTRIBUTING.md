## Getting Started / Setting Up Development Environment

To run this code, you'll need to have Python 3.11, 3.12 or 3.13 installed on your machine. You'll also need to
install the required packages by running the following commands from inside the project folder:

```shell
pip install -U pip uv
```

```shell
uv venv
```

```shell
source .venv/bin/activate # Linux or macOS
.venv\Scripts\activate # Windows
```

```shell
uv pip install -e .[dev]
```

```shell
prek install
```

## Code Submissions

### Tests

Pytest is used to simplify testing and avoid committing broken code. Before committing, please run `pytest` in the
project folder and resolve any errors.

### Dependencies

If you add or modify any dependencies, be sure to list them in pyproject.toml.
The optional dependency group [dev] is used for dependencies used by developers working on this codebase.
The optional dependency group [github-actions] is used for dependencies used when testing or executing CI actions.

### Style

If your text editor doesn't support [.editorconfig](https://editorconfig.org/), please reference
the [.editorconfig file](.editorconfig) for some basic formatting norms.
Regardless, `ruff format .` should be run to standardize formatting before attempting to commit.
