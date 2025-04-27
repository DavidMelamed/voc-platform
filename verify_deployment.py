#!/usr/bin/env python3
'''
Deployment Verification Script

Checks if all services and dependencies are properly configured for deployment.
'''

import os
import sys
import json
import requests
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Any

# Color constants for terminal output
COLORS = {
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'RESET': '\033[0m',
    'BOLD': '\033[1m'
}

def success(message: str) -> None:
    print(f"{COLORS['GREEN']}✓ {message}{COLORS['RESET']}")

def warning(message: str) -> None:
    print(f"{COLORS['YELLOW']}⚠ {message}{COLORS['RESET']}")

def error(message: str) -> None:
    print(f"{COLORS['RED']}✗ {message}{COLORS['RESET']}")
    
def section(title: str) -> None:
    print(f"\n{COLORS['BOLD']}=== {title} ==={COLORS['RESET']}")

def check_env_file(env_file: str = '.env.prod') -> Dict[str, List[str]]:
    '''
    Checks if all necessary environment variables are set in the specified env file.
    '''
    section(f"Checking Environment File ({env_file})")
    
    env_path = Path(env_file)
    if not env_path.exists():
        error(f"Environment file {env_file} not found!")
        return {'missing': [], 'empty': []}
    
    # Load environment variables from the file
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    # Required environment variables by category
    required_vars = {
        'Tenant': ['TENANT_ID', 'TENANT_NAME'],
        'Astra DB': ['ASTRA_DB_ID', 'ASTRA_DB_REGION', 'ASTRA_TOKEN', 'ASTRA_API_ENDPOINT', 'ASTRA_KEYSPACE'],
        'Astra Streaming': ['ASTRA_STREAMING_TENANT', 'ASTRA_STREAMING_NAMESPACE', 'ASTRA_STREAMING_BROKER_URL', 'ASTRA_STREAMING_TOKEN'],
        'OpenAI': ['OPENAI_API_KEY'],
        'DataForSEO': ['DATAFORSEO_USERNAME', 'DATAFORSEO_PASSWORD'],
        'Apify': ['APIFY_API_TOKEN'],
        'Phantombuster': ['PHANTOMBUSTER_API_KEY'],
        'Langfuse': ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_PROJECT_ID', 'LANGFUSE_ORG_ID']
    }
    
    missing_vars = []
    empty_vars = []
    
    # Check for each required variable
    for category, vars_list in required_vars.items():
        print(f"Checking {category} Configuration:")
        for var_name in vars_list:
            if var_name not in env_vars:
                error(f"  {var_name} is missing")
                missing_vars.append(var_name)
            elif not env_vars[var_name] or env_vars[var_name].startswith('#'):
                warning(f"  {var_name} is empty or commented out")
                empty_vars.append(var_name)
            else:
                # Mask sensitive values when displaying
                masked_value = env_vars[var_name]
                if 'KEY' in var_name or 'TOKEN' in var_name or 'PASSWORD' in var_name:
                    if len(masked_value) > 8:
                        masked_value = f"{masked_value[:4]}...{masked_value[-4:]}"
                    else:
                        masked_value = "*" * len(masked_value)
                success(f"  {var_name} = {masked_value}")
    
    if not missing_vars and not empty_vars:
        success(f"All required environment variables are set in {env_file}")
    
    return {'missing': missing_vars, 'empty': empty_vars}

def check_docker_files() -> bool:
    '''
    Checks if Dockerfile and docker-compose.yml exist and are properly configured.
    '''
    section("Checking Docker Configuration")
    
    docker_compose_path = Path('docker-compose.yml')
    if not docker_compose_path.exists():
        error("docker-compose.yml not found!")
        return False
    
    success("docker-compose.yml exists")
    
    # Check for Dockerfiles in each service directory
    services_with_dockerfile = []
    services_without_dockerfile = []
    
    with open(docker_compose_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'build:' in line and i+1 < len(lines) and 'context:' in lines[i+1]:
                context_line = lines[i+1].strip()
                if 'context:' in context_line:
                    context_path = context_line.split('context:', 1)[1].strip()
                dockerfile_path = Path(context_path) / 'Dockerfile'
                
                if dockerfile_path.exists():
                    services_with_dockerfile.append(context_path)
                else:
                    services_without_dockerfile.append(context_path)
    
    for service in services_with_dockerfile:
        success(f"Dockerfile found for {service}")
        
    for service in services_without_dockerfile:
        error(f"Dockerfile not found for {service}")
    
    return len(services_without_dockerfile) == 0

def check_gitignore() -> bool:
    '''
    Checks if .gitignore exists and includes common sensitive files.
    '''
    section("Checking .gitignore Configuration")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        error(".gitignore not found!")
        return False
    
    success(".gitignore exists")
    
    # Check for important entries
    required_entries = [
        '.env', '.env.*', '*.pem', '*.key', 
        'node_modules/', 'venv/', '__pycache__/', 
        '.terraform', '*.tfstate'
    ]
    
    missing_entries = []
    with open(gitignore_path, 'r') as f:
        content = f.read()
        for entry in required_entries:
            if entry not in content:
                missing_entries.append(entry)
    
    if missing_entries:
        for entry in missing_entries:
            warning(f"Missing entry in .gitignore: {entry}")
        return False
    else:
        success("All important entries found in .gitignore")
        return True

def check_terraform_config() -> bool:
    '''
    Checks if Terraform configuration is present and valid.
    '''
    section("Checking Terraform Configuration")
    
    terraform_dir = Path('infrastructure/terraform')
    if not terraform_dir.exists():
        error("Terraform directory not found!")
        return False
    
    success("Terraform directory exists")
    
    # Check for required Terraform files
    required_files = ['main.tf', 'variables.tf']
    missing_files = []
    
    for file in required_files:
        if not (terraform_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        for file in missing_files:
            error(f"Missing Terraform file: {file}")
        return False
    else:
        success("All required Terraform files exist")
    
    # Check for tfvars example file
    tfvars_example = terraform_dir / 'tenant.tfvars.example'
    if not tfvars_example.exists():
        warning("tenant.tfvars.example not found")
    else:
        success("tenant.tfvars.example exists")
        
        # Check for production tfvars file
        prod_tfvars = terraform_dir / 'tenant-prod.tfvars'
        if not prod_tfvars.exists():
            warning("tenant-prod.tfvars not found. You'll need to create this before deployment.")
        else:
            success("tenant-prod.tfvars exists")
    
    return True

def identify_mock_implementations() -> Dict[str, List[str]]:
    '''
    Identifies mock implementations that need to be replaced.
    '''
    section("Identifying Mock Implementations")
    
    mock_patterns = [
        "mock", "fake", "dummy", "stub", "test data", 
        "placeholder", "TODO", "FIXME", "# This is a custom method"
    ]
    
    # Patterns to exclude (legitimate references to mock or stub in real implementations)
    exclude_patterns = [
        "from common.cassandra_client", 
        "from common.openai_client",
        "import PulsarClient",
        "replace mock",
        "replacing mock",
        "unmock",
        "real implementation"
    ]
    
    # Files to exclude from checking
    exclude_files = [
        'verify_deployment.py',
        'setup_env_prod.sh',
        'setup_env_prod.ps1',
        'cassandra_client.js',
        'openai_client.js',
        'test_',
        'README.md',
        '.gitignore'
    ]
    
    # Files to check
    python_files = list(Path('./agents').rglob('*.py'))
    python_files.extend(Path('./common').rglob('*.py'))
    js_files = list(Path('./frontend').rglob('*.js'))
    js_files.extend(Path('./frontend').rglob('*.jsx'))
    js_files.extend(Path('./frontend').rglob('*.ts'))
    js_files.extend(Path('./frontend').rglob('*.tsx'))
    
    mock_implementations = {}
    
    for files, ext in [(python_files, 'Python'), (js_files, 'JavaScript')]:
        found_mocks = []
        for file_path in files:
            # Skip excluded files
            if any(exclude_file in str(file_path) for exclude_file in exclude_files):
                continue
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                    
                    # Skip if file contains exclude patterns
                    if any(exclude.lower() in content.lower() for exclude in exclude_patterns):
                        continue
                        
                    for pattern in mock_patterns:
                        if pattern.lower() in content.lower():
                            line_number = content.lower().find(pattern.lower())
                            line_context = content[max(0, line_number-50):min(len(content), line_number+50)]
                            found_mocks.append(f"{file_path}:{line_context}")
                            break
                except Exception as e:
                    warning(f"Could not read {file_path}: {str(e)}")
                    
        mock_implementations[ext] = found_mocks
    
    for lang, mocks in mock_implementations.items():
        if mocks:
            warning(f"Found {len(mocks)} potential mock implementations in {lang} files")
            for mock in mocks[:5]:  # Show the first 5 mocks only
                print(f"  - {mock}")
            if len(mocks) > 5:
                print(f"  ... and {len(mocks) - 5} more")
        else:
            success(f"No mock implementations found in {lang} files")
    
    return mock_implementations

# Main execution
if __name__ == "__main__":
    # Check command line arguments
    env_file = '.env.prod'
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
    
    print(f"{COLORS['BOLD']}Voice-of-Customer & Brand-Intel Platform Deployment Verification{COLORS['RESET']}")
    print(f"Verifying deployment readiness using {env_file}...\n")
    
    # Run checks
    env_check = check_env_file(env_file)
    docker_check = check_docker_files()
    gitignore_check = check_gitignore()
    terraform_check = check_terraform_config()
    mock_implementations = identify_mock_implementations()
    
    # Summary
    section("Verification Summary")
    if not env_check['missing'] and not env_check['empty']:
        success("Environment configuration is complete")
    else:
        error(f"Environment configuration has issues: {len(env_check['missing'])} missing, {len(env_check['empty'])} empty variables")
        
    if docker_check:
        success("Docker configuration is valid")
    else:
        error("Docker configuration has issues")
        
    if gitignore_check:
        success(".gitignore configuration is valid")
    else:
        warning(".gitignore may be missing important entries")
        
    if terraform_check:
        success("Terraform configuration is valid")
    else:
        error("Terraform configuration has issues")
    
    mock_count = sum([len(mocks) for mocks in mock_implementations.values()])
    if mock_count > 0:
        warning(f"Found {mock_count} potential mock implementations that need real implementations")
    else:
        success("No mock implementations detected")
    
    # Final assessment
    print("\n" + "-" * 80)
    if not env_check['missing'] and docker_check and gitignore_check and terraform_check and mock_count == 0:
        print(f"{COLORS['GREEN']}{COLORS['BOLD']}✓ DEPLOYMENT READY: All checks passed!{COLORS['RESET']}")
    elif not env_check['missing'] and docker_check and terraform_check:
        print(f"{COLORS['YELLOW']}{COLORS['BOLD']}⚠ PARTIALLY READY: Core checks passed but there are warnings.{COLORS['RESET']}")
        print("You may proceed with deployment after addressing the warnings.")
    else:
        print(f"{COLORS['RED']}{COLORS['BOLD']}✗ NOT READY: Critical checks failed.{COLORS['RESET']}")
        print("Please address the errors before attempting deployment.")
    print("-" * 80)
