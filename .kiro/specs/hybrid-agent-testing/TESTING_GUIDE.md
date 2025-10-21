# Hybrid Agent Testing Guide

## Overview

This guide provides comprehensive testing scenarios, validation checklists, and debugging procedures for the Hybrid Agent Testing system. The system enables testing AWS Bedrock Agent functionality locally using mock authentication with direct AWS service integration.

## Testing Scenarios

### 1. Environment Configuration Testing

#### Test Case 1.1: Hybrid Mode Detection
**Objective**: Verify the system correctly detects hybrid testing mode
**Prerequisites**: Environment variables configured
**Steps**:
1. Set `VITE_USE_MOCK_AUTH=true` and `VITE_USE_MOCK_AGENT=false`
2. Start the application
3. Check the UI for hybrid mode indicators
**Expected Result**: System displays "Hybrid Testing Mode" indicator
**Validation**: Mode indicator shows green status with "Real Agent" label

#### Test Case 1.2: AWS Configuration Validation
**Objective**: Verify AWS credentials and agent connectivity
**Prerequisites**: AWS CLI configured with valid credentials
**Steps**:
1. Open Agent Tester interface
2. Click "Test Configuration" button
3. Review configuration status display
**Expected Result**: All AWS services show "Connected" status
**Validation**: No red error indicators in configuration panel

#### Test Case 1.3: Environment Variable Validation
**Objective**: Ensure all required environment variables are set
**Prerequisites**: .env.local file configured
**Steps**:
1. Check configuration validation in AgentTester component
2. Verify all required variables are detected
**Expected Result**: Configuration status shows all variables as valid
**Validation**: No missing variable warnings displayed

### 2. Direct Agent Service Testing

#### Test Case 2.1: Basic Chat Functionality
**Objective**: Test basic chat communication with Bedrock Agent
**Prerequisites**: Agent service initialized, valid session
**Steps**:
1. Open ChatTester component
2. Send message: "Hello, can you help me with learning?"
3. Wait for agent response
4. Verify conversation history updates
**Expected Result**: Agent responds with helpful message
**Validation**: Response appears in chat history with timestamp

#### Test Case 2.2: Session Management
**Objective**: Verify session creation and persistence
**Prerequisites**: DirectAgentService configured
**Steps**:
1. Start new chat session
2. Send multiple messages in sequence
3. Check session ID consistency
4. Verify conversation context maintained
**Expected Result**: All messages use same session ID
**Validation**: Session ID displayed in debug panel remains constant

#### Test Case 2.3: Error Handling
**Objective**: Test error scenarios and recovery
**Prerequisites**: Network connectivity available
**Steps**:
1. Send message with invalid characters
2. Test with extremely long message (>10000 chars)
3. Simulate network timeout
**Expected Result**: Appropriate error messages displayed
**Validation**: User-friendly error messages, no application crashes

### 3. Document Analysis Testing

#### Test Case 3.1: PDF Document Upload
**Objective**: Test document upload and analysis functionality
**Prerequisites**: Sample PDF document available
**Steps**:
1. Open DocumentTester component
2. Upload a PDF document (< 10MB)
3. Click "Analyze Document" button
4. Wait for analysis results
**Expected Result**: Document analysis results displayed
**Validation**: Key insights, summary, and suggested questions shown

#### Test Case 3.2: Document Processing Pipeline
**Objective**: Verify complete document processing workflow
**Prerequisites**: Document uploaded successfully
**Steps**:
1. Upload document with complex content
2. Request specific analysis: "Summarize key concepts"
3. Verify S3 upload completion
4. Check agent processing results
**Expected Result**: Detailed analysis with citations
**Validation**: Analysis includes document references and confidence scores

#### Test Case 3.3: Document Error Scenarios
**Objective**: Test document processing error handling
**Prerequisites**: DocumentTester component loaded
**Steps**:
1. Upload unsupported file format (.txt, .docx)
2. Upload oversized file (>50MB)
3. Upload corrupted PDF file
**Expected Result**: Clear error messages for each scenario
**Validation**: Specific error descriptions, no system crashes

### 4. Quiz Generation Testing

#### Test Case 4.1: Basic Quiz Creation
**Objective**: Test AI-powered quiz generation
**Prerequisites**: QuizTester component loaded
**Steps**:
1. Enter topic: "Machine Learning Basics"
2. Set difficulty: "Medium"
3. Set question count: 5
4. Click "Generate Quiz"
**Expected Result**: 5 multiple-choice questions generated
**Validation**: Questions relevant to topic, appropriate difficulty

#### Test Case 4.2: Quiz Customization
**Objective**: Test quiz parameter customization
**Prerequisites**: Quiz generation working
**Steps**:
1. Test different difficulty levels (Easy, Medium, Hard)
2. Test different question counts (3, 5, 10)
3. Test different question types
**Expected Result**: Quiz adapts to specified parameters
**Validation**: Question complexity matches difficulty setting

#### Test Case 4.3: Quiz Content Validation
**Objective**: Verify quiz content quality and accuracy
**Prerequisites**: Generated quiz available
**Steps**:
1. Review question clarity and grammar
2. Check answer options for correctness
3. Verify explanations are provided
**Expected Result**: High-quality, educational quiz content
**Validation**: No grammatical errors, logical answer choices

### 5. Interview Practice Testing

#### Test Case 5.1: Interview Session Initialization
**Objective**: Test interview practice setup
**Prerequisites**: InterviewTester component loaded
**Steps**:
1. Select interview topic: "Software Engineering"
2. Click "Start Interview"
3. Verify session initialization
**Expected Result**: Interview session starts with first question
**Validation**: Question displayed, response input available

#### Test Case 5.2: Interview Conversation Flow
**Objective**: Test multi-turn interview simulation
**Prerequisites**: Interview session active
**Steps**:
1. Provide answer to first question
2. Submit response and wait for follow-up
3. Continue for 3-5 question cycles
4. End interview session
**Expected Result**: Natural conversation flow maintained
**Validation**: Follow-up questions relevant to previous answers

#### Test Case 5.3: Interview Feedback Generation
**Objective**: Test AI feedback on interview performance
**Prerequisites**: Completed interview session
**Steps**:
1. Complete full interview session
2. Request performance feedback
3. Review feedback quality and relevance
**Expected Result**: Constructive feedback with specific suggestions
**Validation**: Feedback addresses actual responses given

### 6. Integration Testing

#### Test Case 6.1: Component Integration
**Objective**: Test integration between all major components
**Prerequisites**: All components loaded successfully
**Steps**:
1. Switch between different testing interfaces
2. Verify state persistence across components
3. Test shared session management
**Expected Result**: Seamless navigation between features
**Validation**: No data loss when switching components

#### Test Case 6.2: Mock to Real Service Integration
**Objective**: Verify hybrid mode functionality
**Prerequisites**: Both mock and real services configured
**Steps**:
1. Test with mock authentication active
2. Verify real agent service calls
3. Check UI component behavior
**Expected Result**: Mock auth with real AI functionality
**Validation**: User context from mock, AI responses from real agent

#### Test Case 6.3: Performance Under Load
**Objective**: Test system performance with multiple concurrent requests
**Prerequisites**: Performance monitoring enabled
**Steps**:
1. Send multiple chat messages rapidly
2. Upload multiple documents simultaneously
3. Generate multiple quizzes concurrently
**Expected Result**: System handles load gracefully
**Validation**: Response times remain under 5 seconds

## Feature Validation Checklist

### Pre-Testing Setup
- [ ] AWS CLI configured with valid credentials
- [ ] Environment variables set in .env.local
- [ ] Node.js dependencies installed
- [ ] Development server running
- [ ] Bedrock Agent accessible (Agent ID: ZTBBVSC6Y1)

### Core Functionality
- [ ] Hybrid mode detection working
- [ ] Mock authentication providing user context
- [ ] Direct agent service connecting to AWS
- [ ] Configuration validation showing all green
- [ ] Error handling displaying user-friendly messages

### Chat Testing
- [ ] Basic chat messages working
- [ ] Conversation history maintained
- [ ] Session management functional
- [ ] Response formatting correct
- [ ] Error scenarios handled gracefully

### Document Analysis
- [ ] PDF upload successful
- [ ] Document analysis generating insights
- [ ] S3 integration working
- [ ] Analysis results properly formatted
- [ ] Error handling for invalid files

### Quiz Generation
- [ ] Quiz creation from topics working
- [ ] Parameter customization functional
- [ ] Question quality acceptable
- [ ] Answer validation working
- [ ] Different difficulty levels supported

### Interview Practice
- [ ] Interview session initialization working
- [ ] Multi-turn conversation flow natural
- [ ] Feedback generation providing value
- [ ] Session management stable
- [ ] Voice input processing (if enabled)

### Performance & Reliability
- [ ] Response times under target thresholds
- [ ] No memory leaks during extended use
- [ ] Error recovery working properly
- [ ] Logging capturing important events
- [ ] UI remaining responsive under load

## Debugging Guide

### Common Issues and Solutions

#### Issue: "Agent not responding"
**Symptoms**: Chat messages sent but no response received
**Debugging Steps**:
1. Check browser console for JavaScript errors
2. Verify AWS credentials in configuration panel
3. Check network tab for failed API calls
4. Verify Bedrock Agent ID and alias are correct
**Solution**: Update AWS credentials or check agent deployment status

#### Issue: "Configuration validation failing"
**Symptoms**: Red status indicators in configuration panel
**Debugging Steps**:
1. Verify .env.local file exists and has correct values
2. Check AWS CLI configuration: `aws sts get-caller-identity`
3. Test Bedrock access: `aws bedrock list-foundation-models`
4. Verify agent exists: `aws bedrock-agent get-agent --agent-id ZTBBVSC6Y1`
**Solution**: Fix AWS configuration or update environment variables

#### Issue: "Document upload failing"
**Symptoms**: Upload progress stops or error messages appear
**Debugging Steps**:
1. Check file size (must be < 10MB for testing)
2. Verify file format is supported (PDF recommended)
3. Check S3 bucket permissions
4. Review browser console for upload errors
**Solution**: Use smaller files or check S3 configuration

#### Issue: "Quiz generation producing poor quality"
**Symptoms**: Irrelevant questions or incorrect answers
**Debugging Steps**:
1. Check input topic clarity and specificity
2. Verify agent instructions are properly configured
3. Test with different topics to isolate issue
4. Review agent logs in CloudWatch
**Solution**: Refine topic description or update agent instructions

#### Issue: "Performance degradation"
**Symptoms**: Slow response times or UI freezing
**Debugging Steps**:
1. Check browser performance tab for bottlenecks
2. Monitor network requests for slow API calls
3. Review memory usage in browser dev tools
4. Check for JavaScript errors or infinite loops
**Solution**: Optimize API calls or restart development server

### Debug Tools and Techniques

#### Browser Developer Tools
- **Console**: Check for JavaScript errors and warnings
- **Network**: Monitor API calls and response times
- **Performance**: Profile application performance
- **Application**: Inspect local storage and session data

#### AWS CloudWatch Logs
- **Agent Logs**: Monitor Bedrock Agent execution logs
- **Lambda Logs**: Check action group execution details
- **API Gateway Logs**: Review request/response patterns

#### Application Debug Features
- **Configuration Panel**: Real-time status of all services
- **Session Debug Info**: Display session IDs and state
- **Performance Metrics**: Response time monitoring
- **Error Logging**: Detailed error information capture

### Logging and Monitoring

#### Enable Debug Logging
```javascript
// Add to .env.local for verbose logging
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
```

#### Monitor Key Metrics
- Agent response times
- Error rates by component
- Session duration and activity
- Document processing success rates
- Quiz generation quality scores

#### Performance Monitoring
- Memory usage trends
- API call frequency and duration
- UI responsiveness metrics
- Error recovery success rates

### Troubleshooting Workflow

1. **Identify Symptoms**: Document exact error messages and behaviors
2. **Check Configuration**: Verify all environment variables and AWS setup
3. **Review Logs**: Check browser console and AWS CloudWatch logs
4. **Isolate Issue**: Test individual components to narrow down problem
5. **Apply Solution**: Implement fix based on root cause analysis
6. **Verify Fix**: Re-test affected functionality thoroughly
7. **Document Resolution**: Update troubleshooting guide with new solutions

### Support and Resources

#### Documentation References
- AWS Bedrock Agent Documentation
- React Development Guide
- AWS SDK for JavaScript Documentation
- TypeScript Configuration Guide

#### Community Resources
- AWS Developer Forums
- Stack Overflow (aws-bedrock tag)
- GitHub Issues for related projects
- AWS Support (if available)

#### Internal Resources
- Project README.md
- Architecture documentation
- API specifications
- Deployment guides

This testing guide provides comprehensive coverage for validating the hybrid agent testing system functionality and troubleshooting common issues.