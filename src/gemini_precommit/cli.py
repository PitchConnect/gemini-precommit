"""Command-line interface for the Gemini Pre-commit Hook Generator."""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from gemini_precommit.generator import generate_hooks
from gemini_precommit.utils import get_git_root, is_git_repository, is_pre_commit_installed, install_pre_commit


@click.group()
@click.version_option()
def cli() -> None:
    """Gemini Pre-commit Hook Generator.

    A tool that uses Google's Gemini LLM to analyze your codebase and generate
    customized pre-commit hooks based on your project's specific needs.
    """
    pass


@cli.command()
@click.option(
    "--repo-path",
    "-p",
    default=".",
    help="Path to the repository root. Defaults to current directory.",
)
@click.option(
    "--api-key",
    "-k",
    help="Google Gemini API key. If not provided, will try to load from environment variable GOOGLE_GEMINI_API_KEY.",
)
@click.option(
    "--non-interactive",
    "-n",
    is_flag=True,
    help="Run in non-interactive mode. Will not prompt for confirmation.",
)
@click.option(
    "--install",
    "-i",
    is_flag=True,
    help="Install the hooks after generating.",
)
def generate(
    repo_path: str = ".",
    api_key: Optional[str] = None,
    non_interactive: bool = False,
    install: bool = False,
) -> None:
    """Generate pre-commit hooks for the repository."""
    # Check if the path is a git repository
    if not is_git_repository(repo_path):
        click.echo(f"Error: {repo_path} is not a git repository.")
        sys.exit(1)

    # Get the repository root
    git_root = get_git_root(repo_path)
    if not git_root:
        click.echo(f"Error: Could not determine git repository root from {repo_path}.")
        sys.exit(1)

    # Check if pre-commit is installed
    if install and not is_pre_commit_installed():
        click.echo("pre-commit is not installed. Installing...")
        if not install_pre_commit():
            click.echo("Error: Failed to install pre-commit.")
            sys.exit(1)

    # Generate the hooks
    click.echo(f"Generating pre-commit hooks for {git_root}...")
    result = generate_hooks(git_root, api_key, non_interactive, install)

    if result["success"]:
        click.echo(f"Successfully generated pre-commit hooks at {result['config_path']}.")
        if install:
            click.echo("Hooks installed successfully.")
    else:
        click.echo(f"Error: {result.get('error', 'Unknown error')}.")
        sys.exit(1)


@cli.command()
@click.option(
    "--repo-path",
    "-p",
    default=".",
    help="Path to the repository root. Defaults to current directory.",
)
def check_docs(repo_path: str = ".") -> None:
    """Check if documentation files are up-to-date."""
    from gemini_precommit.utils import check_doc_freshness

    # Check if the path is a git repository
    if not is_git_repository(repo_path):
        click.echo(f"Error: {repo_path} is not a git repository.")
        sys.exit(1)

    # Get the repository root
    git_root = get_git_root(repo_path)
    if not git_root:
        click.echo(f"Error: Could not determine git repository root from {repo_path}.")
        sys.exit(1)

    # Check documentation freshness
    outdated_docs = check_doc_freshness(git_root)
    if outdated_docs:
        click.echo("The following documentation files may be outdated:")
        for doc in outdated_docs:
            click.echo(f"  - {doc}")
        sys.exit(1)
    else:
        click.echo("All documentation files are up-to-date.")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
