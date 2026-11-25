#!/usr/bin/env python3
"""
Environment File Generator for LatMatrix Project
Generates .env file with default values and random secrets.
Users can override defaults through command-line arguments or interactive menu.
"""

import sys
import secrets
import string
import argparse
from pathlib import Path


def generate_random_secret(length=64):
    """Generate a cryptographically secure random secret string."""
    # Use URL-safe base64 characters for compatibility
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_hex_secret(length=32):
    """Generate a hex-encoded secret (64 characters for 32 bytes)."""
    return secrets.token_hex(length)


def collect_keyboard_entropy():
    """
    Collect keyboard entropy from user to enhance randomness.
    Uses standard input() call - user must type at least 20 random characters.
    Returns a string of collected entropy.
    """
    print("\n" + "=" * 60)
    print("KEYBOARD ENTROPY COLLECTION")
    print("=" * 60)
    print("Please type at least 20 random characters.")
    print("The characters you type will be used to enhance randomness.")
    print("Examples: mash keyboard, type random words, etc.")
    print()

    while True:
        input_text = input("Type random characters (min 20 chars): ").strip()

        if len(input_text) >= 20:
            print(f"✓ Collected {len(input_text)} characters of entropy.")

            # Add some system entropy as well
            import time
            import os
            import random

            # Mix with system randomness
            system_entropy = (
                str(time.time()) + str(os.getpid()) + str(random.getrandbits(64))
            )

            # Combine user input with system entropy
            combined = input_text + system_entropy

            # Hash it for consistent length
            import hashlib

            entropy_hash = hashlib.sha256(combined.encode()).hexdigest()

            return entropy_hash
        else:
            print(
                f"✗ Only {len(input_text)} characters. Please type at least 20 "
                f"characters."
            )
            print("Try again or press Ctrl+C to cancel.")


def get_default_values(entropy=None):
    """Return dictionary of default environment values."""
    # Use entropy to seed secrets if provided
    import hashlib
    import time

    if entropy:
        # Create a seed from entropy
        seed = hashlib.sha256(entropy.encode()).hexdigest()
        # Mix with current time
        seed += str(time.time())
        # Use seed to influence secret generation
        seed_hash = hashlib.sha256(seed.encode()).hexdigest()
        # Use first 16 chars of hash as extra randomness
        extra_random = seed_hash[:16]
    else:
        extra_random = ""

    def generate_secret_with_entropy(length=64, extra=""):
        """Generate secret with optional extra entropy."""
        base_secret = generate_random_secret(length - len(extra))
        return extra + base_secret[: length - len(extra)]

    return {
        # Docker Network Configuration
        "DOCKER_NETWORK_SUBNET": "172.20.0.0/16",
        # Streamlit Frontend Configuration
        "STREAMLIT_SERVER_PORT": "8501",
        "STREAMLIT_SERVER_ADDRESS": "0.0.0.0",
        "STREAMLIT_SERVER_ENABLE_CORS": "true",
        "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION": "true",
        "STREAMLIT_SERVER_MAX_UPLOAD_SIZE": "200",
        "STREAMLIT_SERVER_FILE_WATCHER_TYPE": "none",
        "STREAMLIT_SERVER_WEBSOCKET_COMPRESSION_LEVEL": "1",
        "STREAMLIT_SERVER_WEBSOCKET_MAX_MESSAGE_SIZE": "200",
        "STREAMLIT_SERVER_MAX_MESSAGE_SIZE": "200",
        "STREAMLIT_BROWSER_SERVER_ADDRESS": "localhost",
        # Backend API Configuration
        "API_SERVICE_NAME": "api",
        "API_PORT": "8000",
        "API_URL": "http://api:8000",
        # Application Settings
        "SERVICE": "frontend",
        "PORT": "8501",
        # Security (randomly generated secrets with optional entropy)
        "STREAMLIT_COOKIE_SECRET": generate_secret_with_entropy(64, extra_random[:8]),
        "STREAMLIT_XSRF_SECRET": generate_secret_with_entropy(
            64, extra_random[8:16] if len(extra_random) >= 16 else ""
        ),
        # Health Check Configuration
        "HEALTH_CHECK_INTERVAL": "30",
        "HEALTH_CHECK_TIMEOUT": "10",
        "HEALTH_CHECK_RETRIES": "3",
        "HEALTH_CHECK_START_PERIOD": "40",
    }


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate .env file for LatMatrix project"
    )
    parser.add_argument(
        "--output", "-o", default=".env", help="Output file path (default: .env)"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing file without confirmation",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode to customize values",
    )
    parser.add_argument(
        "--show-secrets", action="store_true", help="Show generated secrets in output"
    )
    return parser.parse_args()


def interactive_customization(defaults):
    """Allow user to customize values interactively."""
    print("Interactive Environment Configuration")
    print("=" * 40)
    print("Press Enter to accept default values, or enter new values.")
    print()

    customized = defaults.copy()

    # Group settings for better organization
    groups = {
        "Docker Network": ["DOCKER_NETWORK_SUBNET"],
        "Streamlit Server": [
            "STREAMLIT_SERVER_PORT",
            "STREAMLIT_SERVER_ADDRESS",
            "STREAMLIT_SERVER_MAX_UPLOAD_SIZE",
            "STREAMLIT_BROWSER_SERVER_ADDRESS",
        ],
        "Security": [
            "STREAMLIT_SERVER_ENABLE_CORS",
            "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION",
        ],
        "Backend API": ["API_SERVICE_NAME", "API_PORT", "API_URL"],
        "Health Checks": [
            "HEALTH_CHECK_INTERVAL",
            "HEALTH_CHECK_TIMEOUT",
            "HEALTH_CHECK_RETRIES",
            "HEALTH_CHECK_START_PERIOD",
        ],
    }

    for group_name, keys in groups.items():
        print(f"\n{group_name} Settings:")
        print("-" * 30)
        for key in keys:
            current = customized[key]
            new_value = input(f"{key} [{current}]: ").strip()
            if new_value:
                customized[key] = new_value

    # Ask about regenerating secrets
    print("\nSecurity Secrets:")
    print("-" * 30)
    regenerate = input("Regenerate random secrets? (y/N): ").strip().lower()
    if regenerate == "y":
        customized["STREAMLIT_COOKIE_SECRET"] = generate_random_secret(64)
        customized["STREAMLIT_XSRF_SECRET"] = generate_random_secret(64)
        print("Secrets regenerated.")

    return customized


def write_env_file(values, output_path, show_secrets=False):
    """Write environment variables to file."""
    env_content = "# Environment Configuration for LatMatrix Project\n"
    env_content += "# Generated by generate-env.py\n"
    env_content += "#\n"
    env_content += "# WARNING: Keep secrets secure! Do not commit to version control.\n"
    env_content += "\n"

    # Group variables for better organization
    groups = [
        ("# Docker Network Configuration", ["DOCKER_NETWORK_SUBNET"]),
        (
            "# Streamlit Frontend Configuration",
            [
                "STREAMLIT_SERVER_PORT",
                "STREAMLIT_SERVER_ADDRESS",
                "STREAMLIT_SERVER_ENABLE_CORS",
                "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION",
                "STREAMLIT_SERVER_MAX_UPLOAD_SIZE",
                "STREAMLIT_SERVER_FILE_WATCHER_TYPE",
                "STREAMLIT_SERVER_WEBSOCKET_COMPRESSION_LEVEL",
                "STREAMLIT_SERVER_WEBSOCKET_MAX_MESSAGE_SIZE",
                "STREAMLIT_SERVER_MAX_MESSAGE_SIZE",
                "STREAMLIT_BROWSER_SERVER_ADDRESS",
            ],
        ),
        ("# Backend API Configuration", ["API_SERVICE_NAME", "API_PORT", "API_URL"]),
        ("# Application Settings", ["SERVICE", "PORT"]),
        (
            "# Security (randomly generated - keep secret!)",
            ["STREAMLIT_COOKIE_SECRET", "STREAMLIT_XSRF_SECRET"],
        ),
        (
            "# Health Check Configuration",
            [
                "HEALTH_CHECK_INTERVAL",
                "HEALTH_CHECK_TIMEOUT",
                "HEALTH_CHECK_RETRIES",
                "HEALTH_CHECK_START_PERIOD",
            ],
        ),
    ]

    for group_header, keys in groups:
        env_content += f"\n{group_header}\n"
        for key in keys:
            value = values[key]
            env_content += f"{key}={value}\n"

    # Write to file
    with open(output_path, "w") as f:
        f.write(env_content)

    return env_content


def main():
    """Main function."""
    args = parse_arguments()

    # Check if file exists
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        response = (
            input(f"File '{output_path}' already exists. Overwrite? (y/N): ")
            .strip()
            .lower()
        )
        if response != "y":
            print("Operation cancelled.")
            return 1

    # Collect entropy for enhanced randomness (unless in non-interactive mode)
    entropy = None
    if not args.interactive:
        print("Collecting entropy for enhanced randomness...")
        try:
            entropy = collect_keyboard_entropy()
            print("Entropy collected successfully.")
        except Exception as e:
            print(f"Warning: Could not collect entropy: {e}")
            print("Using system randomness only.")

    # Get values
    defaults = get_default_values(entropy=entropy)

    if args.interactive:
        values = interactive_customization(defaults)
    else:
        values = defaults

    # Write file
    env_content = write_env_file(values, output_path, args.show_secrets)

    # Show summary
    print(f"\nEnvironment file generated: {output_path}")
    print(f"File size: {output_path.stat().st_size} bytes")

    if args.show_secrets:
        print("\nGenerated content:")
        print("-" * 40)
        print(env_content)
    else:
        print("\nSecrets are hidden. Use --show-secrets to view them.")

    # Show important notes
    print("\n" + "=" * 60)
    print("IMPORTANT NOTES:")
    print("1. Keep the .env file secure and do not commit it to version control")
    print("2. Add '.env' to your .gitignore file if not already done")
    print("3. Regenerate secrets periodically for security")
    print("4. Update docker-compose.yml if you change network settings")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
