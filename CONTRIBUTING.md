# Contributing to the Moorcheh Python SDK
First off, thank you for considering contributing to the Moorcheh Python SDK! We welcome contributions from the community to help improve the SDK.
This document provides guidelines for contributing to this project.
# How Can I Contribute?
* **Reporting Bugs:**   If you find a bug, please open an issue on GitHub. Include a clear description, steps to reproduce the bug, the expected behavior, and the actual behavior. Include relevant details like your Python version, SDK version, and operating system.
* **Suggesting Enhancements:** Have an idea for a new feature or an improvement to an existing one? Open an issue on GitHub. Clearly describe the proposed enhancement and why it would be beneficial.
* **Code Contributions:** If you want to fix a bug or implement a feature, please follow the process outlined below.
# Getting Started (Development Setup)
1. Fork the Repository: Create your own fork of the moorcheh-python-sdk [https://github.com/moorcheh-ai/moorcheh-python-sdk] repository on GitHub.
2. Clone Your Fork: Clone your forked repository to your local machine.
```bash
git clone https://github.com/YOUR_USERNAME/moorcheh-python-sdk.git
cd moorcheh-python-sdk
```
3. Set Up Environment: Follow the "Development Setup" instructions in the README.md file, which uses Poetry to create a virtual environment and install dependencies (including development tools).
```bash
poetry install --with dev
```
4. Create a Branch: Create a new branch for your changes. Use a descriptive name (e.g., fix/issue-123, feat/add-graph-endpoint).
```bash 
git checkout -b your-branch-name
```
# Making Changes
* **Code Style:**  Please follow standard Python coding conventions (PEP 8). We recommend using tools like black for formatting and ruff or flake8 for linting (consider adding these to dev-dependencies in pyproject.toml if you haven't already).
* **Testing:**

1. Unit Tests: Write new tests for any new features you add.
2. Integration Tests: Add or update tests for any bugs you fix to prevent regressions.
3.  Ensure all tests pass before submitting a pull request. Run tests using:
```bash
poetry run pytest tests/
```
* **Documentation:** Update docstrings, examples, and the README.md as necessary to reflect your changes.
* **Commit Messages:** Write clear and concise commit messages explaining the "what" and "why" of your changes.
# Submitting Changes (Pull Requests)
1. Commit and Push: Commit your changes to your branch and push them to your fork on GitHub.
```bash
git add .
git commit -m "Your descriptive commit message"
git push origin your-branch-name
```
2. Open a Pull Request: Go to the original moorcheh-python-sdk repository on GitHub and open a pull request from your branch to the main branch (or the appropriate target branch).
3. Describe Your PR: Provide a clear description of the changes in your pull request. Link to any relevant issues (e.g., "Fixes #123").
4. Review Process: Your pull request will be reviewed by the maintainers. Be prepared to discuss your changes and make adjustments based on feedback. Once approved, your changes will be merged.
# Code of Conduct
Please note that this project is released with a Contributor Code of Conduct. By participating in this project, you agree to abide by its terms. (Optional: Consider adding a CODE_OF_CONDUCT.md file, perhaps based on the Contributor Covenant: https://www.contributor-covenant.org/)
Thank you for your contributions!
