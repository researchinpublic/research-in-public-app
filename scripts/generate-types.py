#!/usr/bin/env python3
"""
Generate TypeScript/Python types from OpenAPI contract.

Usage:
    python scripts/generate-types.py [--lang typescript|python]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# OpenAPI Generator configuration
OPENAPI_GENERATOR_CONFIG = {
    "typescript": {
        "generator": "typescript-axios",
        "output": "src/gen/types/typescript",
        "additional_properties": "npmName=@research-in-public/api-client,withInterfaces=true"
    },
    "python": {
        "generator": "python",
        "output": "src/gen/types/python",
        "additional_properties": "packageName=research_in_public_api,packageVersion=1.0.0"
    }
}


def check_openapi_generator():
    """Check if openapi-generator is installed."""
    try:
        subprocess.run(
            ["openapi-generator", "version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_openapi_generator():
    """Install openapi-generator via npm."""
    print("Installing openapi-generator-cli via npm...")
    try:
        subprocess.run(
            ["npm", "install", "-g", "@openapitools/openapi-generator-cli"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install openapi-generator-cli")
        return False


def generate_types(lang: str, openapi_spec: Path, output_dir: Path):
    """Generate types from OpenAPI spec."""
    config = OPENAPI_GENERATOR_CONFIG[lang]
    
    cmd = [
        "openapi-generator",
        "generate",
        "-i", str(openapi_spec),
        "-g", config["generator"],
        "-o", str(output_dir),
        "--additional-properties", config["additional_properties"]
    ]
    
    print(f"Generating {lang} types from {openapi_spec}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Types generated successfully in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to generate types: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate types from OpenAPI contract"
    )
    parser.add_argument(
        "--lang",
        choices=["typescript", "python"],
        default="typescript",
        help="Language for generated types (default: typescript)"
    )
    parser.add_argument(
        "--openapi",
        type=Path,
        default=Path("contract/openapi.yaml"),
        help="Path to OpenAPI spec (default: contract/openapi.yaml)"
    )
    
    args = parser.parse_args()
    
    # Check if OpenAPI spec exists
    if not args.openapi.exists():
        print(f"Error: OpenAPI spec not found: {args.openapi}")
        sys.exit(1)
    
    # Check if openapi-generator is installed
    if not check_openapi_generator():
        print("openapi-generator not found. Attempting to install...")
        if not install_openapi_generator():
            print("Error: Please install openapi-generator-cli manually:")
            print("  npm install -g @openapitools/openapi-generator-cli")
            sys.exit(1)
    
    # Create output directory
    output_dir = Path(f"src/gen/types/{args.lang}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate types
    if generate_types(args.lang, args.openapi, output_dir):
        print(f"\n✓ Success! Types generated in {output_dir}")
        print(f"\nNext steps:")
        print(f"  1. Review generated types in {output_dir}")
        print(f"  2. Import types in your code:")
        if args.lang == "typescript":
            print(f"     import {{ SessionResponse }} from '@/gen/types/typescript'")
        else:
            print(f"     from research_in_public_api import SessionResponse")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

