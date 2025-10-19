# Clean Project Structure

## Core Files
- `main.py` - Main Gradio application (entry point)
- `simple-lms-agent.py` - Simple demo version
- `file_processor_app.py` - File processing Gradio interface
- `simple_demo.py` - Basic demo for testing

## Configuration
- `.env` - Your AWS credentials and config
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `SETUP_INSTRUCTIONS.md` - How to set up the project

## Source Code
- `src/` - Main application code
  - `src/shared/` - Shared utilities and config
  - `src/file_processor/` - File processing logic
  - `src/auth_service/` - Authentication service

## Testing
- `test_*.py` - Various test files for different components
- `tests/` - Organized test directory

## Documentation
- `README.md` - Project overview
- `.kiro/` - Kiro AI assistant configuration and specs

## What Was Removed
- Old infrastructure files (Lambda, API Gateway configs)
- Duplicate test files
- PowerShell deployment scripts
- Old completion summaries
- Unused frontend HTML files
- Debug and temporary files

## Next Steps
Focus on these core files:
1. `main.py` - Your main Gradio app
2. `src/` directory - Your core logic
3. Test files - Keep the ones that work