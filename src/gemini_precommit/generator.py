"""Pre-commit hook generator for the Gemini Pre-commit Hook Generator.

This module generates pre-commit hook configurations based on codebase analysis
and Gemini API responses.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from gemini_precommit.analyzer import analyze_codebase
from gemini_precommit.gemini_client import generate_precommit_config


class PrecommitGenerator:
    """Generates pre-commit hook configurations."""

    def __init__(
        self, repo_path: str = ".", api_key: Optional[str] = None, non_interactive: bool = False
    ) -> None:
        """Initialize the generator with the repository path.

        Args:
            repo_path: Path to the repository root. Defaults to current directory.
            api_key: Google Gemini API key. If not provided, will try to load from
                environment variable GOOGLE_GEMINI_API_KEY.
            non_interactive: Whether to run in non-interactive mode. Defaults to False.
        """
        self.repo_path = Path(repo_path).resolve()
        self.api_key = api_key
        self.non_interactive = non_interactive
        self.config_path = self.repo_path / ".pre-commit-config.yaml"
        self.analysis_results: Dict[str, Any] = {}
        self.generated_config: Dict[str, Any] = {}

    def generate(self) -> Dict[str, Any]:
        """Generate pre-commit hooks for the repository.

        Returns:
            A dictionary containing the generated pre-commit configuration.
        """
        print("Analyzing codebase...")
        self.analysis_results = analyze_codebase(str(self.repo_path))

        print("Generating pre-commit configuration...")
        self.generated_config = generate_precommit_config(self.analysis_results, self.api_key)

        return self.generated_config

    def apply_config(self, install: bool = False) -> bool:
        """Apply the generated configuration to the repository.

        Args:
            install: Whether to install the hooks after applying the configuration.

        Returns:
            True if the configuration was applied successfully, False otherwise.
        """
        if not self.generated_config:
            print("No configuration generated. Run generate() first.")
            return False

        yaml_content = self.generated_config.get("yaml_content", "")
        if not yaml_content:
            print("Generated configuration is empty.")
            return False

        # If the file exists and we're in interactive mode, ask for confirmation
        if self.config_path.exists() and not self.non_interactive:
            print(f"\nExisting configuration found at {self.config_path}")
            print("\nGenerated configuration:")
            print("-" * 80)
            print(yaml_content)
            print("-" * 80)
            
            response = input("\nDo you want to replace the existing configuration? (y/n): ")
            if response.lower() != "y":
                print("Configuration not applied.")
                return False

        # Write the configuration to the file
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            print(f"Configuration written to {self.config_path}")
        except Exception as e:
            print(f"Failed to write configuration: {str(e)}")
            return False

        # Install the hooks if requested
        if install:
            return self._install_hooks()

        return True

    def _install_hooks(self) -> bool:
        """Install the pre-commit hooks.

        Returns:
            True if the hooks were installed successfully, False otherwise.
        """
        try:
            print("Installing pre-commit hooks...")
            result = subprocess.run(
                ["pre-commit", "install"],
                cwd=str(self.repo_path),
                check=True,
                capture_output=True,
                text=True,
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install hooks: {e.stderr}")
            return False
        except Exception as e:
            print(f"Failed to install hooks: {str(e)}")
            return False


def generate_hooks(
    repo_path: str = ".",
    api_key: Optional[str] = None,
    non_interactive: bool = False,
    install: bool = False,
) -> Dict[str, Any]:
    """Generate pre-commit hooks for the repository.

    Args:
        repo_path: Path to the repository root. Defaults to current directory.
        api_key: Google Gemini API key. If not provided, will try to load from
            environment variable GOOGLE_GEMINI_API_KEY.
        non_interactive: Whether to run in non-interactive mode. Defaults to False.
        install: Whether to install the hooks after generating. Defaults to False.

    Returns:
        A dictionary containing the generated pre-commit configuration.
    """
    generator = PrecommitGenerator(repo_path, api_key, non_interactive)
    config = generator.generate()
    
    if generator.apply_config(install):
        return {
            "success": True,
            "config": config,
            "config_path": str(generator.config_path),
        }
    else:
        return {
            "success": False,
            "config": config,
            "error": "Failed to apply configuration",
        }
