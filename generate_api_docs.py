#!/usr/bin/env python3
"""
Generate comprehensive API documentation
Creates OpenAPI specs, API reference, testing guides, and Postman collections
"""

import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.api_documentation import APIDocumentationGenerator
from shared.openapi_spec import save_openapi_spec
from shared.logging_config import setup_logging


def main():
    """Generate all API documentation"""
    
    parser = argparse.ArgumentParser(description="Generate comprehensive API documentation")
    parser.add_argument("--output-dir", default="docs", help="Output directory for documentation")
    parser.add_argument("--format", choices=["all", "openapi", "reference", "testing", "postman"], 
                       default="all", help="Documentation format to generate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level="DEBUG" if args.verbose else "INFO")
    
    print("LMS API Documentation Generator")
    print("=" * 50)
    print(f"Output directory: {args.output_dir}")
    print(f"Format: {args.format}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Initialize generator
    generator = APIDocumentationGenerator(args.output_dir)
    
    generated_files = {}
    
    try:
        if args.format in ["all", "openapi"]:
            print("Generating OpenAPI specifications...")
            openapi_files = generator.generate_openapi_docs()
            generated_files.update(openapi_files)
            print(f"  ✓ OpenAPI JSON: {openapi_files.get('json', 'N/A')}")
            print(f"  ✓ OpenAPI YAML: {openapi_files.get('yaml', 'N/A')}")
        
        if args.format in ["all", "reference"]:
            print("\nGenerating API reference documentation...")
            reference_file = generator.generate_api_reference()
            generated_files["api_reference"] = reference_file
            print(f"  ✓ API Reference: {reference_file}")
        
        if args.format in ["all", "testing"]:
            print("\nGenerating testing guide...")
            testing_file = generator.generate_testing_guide()
            generated_files["testing_guide"] = testing_file
            print(f"  ✓ Testing Guide: {testing_file}")
        
        if args.format in ["all", "postman"]:
            print("\nGenerating Postman collection...")
            postman_file = generator.generate_postman_collection()
            generated_files["postman_collection"] = postman_file
            print(f"  ✓ Postman Collection: {postman_file}")
        
        print("\n" + "=" * 50)
        print("Documentation generation completed successfully!")
        print("\nGenerated files:")
        for doc_type, file_path in generated_files.items():
            if file_path:
                print(f"  {doc_type}: {file_path}")
        
        print(f"\nAll files saved to: {args.output_dir}/")
        
        # Generate index file
        generate_index_file(args.output_dir, generated_files)
        
    except Exception as e:
        print(f"\nERROR: Failed to generate documentation: {str(e)}")
        sys.exit(1)


def generate_index_file(output_dir: str, generated_files: dict):
    """Generate an index file for all documentation"""
    
    index_content = []
    
    # Header
    index_content.append("# LMS API Documentation")
    index_content.append("")
    index_content.append("This directory contains comprehensive documentation for the LMS API.")
    index_content.append("")
    index_content.append(f"Generated on: {datetime.utcnow().isoformat()}")
    index_content.append("")
    
    # Files section
    index_content.append("## Available Documentation")
    index_content.append("")
    
    doc_descriptions = {
        "json": ("OpenAPI Specification (JSON)", "Machine-readable API specification in JSON format"),
        "yaml": ("OpenAPI Specification (YAML)", "Human-readable API specification in YAML format"),
        "api_reference": ("API Reference Guide", "Comprehensive API reference with examples"),
        "testing_guide": ("Testing Guide", "Instructions for testing the API"),
        "postman_collection": ("Postman Collection", "Postman collection for API testing")
    }
    
    for doc_type, file_path in generated_files.items():
        if file_path and doc_type in doc_descriptions:
            title, description = doc_descriptions[doc_type]
            filename = os.path.basename(file_path)
            index_content.append(f"### {title}")
            index_content.append(f"**File:** `{filename}`")
            index_content.append(f"**Description:** {description}")
            index_content.append("")
    
    # Usage section
    index_content.append("## Quick Start")
    index_content.append("")
    index_content.append("1. **API Reference**: Start with `api_reference.md` for comprehensive API documentation")
    index_content.append("2. **Testing**: Use `testing_guide.md` for testing instructions")
    index_content.append("3. **Postman**: Import `postman_collection.json` into Postman for interactive testing")
    index_content.append("4. **OpenAPI**: Use `openapi.json` or `openapi.yaml` with API tools like Swagger UI")
    index_content.append("")
    
    # Tools section
    index_content.append("## Recommended Tools")
    index_content.append("")
    index_content.append("- **Swagger UI**: Visualize and interact with the API using the OpenAPI specification")
    index_content.append("- **Postman**: Test API endpoints using the provided collection")
    index_content.append("- **curl**: Command-line testing using examples from the testing guide")
    index_content.append("- **Insomnia**: Alternative API client that supports OpenAPI imports")
    index_content.append("")
    
    # Support section
    index_content.append("## Support")
    index_content.append("")
    index_content.append("For questions or issues with the API:")
    index_content.append("- Check the testing guide for troubleshooting tips")
    index_content.append("- Review error codes in the API reference")
    index_content.append("- Test with the health endpoint: `GET /health`")
    index_content.append("")
    
    # Save index file
    index_path = os.path.join(output_dir, "README.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(index_content))
    
    print(f"  ✓ Documentation Index: {index_path}")


if __name__ == "__main__":
    main()