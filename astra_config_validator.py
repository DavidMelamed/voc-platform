#!/usr/bin/env python3
'''
Astra Configuration Validator

A simplified script to validate Astra DB and Astra Streaming configurations
using HTTP requests instead of direct client connections.
'''

import os
import json
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test results
results = {
    "astra_db": {
        "status": "Not Tested",
        "details": ""
    },
    "astra_streaming": {
        "status": "Not Tested",
        "details": ""
    }
}

def validate_astra_db():
    '''
    Validate Astra DB configuration by making a simple API request
    '''
    print("\n==== Validating Astra DB Configuration ====")
    
    # Get Astra DB configuration
    db_id = os.getenv("ASTRA_DB_ID")
    token = os.getenv("ASTRA_TOKEN")
    api_endpoint = os.getenv("ASTRA_API_ENDPOINT")
    
    if not all([db_id, token, api_endpoint]):
        results["astra_db"]["status"] = "Failed"
        results["astra_db"]["details"] = "Missing required configuration variables"
        print("❌ Missing required Astra DB configuration variables")
        return
    
    print(f"Database ID: {db_id}")
    print(f"API Endpoint: {api_endpoint}")
    
    # Validate token format (should start with "AstraCS:")
    if not token.startswith("AstraCS:"):
        print("⚠️ Token format warning: Should start with 'AstraCS:'")
    
    # Validate endpoint format
    expected_endpoint_format = f"https://{db_id}-"
    if not api_endpoint.startswith(expected_endpoint_format):
        print("⚠️ API endpoint format warning: Doesn't match expected pattern")
        results["astra_db"]["status"] = "Warning"
        results["astra_db"]["details"] = "API endpoint format doesn't match expected pattern"
    else:
        # Try making a request to validate the API endpoint and token
        try:
            # Build the schemas API URL to check if the endpoint is valid
            schemas_url = f"{api_endpoint}/api/rest/v2/schemas/keyspaces"
            headers = {
                "X-Cassandra-Token": token,
                "Content-Type": "application/json"
            }
            
            print(f"Sending test request to: {schemas_url}")
            response = requests.get(schemas_url, headers=headers)
            
            if response.status_code == 200:
                print("✅ Successfully connected to Astra DB API")
                results["astra_db"]["status"] = "Success"
                results["astra_db"]["details"] = "API connection successful"
            else:
                print(f"❌ Failed to connect to Astra DB API: {response.status_code} - {response.text}")
                results["astra_db"]["status"] = "Failed"
                results["astra_db"]["details"] = f"API request failed: {response.status_code}"
        except Exception as e:
            print(f"❌ Error validating Astra DB configuration: {str(e)}")
            results["astra_db"]["status"] = "Failed"
            results["astra_db"]["details"] = str(e)

def validate_astra_streaming():
    '''
    Validate Astra Streaming configuration
    '''
    print("\n==== Validating Astra Streaming Configuration ====")
    
    # Get Astra Streaming configuration
    tenant = os.getenv("ASTRA_STREAMING_TENANT")
    token = os.getenv("ASTRA_STREAMING_TOKEN")
    broker_url = os.getenv("ASTRA_STREAMING_BROKER_URL")
    
    if not all([tenant, token, broker_url]):
        results["astra_streaming"]["status"] = "Failed"
        results["astra_streaming"]["details"] = "Missing required configuration variables"
        print("❌ Missing required Astra Streaming configuration variables")
        return
    
    print(f"Tenant: {tenant}")
    print(f"Broker URL: {broker_url}")
    
    # Validate broker URL format
    if not broker_url.startswith("pulsar+ssl://"):
        print("⚠️ Broker URL format warning: Should start with 'pulsar+ssl://'")
    
    # Validate token format (should be a JWT)
    if token.count('.') != 2:
        print("❌ Invalid token format: JWT should have 3 parts separated by dots")
        results["astra_streaming"]["status"] = "Failed"
        results["astra_streaming"]["details"] = "Invalid token format"
        return
    
    # Validate token by decoding it
    try:
        # Get the payload part (second part)
        payload = token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
        # Decode the payload
        decoded = base64.b64decode(payload).decode('utf-8')
        payload_json = json.loads(decoded)
        
        print("Token payload:")
        print(json.dumps(payload_json, indent=2))
        
        # Check if the tenant info is in the token
        sub = payload_json.get('sub', '')
        if tenant.lower() in sub.lower():
            print("✅ Token contains tenant information")
            results["astra_streaming"]["status"] = "Success"
            results["astra_streaming"]["details"] = "Token validated and contains tenant info"
        else:
            print("⚠️ Tenant name not found in token payload")
            results["astra_streaming"]["status"] = "Warning"
            results["astra_streaming"]["details"] = "Token is valid but tenant not found in payload"
    except Exception as e:
        print(f"❌ Error validating token: {str(e)}")
        results["astra_streaming"]["status"] = "Failed"
        results["astra_streaming"]["details"] = f"Token validation error: {str(e)}"

# Main execution
if __name__ == "__main__":
    print("Starting Astra configuration validation...")
    
    # Validate Astra DB configuration
    validate_astra_db()
    
    # Validate Astra Streaming configuration
    validate_astra_streaming()
    
    # Print summary
    print("\n==== Validation Results Summary ====")
    print(f"Astra DB: {results['astra_db']['status']}")
    print(f"Astra Streaming: {results['astra_streaming']['status']}")
    
    # Output detailed JSON result
    print("\nDetailed results:")
    print(json.dumps(results, indent=2))
