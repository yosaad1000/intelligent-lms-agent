# 🚀 LMS React Frontend - Complete Setup Guide for Testing

## 📋 **What Your Friend Can Test**

### ✅ **Frontend Features (Works Immediately)**
- Complete React UI with all pages and components
- Dark/Light theme switching
- Responsive design (mobile, tablet, desktop)
- Accessibility features
- Mock authentication (no AWS needed)
- All navigation and UI interactions

### 🔧 **Full AI Agent Features (Requires AWS Setup)**
- Real Bedrock AI Agent conversations
- Document upload and processing
- Voice interview functionality
- Learning analytics with real data
- Quiz generation from documents

---

## 🎯 **Quick Start (Frontend Only)**

Your friend can test the UI immediately without any AWS setup:

### 1. **Clone & Install**
```bash
git clone https://github.com/yosaad1000/intelligent-lms-agent.git
cd intelligent-lms-agent/frontend_extracted/frontend
npm install
```

### 2. **Start Development Server**
```bash
npm run dev
```

### 3. **Access the App**
- Open: `http://localhost:5173`
- Login with mock credentials:
  - **Teacher**: `teacher@demo.com` / `password123`
  - **Student**: `student@demo.com` / `password123`

### 4. **Test Features**
- ✅ All UI components and navigation
- ✅ Theme switching (dark/light mode)
- ✅ Responsive design on different screen sizes
- ✅ Teacher dashboard with all pages
- ✅ Student dashboard and features
- ✅ Profile settings and preferences
- ✅ Mock data for all features

---

## 🤖 **Full AI Agent Testing (WITH ADMIN ACCESS - EASY!)**

✅ **GREAT NEWS**: With admin access, your friend can test ALL features immediately!

### **Current AWS Resources Available:**
- ✅ **Bedrock Agent**: `ZTBBVSC6Y1` (lms-analytics-assistant) - **ACTIVE & READY**
- ✅ **API Gateway**: `7k21xsoz93` (lms-api-dev) - **DEPLOYED & WORKING**
- ✅ **S3 Buckets**: Multiple document storage buckets - **ACCESSIBLE**
- ✅ **WebSocket**: Real-time communication endpoints - **LIVE**

### **Simple Setup with Admin Access:**

#### 1. **Configure AWS CLI (One-time setup)**
```bash
aws configure
# Enter your admin AWS credentials when prompted
# Region: us-east-1
# Output format: json
```

#### 2. **Update Environment Configuration**
Edit `.env.local` in the frontend directory:
```bash
# Enable Real Agent (instead of mock)
VITE_USE_MOCK_AUTH=false
VITE_USE_MOCK_AGENT=false
VITE_USE_DUMMY_DATA=false

# AWS Configuration (Admin access - full permissions)
VITE_AWS_REGION=us-east-1

# Bedrock Agent (Already Deployed & Active)
VITE_BEDROCK_AGENT_ID=ZTBBVSC6Y1
VITE_BEDROCK_AGENT_ALIAS_ID=TSTALIASID

# API Endpoints (Already Deployed & Working)
VITE_API_GATEWAY_URL=https://7k21xsoz93.execute-api.us-east-1.amazonaws.com/dev
VITE_WEBSOCKET_URL=wss://4olkavb3wa.execute-api.us-east-1.amazonaws.com/dev
VITE_DOCUMENTS_BUCKET=lms-documents-dev-145023137830

# Supabase (Real authentication)
VITE_SUPABASE_URL=https://scijpejtvneuqbhkoxuz.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjaWpwZWp0dm5ldXFiaGtveHV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU1OTcxNDEsImV4cCI6MjA3MTE3MzE0MX0.Z6Q_DmsuHYOOvCGed5hcKDrT93XPL5hHwCyGDREcmmw
```

#### 3. **Test Real AI Features**
With AWS credentials configured, your friend can test:
- 🤖 **AI Chat**: Real conversations with Bedrock Agent
- 📄 **Document Upload**: Upload PDFs and get AI analysis
- 🎤 **Voice Interviews**: Record and get AI feedback
- 📊 **Analytics**: Real learning progress tracking
- 🧪 **Quiz Generation**: AI-generated quizzes from documents

---

## 🧪 **Testing Scenarios**

### **Frontend-Only Testing (No AWS)**
1. **Navigation**: Test all pages and routes
2. **Responsive Design**: Resize browser, test mobile view
3. **Theme Switching**: Toggle dark/light mode
4. **Forms**: Fill out profile, settings, preferences
5. **Mock Data**: View dashboards with sample data

### **Full AI Testing (With AWS)**
1. **AI Chat**: 
   - Go to Study Chat page
   - Ask questions about learning topics
   - Test document-based conversations

2. **Document Processing**:
   - Upload PDF documents
   - Wait for AI analysis
   - Ask questions about uploaded content

3. **Voice Interviews**:
   - Record voice responses
   - Get AI feedback and scoring
   - Test transcription accuracy

4. **Learning Analytics**:
   - View real progress data
   - Test analytics dashboard
   - Check recommendation engine

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **Frontend Won't Start**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### **AWS Authentication Errors**
- Check AWS credentials are valid
- Verify IAM permissions for Bedrock and S3
- Test credentials with: `aws sts get-caller-identity`

#### **API Gateway Errors**
- Verify API Gateway endpoints are deployed
- Check CORS configuration
- Test endpoints directly with curl/Postman

#### **Bedrock Agent Not Responding**
- Verify agent ID: `ZTBBVSC6Y1` is active
- Check agent alias: `TSTALIASID` exists
- Test agent via AWS Console first

---

## 📊 **Current Deployment Status**

### ✅ **Active Resources**
- **Bedrock Agent**: `lms-analytics-assistant` (PREPARED)
- **API Gateway**: `lms-api-dev` (7k21xsoz93)
- **S3 Buckets**: 6 buckets for document storage
- **Frontend**: Production-ready React app

### 🔧 **Configuration Needed**
- AWS credentials for full functionality
- Environment variables for real agent
- Optional: Supabase for real authentication

---

## 🎯 **Recommendation**

**For Quick Demo**: Start with frontend-only testing (mock mode)
**For Full Testing**: Provide AWS credentials for complete functionality

The app is designed to work in both modes - your friend can see the full UI and interactions immediately, then upgrade to real AI features when AWS is configured.

---

## 📞 **Support**

If your friend encounters issues:
1. Check the browser console for errors
2. Verify environment variables are set correctly
3. Test AWS credentials separately
4. Start with mock mode first, then enable real features

The frontend is production-ready and will work immediately for UI testing!