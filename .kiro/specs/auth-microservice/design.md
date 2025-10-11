# Authentication Microservice Design

## Architecture Overview

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Gradio Auth    │───▶│  Python Auth    │───▶│  AWS Cognito    │
│   Interface     │    │    Handler      │    │   User Pool     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Session State   │    │  Token Manager  │    │  User Database  │
│   Management    │    │                 │    │   (Cognito)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **Registration**: User → Gradio → Python Handler → Cognito → Email Verification
2. **Login**: User → Gradio → Python Handler → Cognito → JWT Token → Session State
3. **Authorization**: Protected Action → Token Validation → Allow/Deny

## Technical Design

### Core Classes
```python
class FastAuth:
    """Main authentication handler"""
    def __init__(self):
        self.cognito = boto3.client('cognito-idp')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        self.session_manager = SessionManager()
    
    def register_user(self, email: str, password: str) -> AuthResult
    def login_user(self, email: str, password: str) -> AuthResult
    def validate_token(self, token: str) -> bool
    def refresh_token(self, refresh_token: str) -> AuthResult
    def logout_user(self, token: str) -> bool

class SessionManager:
    """Manage user sessions in Gradio"""
    def create_session(self, user_data: dict) -> str
    def get_session(self, session_id: str) -> dict
    def update_session(self, session_id: str, data: dict) -> bool
    def destroy_session(self, session_id: str) -> bool

class TokenValidator:
    """JWT token validation utilities"""
    def validate_jwt(self, token: str) -> dict
    def extract_user_info(self, token: str) -> dict
    def is_token_expired(self, token: str) -> bool
```

### AWS Cognito Configuration
```json
{
  "UserPool": {
    "PoolName": "lms-user-pool",
    "Policies": {
      "PasswordPolicy": {
        "MinimumLength": 8,
        "RequireUppercase": true,
        "RequireLowercase": true,
        "RequireNumbers": true,
        "RequireSymbols": false
      }
    },
    "AutoVerifiedAttributes": ["email"],
    "UsernameAttributes": ["email"],
    "Schema": [
      {
        "Name": "email",
        "AttributeDataType": "String",
        "Required": true,
        "Mutable": true
      },
      {
        "Name": "role",
        "AttributeDataType": "String",
        "Required": false,
        "Mutable": true
      }
    ]
  }
}
```

### Gradio Interface Design
```python
def create_auth_interface():
    with gr.Blocks() as auth_app:
        # State management
        user_session = gr.State({})
        
        with gr.Tabs():
            with gr.Tab("🔐 Login"):
                login_email = gr.Textbox(label="Email")
                login_password = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Login", variant="primary")
                login_status = gr.Textbox(label="Status", interactive=False)
                
            with gr.Tab("📝 Register"):
                reg_email = gr.Textbox(label="Email")
                reg_password = gr.Textbox(label="Password", type="password")
                reg_confirm = gr.Textbox(label="Confirm Password", type="password")
                reg_btn = gr.Button("Register", variant="primary")
                reg_status = gr.Textbox(label="Status", interactive=False)
        
        # User info display (when logged in)
        user_info = gr.JSON(label="User Info", visible=False)
        logout_btn = gr.Button("Logout", visible=False)
    
    return auth_app
```

## Security Design

### Password Security
- Minimum 8 characters with complexity requirements
- Cognito handles password hashing and storage
- No plaintext passwords stored locally

### Token Management
- JWT tokens with 15-minute expiry
- Refresh tokens with 7-day expiry
- Secure token storage in Gradio session state

### Session Security
- Session IDs generated with UUID4
- Session data encrypted in memory
- Automatic session cleanup on logout

## Error Handling

### Authentication Errors
```python
class AuthError(Exception):
    """Base authentication error"""
    pass

class InvalidCredentialsError(AuthError):
    """Invalid username/password"""
    pass

class TokenExpiredError(AuthError):
    """JWT token has expired"""
    pass

class UserNotFoundError(AuthError):
    """User does not exist"""
    pass
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": {}
  }
}
```

## Integration Points

### With Other Microservices
- **File Processor**: Requires valid JWT token for file uploads
- **AI Chat**: User ID from token for personalized responses
- **Voice Interview**: User authentication for session management
- **Quiz Generator**: User context for personalized quizzes

### Token Validation Middleware
```python
def require_auth(func):
    """Decorator for functions requiring authentication"""
    def wrapper(*args, **kwargs):
        token = get_current_token()
        if not validate_token(token):
            return {"error": "Authentication required"}
        return func(*args, **kwargs)
    return wrapper
```

## Performance Considerations

### Caching Strategy
- Cache Cognito responses for 5 minutes
- Session data stored in memory for fast access
- Token validation cached to reduce Cognito calls

### Scalability
- Stateless design allows horizontal scaling
- Cognito handles user storage and scaling
- Session state can be moved to Redis if needed

## Testing Strategy

### Unit Tests
- Test registration with valid/invalid inputs
- Test login with correct/incorrect credentials
- Test token validation and expiry
- Test session management functions

### Integration Tests
- Test complete registration → verification → login flow
- Test token refresh mechanism
- Test logout and session cleanup
- Test integration with other microservices

### Security Tests
- Test password complexity enforcement
- Test token tampering detection
- Test session hijacking prevention
- Test rate limiting on auth endpoints