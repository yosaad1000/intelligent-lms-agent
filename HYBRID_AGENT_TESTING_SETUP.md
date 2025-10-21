# 🚀 Hybrid Agent Testing Setup Guide

## Overview

This guide helps you set up **Hybrid Agent Testing Mode** - a configuration that allows you to test your deployed AWS Bedrock Agent directly from your local React frontend without complex authentication setup.

## 🎯 What You Get

- ✅ **Mock Authentication**: No Supabase setup needed
- ✅ **Real Bedrock Agent**: Direct connection to your deployed agent (ZTBBVSC6Y1)
- ✅ **Full UI Testing**: All frontend components work normally
- ✅ **Quick Setup**: 15-20 minutes from start to testing

## 📋 Prerequisites

1. **Node.js 18+** installed
2. **AWS CLI** installed
3. **AWS Account** with Bedrock access
4. **Your Bedrock Agent** already deployed (Agent ID: ZTBBVSC6Y1)

## 🔧 Setup Steps

### Step 1: Configure AWS CLI

```bash
# Configure your AWS credentials
aws configure

# Enter your credentials:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-east-1
# Default output format: json
```

### Step 2: Test AWS Connection

```bash
# Test your AWS connection
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Step 3: Verify Environment Configuration

The `.env.local` file should already be configured for hybrid testing:

```bash
# Hybrid Agent Testing Mode Configuration
VITE_NODE_ENV=development
VITE_USE_MOCK_AUTH=true          # ✅ Mock authentication
VITE_USE_MOCK_AGENT=false        # ✅ Real Bedrock Agent
VITE_USE_DUMMY_DATA=true         # ✅ Mock UI data
VITE_AGENT_TESTING_MODE=true     # ✅ Testing mode enabled

# AWS Configuration (already configured)
VITE_AWS_REGION=us-east-1
VITE_BEDROCK_AGENT_ID=ZTBBVSC6Y1
VITE_BEDROCK_AGENT_ALIAS_ID=TSTALIASID
```

### Step 4: Start the Application

```bash
# The server should already be running at http://localhost:5173
# If not, start it:
npm run dev
```

## 🧪 Testing Your Agent

### 1. Access the Agent Tester

Navigate to: `http://localhost:5173/agent-tester`

### 2. Verify Configuration

- Check that "Configuration Valid" shows green ✅
- If red ❌, follow the troubleshooting steps below

### 3. Run Quick Tests

Click the test buttons to validate each feature:
- **Chat Test**: Basic agent conversation
- **Document Test**: Document analysis capability
- **Quiz Test**: Quiz generation functionality
- **Interview Test**: Interview simulation

### 4. Test Full Features

Navigate to the main features to test complete workflows:
- **Chat**: `/chat` - Full conversation interface
- **Documents**: `/documents` - Document upload and analysis
- **Quizzes**: `/quizzes` - Quiz generation and taking
- **Interview**: `/interview` - Interview practice simulation

## 🔍 How It Works

### Architecture
```
Local Frontend (Mock Auth)
    ↓
Direct Agent Service
    ↓
AWS SDK (Your Credentials)
    ↓
Bedrock Agent (ZTBBVSC6Y1) - REAL
    ↓
Your Lambda Functions - REAL
```

### What's Mock vs Real

**Mock (Local Only):**
- ✅ User authentication (login with teacher@demo.com/password123)
- ✅ User profiles and settings
- ✅ Class management and student data
- ✅ UI navigation and components

**Real (AWS Services):**
- 🔥 **Bedrock Agent conversations**
- 🔥 **Document analysis and insights**
- 🔥 **AI quiz generation**
- 🔥 **Interview practice and feedback**
- 🔥 **Learning analytics**

## 🐛 Troubleshooting

### Configuration Shows Invalid ❌

**Problem**: AWS credentials or permissions issue

**Solutions**:
1. **Check AWS CLI configuration**:
   ```bash
   aws configure list
   aws sts get-caller-identity
   ```

2. **Verify Bedrock permissions**:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

3. **Test agent access**:
   ```bash
   aws bedrock-agent-runtime invoke-agent \
     --agent-id ZTBBVSC6Y1 \
     --agent-alias-id TSTALIASID \
     --session-id test \
     --input-text "Hello"
   ```

### Tests Fail with Network Errors

**Problem**: Network connectivity or AWS service issues

**Solutions**:
1. Check internet connection
2. Verify AWS region is correct (us-east-1)
3. Check AWS service status
4. Try different network (VPN issues)

### Tests Fail with Permission Errors

**Problem**: Insufficient AWS permissions

**Required Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel",
        "bedrock-agent-runtime:InvokeAgent",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "*"
    }
  ]
}
```

### Frontend Won't Start

**Problem**: Dependencies or build issues

**Solutions**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

## 🎯 Testing Scenarios

### 1. Basic Chat Testing
1. Go to `/chat`
2. Send message: "Hello, can you help me with machine learning?"
3. Verify you get a real AI response
4. Check browser console for "Using Direct Agent Service" log

### 2. Document Analysis Testing
1. Go to `/documents`
2. Upload a PDF document
3. Ask questions about the document
4. Verify AI provides relevant insights

### 3. Quiz Generation Testing
1. Go to `/quizzes`
2. Provide some content or topic
3. Generate a quiz
4. Verify questions are relevant and well-formed

### 4. Interview Practice Testing
1. Go to `/interview`
2. Start an interview on a topic
3. Provide responses
4. Verify AI gives constructive feedback

## 📊 Monitoring and Debugging

### Browser Console Logs
Look for these log messages:
- `🤖 Sending message to agent: "..."`
- `✅ Agent response received (XXXms): ...`
- `🔄 Using Direct Agent Service (Hybrid Mode)`

### AWS CloudWatch Logs
Monitor your Lambda function logs for:
- Agent invocations
- Processing times
- Error messages

### Performance Expectations
- **Chat responses**: < 3 seconds
- **Document analysis**: < 10 seconds
- **Quiz generation**: < 5 seconds
- **Interview feedback**: < 5 seconds

## 🔒 Security Notes

- AWS credentials are handled through AWS CLI (secure)
- No sensitive data stored in browser
- All communication encrypted in transit
- Session data temporary and local only

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Configuration shows valid in Agent Tester
- ✅ All quick tests pass
- ✅ Chat responses are contextual and intelligent
- ✅ Document analysis provides relevant insights
- ✅ Quiz questions are well-formed and relevant
- ✅ Interview feedback is constructive and detailed

## 🆘 Getting Help

If you encounter issues:
1. Check browser console for error messages
2. Verify AWS CLI configuration
3. Test AWS connectivity separately
4. Check the troubleshooting section above
5. Review CloudWatch logs for your Lambda functions

**This setup gives you the fastest path to testing your Bedrock Agent with full UI integration!** 🚀