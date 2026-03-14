#!/bin/bash

# FindIt AI Setup Script
echo "🚀 Setting up FindIt AI Lost-and-Found System"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup backend
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv || python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo "✅ Backend setup complete"

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo "✅ Frontend setup complete"

# Create uploads directory
echo ""
echo "📁 Creating uploads directory..."
cd ..
mkdir -p uploads

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "Then visit http://localhost:3000 in your browser"
echo ""
echo "To populate with sample data, make a POST request to:"
echo "http://localhost:8000/seed-data"

# Create uploads directory
echo ""
echo "📁 Creating uploads directory..."
cd ..
mkdir -p uploads

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "Then visit http://localhost:3000 in your browser"
echo ""
echo "To populate with sample data, make a POST request to:"
echo "http://localhost:8000/seed-data"