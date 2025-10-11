# Authentication Microservice - MVP Requirements

## Overview
**Priority: CRITICAL (Build First)**  
Simple authentication service using AWS Cognito + Gradio interface for rapid MVP development.

## Core User Stories

### US-AUTH-001: Simple User Registration
**As a** student  
**I want to** register with email/password  
**So that** I can access the LMS system

#### Acceptance Criteria (EARS Format)
1. WHEN a user provides email and password THEN the system SHALL create a Cognito user account
2. WHEN registration is successful THEN the system SHALL send email verification
3. WHEN email is verified THEN the system SHALL enable account access
4. IF email already exists THEN the system SHALL return appropriate error message

### US-AUTH-002: Simple Login
**As a** registered user  
**I want to** login with my credentials  
**So that** I can access my personalized content

#### Acceptance Criteria
1. WHEN user provides valid credentials THEN the system SHALL authenticate via Cognito
2. WHEN authentication succeeds THEN the system SHALL return JWT access token
3. WHEN token is valid THEN the system SHALL allow access to protected features
4. IF credentials are invalid THEN the system SHALL return authentication error

## Technical Implementation (Fast Build)

### Technology Stack
- **Frontend**: Gradio authentication components
- **Backend**: AWS Cognito User Pools
- **Integration**: boto3 cognito-idp client
- **Storage**: Cognito handles user data

### MVP Implementation
```python
# Fast implementation using Gradio + Cognito
import gradio as gr
import boto3
from botocore.exceptions import ClientError

class FastAuth:
    def __init__(self):
        self.cognito = boto3.client('cognito-idp')
        self.user_pool_id = 'your-user-pool-id'
        self.client_id = 'your-client-id'
    
    def register_user(self, email, password):
        try:
            response = self.cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                TemporaryPassword=password,
                MessageAction='SUPPRESS'
            )
            return "✅ Registration successful! Please verify your email."
        except ClientError as e:
            return f"❌ Registration failed: {e.response['Error']['Message']}"
    
    def login_user(self, email, password):
        try:
            response = self.cognito.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={'USERNAME': email, 'PASSWORD': password}
            )
            return "✅ Login successful!", response['AuthenticationResult']['AccessToken']
        except ClientError as e:
            return f"❌ Login failed: {e.response['Error']['Message']}", None

# Gradio Interface
def create_auth_interface():
    with gr.Blocks() as auth_app:
        gr.Markdown("# 🔐 LMS Authentication")
        
        with gr.Tab("Register"):
            reg_email = gr.Textbox(label="Email")
            reg_password = gr.Textbox(label="Password", type="password")
            reg_btn = gr.Button("Register")
            reg_output = gr.Textbox(label="Status")
            
        with gr.Tab("Login"):
            login_email = gr.Textbox(label="Email")
            login_password = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            login_output = gr.Textbox(label="Status")
    
    return auth_app
```

## Testing Strategy
- **Unit Test**: Test Cognito integration with mock users
- **Integration Test**: End-to-end registration and login flow
- **Manual Test**: Use Gradio interface to register and login
- **Merge Test**: Verify token validation works with other services

## Dependencies
- None (foundational service)

## Delivery Timeline
- **Day 1**: Basic Cognito setup and Gradio interface
- **Day 2**: Testing and integration with main app