@echo off
echo 🚀 LMS API Backend Setup
echo ========================

echo.
echo 📁 Creating virtual environment...
python -m venv lms_venv

echo.
echo 🔄 Activating virtual environment...
call lms_venv\Scripts\activate.bat

echo.
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🧪 Testing Pinecone setup...
python setup_pinecone.py

echo.
echo ✅ Setup complete!
echo.
echo 📋 Next Steps:
echo 1. Activate venv: lms_venv\Scripts\activate.bat
echo 2. Start Task 1: Serverless Project Setup
echo 3. Deploy: sam build && sam deploy --guided

pause