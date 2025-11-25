# Environment Setup Guide

This guide explains how to configure environment variables for the data extraction system.

## Required Environment Variables

The system requires the following environment variables to use LLM features:

- **API Key**: `TOKEN_FACTORY_API_KEY` or `LLM_API_KEY`
- **Base URL**: `TOKEN_FACTORY_BASE_URL` or `LLM_BASE_URL`

## Setup Methods

### Method 1: Using .env File (Recommended)

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   TOKEN_FACTORY_API_KEY=your_actual_api_key_here
   TOKEN_FACTORY_BASE_URL=https://tokenfactory.esprit.tn/api
   ```

3. The `.env` file is automatically loaded by `python-dotenv` when the application starts.

**Note**: The `.env` file is in `.gitignore` and will not be committed to version control.

### Method 2: System Environment Variables

#### Windows (PowerShell)
```powershell
$env:TOKEN_FACTORY_API_KEY = "your_api_key_here"
$env:TOKEN_FACTORY_BASE_URL = "https://tokenfactory.esprit.tn/api"
```

#### Windows (Command Prompt)
```cmd
set TOKEN_FACTORY_API_KEY=your_api_key_here
set TOKEN_FACTORY_BASE_URL=https://tokenfactory.esprit.tn/api
```

#### Linux/Mac (Bash)
```bash
export TOKEN_FACTORY_API_KEY="your_api_key_here"
export TOKEN_FACTORY_BASE_URL="https://tokenfactory.esprit.tn/api"
```

### Method 3: Permanent System Environment Variables

#### Windows
1. Open "System Properties" → "Environment Variables"
2. Add new User or System variables:
   - `TOKEN_FACTORY_API_KEY`
   - `TOKEN_FACTORY_BASE_URL`
3. Restart your terminal/IDE for changes to take effect

#### Linux/Mac
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export TOKEN_FACTORY_API_KEY="your_api_key_here"
export TOKEN_FACTORY_BASE_URL="https://tokenfactory.esprit.tn/api"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Verifying Configuration

Run the environment check script:
```bash
python check_env_vars.py
```

This will show which environment variables are set and which are missing.

## Optional Variables

- `LLM_VISION_MODEL`: Vision model for chart analysis (default: `hosted_vllm/llava-1.5-7b-hf`)
- `LLM_MODEL_NAME`: Text model for content analysis (default: `hosted_vllm/Llama-3.1-70B-Instruct`)

## Troubleshooting

### Variables Not Detected

1. **Check if .env file exists**: The file must be in the project root directory
2. **Check file name**: Must be exactly `.env` (not `.env.txt` or `env`)
3. **Restart your IDE/terminal**: Environment variables may need a restart to be detected
4. **Check for typos**: Variable names are case-sensitive
5. **Verify dotenv is installed**: `pip install python-dotenv`

### Test Failures Due to Missing API Keys

If tests fail with "API credentials not found", the system will:
- Skip LLM-dependent tests gracefully
- Continue with non-LLM tests
- Show warnings instead of errors

This is expected behavior when API keys are not configured.

## Security Notes

- **Never commit `.env` files** to version control
- **Never share API keys** in code, documentation, or public repositories
- Use `.env.example` as a template without actual credentials
- Rotate API keys if they are accidentally exposed

