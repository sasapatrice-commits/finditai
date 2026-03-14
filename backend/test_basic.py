#!/usr/bin/env python3
"""
FindIt AI - Basic functionality test script
Tests core features without AI dependencies for initial validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test basic Python imports"""
    try:
        import jwt
        import fastapi
        import sqlalchemy
        import bcrypt
        print("✅ Basic dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_schema():
    """Test database schema creation"""
    try:
        from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker

        # Test schema creation
        engine = create_engine("sqlite:///:memory:")
        Base = declarative_base()

        # Define test tables
        class TestUser(Base):
            __tablename__ = "test_users"
            id = Column(Integer, primary_key=True)
            username = Column(String, unique=True)
            role = Column(String)

        class TestItem(Base):
            __tablename__ = "test_items"
            id = Column(Integer, primary_key=True)
            name = Column(String)
            description = Column(Text)

        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema creation successful")
        return True
    except Exception as e:
        print(f"❌ Database schema error: {e}")
        return False

def test_auth_functions():
    """Test authentication functions"""
    try:
        import jwt
        import bcrypt
        from datetime import datetime, timedelta, timezone

        # Test password hashing
        password = "testpassword"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

        # Test JWT creation
        secret = "test-secret"
        exp_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        token = jwt.encode({"sub": "testuser", "exp": int(exp_time.timestamp())}, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["sub"] == "testuser"

        print("✅ Authentication functions working")
        return True
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def test_file_operations():
    """Test file upload directory creation"""
    try:
        from pathlib import Path
        upload_dir = Path("./test_uploads")
        upload_dir.mkdir(exist_ok=True)

        # Test file creation
        test_file = upload_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

        # Cleanup
        test_file.unlink()
        upload_dir.rmdir()

        print("✅ File operations working")
        return True
    except Exception as e:
        print(f"❌ File operations error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 FindIt AI - Basic Functionality Tests")
    print("=" * 40)

    tests = [
        ("Python Imports", test_imports),
        ("Database Schema", test_database_schema),
        ("Authentication", test_auth_functions),
        ("File Operations", test_file_operations),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All basic functionality tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the server: python main.py")
        print("3. Test AI features (requires torch, torchvision, sentence-transformers)")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)