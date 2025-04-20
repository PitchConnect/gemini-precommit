"""Client for interacting with Google's Gemini API.

This module handles communication with the Gemini API for generating
pre-commit hook configurations based on codebase analysis.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from gemini_precommit.logging import get_logger


class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the Gemini client.

        Args:
            api_key: Google Gemini API key. If not provided, will try to load from
                environment variable GOOGLE_GEMINI_API_KEY.
        """
        self.logger = get_logger("gemini_client")
        self.logger.info("Initializing Gemini client")

        # Load environment variables from .env file
        self.logger.debug("Loading environment variables from .env file")
        load_dotenv()

        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not self.api_key:
            self.logger.error("Gemini API key not provided")
            raise ValueError(
                "Gemini API key not provided. Set GOOGLE_GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.logger.debug("API key found")

        # Configure the Gemini API
        self.logger.debug("Configuring Gemini API")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.logger.info("Gemini client initialized successfully")

    def generate_precommit_config(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a pre-commit configuration based on codebase analysis.

        Args:
            analysis_results: Results from the codebase analysis.

        Returns:
            A dictionary containing the generated pre-commit configuration.
        """
        self.logger.info("Generating pre-commit configuration based on analysis results")

        self.logger.debug("Creating prompt for Gemini API")
        prompt = self._create_prompt(analysis_results)

        self.logger.debug("Calling Gemini API")
        start_time = time.time()
        response = self._call_gemini_api(prompt)
        elapsed_time = time.time() - start_time
        self.logger.debug(f"Gemini API call completed in {elapsed_time:.2f} seconds")

        self.logger.debug("Parsing API response")
        result = self._parse_response(response)
        self.logger.info("Pre-commit configuration generated successfully")

        return result

    def _create_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Create a prompt for the Gemini API based on analysis results.

        Args:
            analysis_results: Results from the codebase analysis.

        Returns:
            A string prompt for the Gemini API.
        """
        file_extensions = analysis_results.get("file_extensions", [])
        languages = analysis_results.get("languages", [])
        python_dependencies = analysis_results.get("python_dependencies", [])
        existing_configs = analysis_results.get("existing_configs", {})
        ci_workflows = analysis_results.get("ci_workflows", [])

        prompt = f"""
        You are an expert in software development best practices and tooling. Your task is to generate
        a comprehensive pre-commit hook configuration for a codebase with the following characteristics:

        File extensions: {', '.join(file_extensions)}
        Programming languages: {', '.join(languages)}
        Python dependencies: {', '.join(python_dependencies[:20])}{"..." if len(python_dependencies) > 20 else ""}
        Existing configurations: {json.dumps(existing_configs)}
        CI/CD workflows: {', '.join(ci_workflows)}

        Please generate a .pre-commit-config.yaml file that:
        1. Includes appropriate hooks for the detected languages
        2. Aligns with existing configurations
        3. Complements the CI/CD workflows
        4. Follows best practices for each language
        5. Includes appropriate hooks for security, formatting, linting, and testing
        6. Includes custom hooks for checking documentation freshness if appropriate

        Return ONLY the YAML content for the .pre-commit-config.yaml file, without any explanations or markdown formatting.
        The output should be valid YAML that can be directly saved to a .pre-commit-config.yaml file.
        """

        return prompt

    def _call_gemini_api(self, prompt: str) -> str:
        """Call the Gemini API with the given prompt.

        Args:
            prompt: The prompt to send to the Gemini API.

        Returns:
            The response from the Gemini API.

        Raises:
            Exception: If the API call fails.
        """
        self.logger.trace(f"Sending prompt to Gemini API: {prompt[:100]}...")

        try:
            self.logger.debug("Making API request to Gemini")
            response = self.model.generate_content(prompt)
            self.logger.debug("Received response from Gemini API")
            self.logger.trace(f"Raw response: {response.text[:100]}...")
            return response.text
        except Exception as e:
            error_msg = f"Failed to call Gemini API: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(f"Full error details: {e}", exc_info=True)
            raise Exception(error_msg) from e

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the response from the Gemini API.

        Args:
            response: The response from the Gemini API.

        Returns:
            A dictionary containing the parsed pre-commit configuration.

        Raises:
            ValueError: If the response cannot be parsed.
        """
        self.logger.debug("Parsing Gemini API response")
        try:
            # Clean up the response to extract just the YAML content
            yaml_content = response.strip()
            self.logger.trace(f"Initial response length: {len(yaml_content)} characters")

            # If the response is wrapped in code blocks, extract just the content
            if yaml_content.startswith("```yaml"):
                self.logger.debug("Detected ```yaml code block, extracting content")
                yaml_content = yaml_content.split("```yaml", 1)[1]
            if yaml_content.startswith("```"):
                self.logger.debug("Detected ``` code block, extracting content")
                yaml_content = yaml_content.split("```", 1)[1]
            if yaml_content.endswith("```"):
                self.logger.debug("Detected trailing ``` code block, removing it")
                yaml_content = yaml_content.rsplit("```", 1)[0]

            yaml_content = yaml_content.strip()
            self.logger.debug(f"Extracted YAML content length: {len(yaml_content)} characters")
            self.logger.trace(f"YAML content starts with: {yaml_content[:50]}...")

            result = {
                "yaml_content": yaml_content,
                "raw_response": response
            }
            self.logger.debug("Successfully parsed Gemini API response")
            return result
        except Exception as e:
            error_msg = f"Failed to parse Gemini API response: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(f"Full error details: {e}", exc_info=True)
            raise ValueError(error_msg) from e


def generate_precommit_config(analysis_results: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate a pre-commit configuration based on codebase analysis.

    Args:
        analysis_results: Results from the codebase analysis.
        api_key: Google Gemini API key. If not provided, will try to load from
            environment variable GOOGLE_GEMINI_API_KEY.

    Returns:
        A dictionary containing the generated pre-commit configuration.
    """
    client = GeminiClient(api_key)
    return client.generate_precommit_config(analysis_results)
