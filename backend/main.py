from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
import bcrypt
import os
import shutil
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

# Heavy ML libraries are lazily imported in load_ai_models() to reduce startup time

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Use a database file located alongside this module so the app behaves consistently
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'findit.db'}"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# AI Models (pretrained) - Load only when needed
device = None
image_model = None
text_model = None
transform = None

def load_ai_models():
    """Load AI models on demand"""
    global device, image_model, text_model, transform, torch
    if image_model is None:
        try:
            # imports are delayed until the first request to reduce startup time
            import torch
            import torchvision.transforms as transforms
            from torchvision.models import resnet50
            from sentence_transformers import SentenceTransformer

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            image_model = resnet50(pretrained=True)
            image_model.fc = torch.nn.Identity()  # Remove classification layer
            image_model.eval().to(device)

            text_model = SentenceTransformer('all-MiniLM-L6-v2')

            # Image preprocessing
            transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        except Exception as e:
            print(f"Failed to load AI models: {e}")
            # Set to None so features won't be extracted
            image_model = None
            text_model = None

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # "student" or "staff"
    created_at = Column(DateTime, default=datetime.utcnow)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_type = Column(String)  # "lost" or "found"
    name = Column(String)
    description = Column(Text)
    location = Column(String)
    date_time = Column(DateTime)
    image_path = Column(String, nullable=True)
    image_features = Column(Text, nullable=True)  # JSON string of image features
    text_features = Column(Text, nullable=True)  # JSON string of text features
    status = Column(String, default="active")  # "active", "matched", "claimed"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    lost_item_id = Column(Integer, ForeignKey("items.id"))
    found_item_id = Column(Integer, ForeignKey("items.id"))
    similarity_score = Column(Float)
    image_similarity = Column(Float)
    image_similarity_type = Column(String, default="none")  # 'ai', 'basic', or 'none'
    text_similarity = Column(Float)
    location_match = Column(Boolean)
    time_proximity = Column(Float)  # hours difference
    status = Column(String, default="suggested")  # "suggested", "verified", "rejected"
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lost_item = relationship("Item", foreign_keys=[lost_item_id])
    found_item = relationship("Item", foreign_keys=[found_item_id])
    verifier = relationship("User", foreign_keys=[verified_by])

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="FindIt AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# AI Functions
def extract_image_features(image_path: str) -> np.ndarray:
    """Extract features from image using pretrained ResNet"""
    load_ai_models()  # Ensure models are loaded
    if image_model is None or transform is None:
        raise Exception("AI models not available")
    from PIL import Image
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = image_model(image_tensor)
    return features.cpu().numpy().flatten()

from difflib import SequenceMatcher

def extract_text_features(text: str) -> np.ndarray:
    """Extract features from text using sentence transformers"""
    load_ai_models()  # Ensure models are loaded
    if text_model is None:
        raise Exception("AI models not available")
    return text_model.encode(text)

def simple_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity using difflib"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def calculate_similarity_score(lost_item: Item, found_item: Item) -> dict:
    """Calculate comprehensive similarity score between lost and found items"""
    scores = {
        'image_similarity': 0.0,
        'image_similarity_type': 'none',  # 'ai', 'basic', or 'none'
        'text_similarity': 0.0,
        'location_match': False,
        'time_proximity': 24.0,  # default 24 hours
        'overall_score': 0.0
    }

    # Image similarity
    if lost_item.image_features and found_item.image_features:
        # If we have extracted features for both images, use cosine similarity
        lost_img_feat = np.array(json.loads(lost_item.image_features))
        found_img_feat = np.array(json.loads(found_item.image_features))
        scores['image_similarity'] = float(cosine_similarity([lost_img_feat], [found_img_feat])[0][0])
        scores['image_similarity_type'] = 'ai'
    elif lost_item.image_path or found_item.image_path:
        # Fallback: if at least one item has an image but we don't have features, use a basic comparison
        scores['image_similarity'] = 0.5
        scores['image_similarity_type'] = 'basic'
    else:
        scores['image_similarity_type'] = 'none'
    # If neither has images, image_similarity remains 0.0

    # Text similarity (combine name and description)
    lost_text = f"{lost_item.name} {lost_item.description}"
    found_text = f"{found_item.name} {found_item.description}"

    if lost_item.text_features and found_item.text_features:
        lost_text_feat = np.array(json.loads(lost_item.text_features))
        found_text_feat = np.array(json.loads(found_item.text_features))
        scores['text_similarity'] = float(cosine_similarity([lost_text_feat], [found_text_feat])[0][0])
    else:
        # Fallback to simple text similarity if AI features not available
        scores['text_similarity'] = simple_text_similarity(lost_text, found_text)

    # Location match
    scores['location_match'] = lost_item.location.lower() == found_item.location.lower()

    # Time proximity (hours difference)
    time_diff = abs((lost_item.date_time - found_item.date_time).total_seconds()) / 3600
    scores['time_proximity'] = min(time_diff, 24.0)  # Cap at 24 hours

    # Overall score (weighted combination)
    # Weights: image 0.4, text 0.3, location 0.2, time 0.1
    image_weight = 0.4 if scores['image_similarity'] > 0 else 0
    text_weight = 0.3
    location_weight = 0.2 if scores['location_match'] else 0
    time_weight = 0.1 * (1 - scores['time_proximity'] / 24.0)  # Better when closer in time

    scores['overall_score'] = (
        scores['image_similarity'] * image_weight +
        scores['text_similarity'] * text_weight +
        (1.0 if scores['location_match'] else 0.0) * location_weight +
        time_weight
    )

    return scores

# API Routes
@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": user.role}}

@app.post("/auth/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    if role not in ["student", "staff"]:
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'staff'")

    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}

@app.post("/items/")
async def create_item(
    item_type: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    date_time: str = Form(...),
    image: UploadFile = File(None),
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Parse date_time
    try:
        item_datetime = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date_time format")

    # Handle image upload
    image_path = None
    image_features = None
    if image:
        # Save image
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"{datetime.utcnow().timestamp()}_{image.filename}"
        image_path = UPLOAD_DIR / filename
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Extract image features
        try:
            features = extract_image_features(str(image_path))
            image_features = json.dumps(features.tolist())
        except Exception as e:
            print(f"Error extracting image features: {e}")

    # Extract text features
    text_features = None
    try:
        features = extract_text_features(f"{name} {description}")
        text_features = json.dumps(features.tolist())
    except Exception as e:
        print(f"Error extracting text features: {e}")

    # Create item
    item = Item(
        user_id=user.id,
        item_type=item_type,
        name=name,
        description=description,
        location=location,
        date_time=item_datetime,
        image_path=str(image_path) if image_path else None,
        image_features=image_features,
        text_features=text_features
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    # Find potential matches
    if item_type == "lost":
        potential_matches = db.query(Item).filter(Item.item_type == "found", Item.status == "active").all()
    else:
        potential_matches = db.query(Item).filter(Item.item_type == "lost", Item.status == "active").all()

    for potential_match in potential_matches:
        scores = calculate_similarity_score(item if item_type == "lost" else potential_match,
                                         potential_match if item_type == "lost" else item)

        if scores['overall_score'] > 0.1:  # Threshold for suggesting matches
            match = Match(
                lost_item_id=item.id if item_type == "lost" else potential_match.id,
                found_item_id=potential_match.id if item_type == "lost" else item.id,
                similarity_score=scores['overall_score'],
                image_similarity=scores['image_similarity'],
                text_similarity=scores['text_similarity'],
                location_match=scores['location_match'],
                time_proximity=scores['time_proximity']
            )
            db.add(match)

    db.commit()

    return {"message": "Item created successfully", "item_id": item.id}

@app.get("/items/")
def get_items(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role == "staff":
        items = db.query(Item).all()
    else:
        items = db.query(Item).filter(Item.user_id == user.id).all()

    return [{"id": item.id, "item_type": item.item_type, "name": item.name,
             "description": item.description, "location": item.location,
             "date_time": item.date_time.isoformat(), "image_path": item.image_path,
             "status": item.status, "created_at": item.created_at.isoformat()} for item in items]

@app.get("/matches/")
def get_matches(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role == "staff":
        matches = db.query(Match).all()
    else:
        # Students only see matches for their items
        matches = db.query(Match).join(Item, Match.lost_item_id == Item.id).filter(Item.user_id == user.id).all()
        found_matches = db.query(Match).join(Item, Match.found_item_id == Item.id).filter(Item.user_id == user.id).all()
        matches.extend(found_matches)

    result = []
    for match in matches:
        # Ensure image similarity fields are accurate based on current item data
        scores = calculate_similarity_score(match.lost_item, match.found_item)
        needs_update = False

        if match.image_similarity_type != scores['image_similarity_type']:
            match.image_similarity_type = scores['image_similarity_type']
            needs_update = True

        if match.image_similarity != scores['image_similarity']:
            match.image_similarity = scores['image_similarity']
            needs_update = True

        if needs_update:
            db.commit()
            print(f"Updated match {match.id} image similarity -> type: {match.image_similarity_type}, value: {match.image_similarity}")

        result.append({
            "id": match.id,
            "lost_item": {
                "id": match.lost_item.id,
                "user_id": match.lost_item.user_id,
                "name": match.lost_item.name,
                "description": match.lost_item.description,
                "location": match.lost_item.location,
                "date_time": match.lost_item.date_time.isoformat(),
                "image_path": match.lost_item.image_path
            },
            "found_item": {
                "id": match.found_item.id,
                "user_id": match.found_item.user_id,
                "name": match.found_item.name,
                "description": match.found_item.description,
                "location": match.found_item.location,
                "date_time": match.found_item.date_time.isoformat(),
                "image_path": match.found_item.image_path
            },
            "similarity_score": match.similarity_score,
            "image_similarity": match.image_similarity,
            "image_similarity_type": match.image_similarity_type,
            "text_similarity": match.text_similarity,
            "location_match": match.location_match,
            "time_proximity": match.time_proximity,
            "status": match.status
        })

    return result

@app.get("/debug/matches")
def debug_matches(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    all_matches = db.query(Match).all()
    user_matches = []
    
    if user.role == "staff":
        user_matches = all_matches
    else:
        for match in all_matches:
            if match.lost_item.user_id == user.id or match.found_item.user_id == user.id:
                user_matches.append(match)

    return {
        "user_role": user.role,
        "user_id": user.id,
        "total_matches": len(all_matches),
        "user_matches": len(user_matches),
        "matches": [{
            "id": m.id,
            "lost_item": {
                "id": m.lost_item.id,
                "name": m.lost_item.name,
                "image_path": m.lost_item.image_path
            },
            "found_item": {
                "id": m.found_item.id, 
                "name": m.found_item.name,
                "image_path": m.found_item.image_path
            },
            "image_similarity_type": m.image_similarity_type
        } for m in user_matches]
    }

@app.put("/matches/{match_id}/verify")
def verify_match(match_id: int, status: str, token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Allow staff or the owner of the lost/found item
    is_owner = (match.lost_item.user_id == user.id or match.found_item.user_id == user.id)
    if not (user.role == "staff" or is_owner):
        raise HTTPException(status_code=403, detail="Only staff or item owners can verify matches")

    match.status = status
    match.verified_by = user.id

    # Update item statuses if match is verified
    if status == "verified":
        match.lost_item.status = "matched"
        match.found_item.status = "matched"

    db.commit()
    return {"message": f"Match {status} successfully"}

@app.get("/notifications/")
def get_notifications(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Get recent matches for user's items
    recent_matches = db.query(Match).filter(
        ((Match.lost_item_id.in_([item.id for item in db.query(Item).filter(Item.user_id == user.id).all()])) |
         (Match.found_item_id.in_([item.id for item in db.query(Item).filter(Item.user_id == user.id).all()])))
    ).filter(Match.created_at > datetime.utcnow() - timedelta(days=7)).all()

    notifications = []
    for match in recent_matches:
        if match.status == "suggested":
            notifications.append({
                "id": match.id,
                "type": "match_suggestion",
                "message": f"Potential match found for your {match.lost_item.item_type if match.lost_item.user_id == user.id else match.found_item.item_type} item: {match.lost_item.name if match.lost_item.user_id == user.id else match.found_item.name}",
                "similarity_score": match.similarity_score,
                "created_at": match.created_at.isoformat()
            })

    return notifications

@app.post("/match-all")
def match_all_items(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user or user.role != "staff":
        raise HTTPException(status_code=403, detail="Only staff can trigger matching")

    lost_items = db.query(Item).filter(Item.item_type == "lost", Item.status == "active").all()
    found_items = db.query(Item).filter(Item.item_type == "found", Item.status == "active").all()

    new_matches = 0
    for lost in lost_items:
        for found in found_items:
            # Check if match already exists
            existing_match = db.query(Match).filter(
                ((Match.lost_item_id == lost.id) & (Match.found_item_id == found.id))
            ).first()
            if existing_match:
                continue

            scores = calculate_similarity_score(lost, found)
            if scores['overall_score'] > 0.3:
                match = Match(
                    lost_item_id=lost.id,
                    found_item_id=found.id,
                    similarity_score=scores['overall_score'],
                    image_similarity=scores['image_similarity'],
                    image_similarity_type=scores['image_similarity_type'],
                    text_similarity=scores['text_similarity'],
                    location_match=scores['location_match'],
                    time_proximity=scores['time_proximity']
                )
                db.add(match)
                new_matches += 1

    db.commit()
    return {"message": f"Matching completed. {new_matches} new matches found."}

# Seed data
@app.post("/update-match-similarities")
def update_match_similarities(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data["sub"]).first()
    if not user or user.role != "staff":
        raise HTTPException(status_code=403, detail="Only staff can update matches")

    matches = db.query(Match).all()
    updated = 0
    
    for match in matches:
        scores = calculate_similarity_score(match.lost_item, match.found_item)
        if (match.image_similarity_type != scores['image_similarity_type'] or
            match.image_similarity != scores['image_similarity']):
            match.image_similarity = scores['image_similarity']
            match.image_similarity_type = scores['image_similarity_type']
            updated += 1
    
    db.commit()
    return {"message": f"Updated {updated} matches"}
def seed_data(db: Session = Depends(get_db)):
    try:
        # Create sample users
        student1 = db.query(User).filter(User.username == "student1").first()
        if not student1:
            # Check if email exists
            existing_email = db.query(User).filter(User.email == "student1@school.edu").first()
            if existing_email:
                email = f"student1_{datetime.utcnow().timestamp()}@school.edu"
            else:
                email = "student1@school.edu"
            student1 = User(username="student1", email=email, hashed_password=get_password_hash("password"), role="student")
            db.add(student1)
            print("Created student1")
        
        student2 = db.query(User).filter(User.username == "student2").first()
        if not student2:
            existing_email = db.query(User).filter(User.email == "student2@school.edu").first()
            if existing_email:
                email = f"student2_{datetime.utcnow().timestamp()}@school.edu"
            else:
                email = "student2@school.edu"
            student2 = User(username="student2", email=email, hashed_password=get_password_hash("password"), role="student")
            db.add(student2)
            print("Created student2")
        
        staff1 = db.query(User).filter(User.username == "staff1").first()
        if not staff1:
            existing_email = db.query(User).filter(User.email == "staff1@school.edu").first()
            if existing_email:
                email = f"staff1_{datetime.utcnow().timestamp()}@school.edu"
            else:
                email = "staff1@school.edu"
            staff1 = User(username="staff1", email=email, hashed_password=get_password_hash("password"), role="staff")
            db.add(staff1)
            print("Created staff1")
        
        db.commit()
        print("Committed users")

        # Refresh to get IDs
        student1 = db.query(User).filter(User.username == "student1").first()
        student2 = db.query(User).filter(User.username == "student2").first()

        if not student1 or not student2:
            print(f"student1: {student1}, student2: {student2}")
            return {"error": "Failed to create users"}

        print("Users created successfully")
        return {"message": "Users created successfully"}
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

    # Create sample items (without AI features for seed data)
    backpack_lost = db.query(Item).filter(Item.name == "Blue Backpack").first()
    iphone_lost = db.query(Item).filter(Item.name == "iPhone 12").first()
    backpack_found = db.query(Item).filter(Item.name == "Backpack").first()
    phone_found = db.query(Item).filter(Item.name == "Phone").first()
    
    if not backpack_lost:
        backpack_lost = Item(user_id=student1.id, item_type="lost", name="Blue Backpack", description="Nike blue backpack with school logo", location="Library", date_time=datetime.utcnow() - timedelta(days=2))
        db.add(backpack_lost)
    if not iphone_lost:
        iphone_lost = Item(user_id=student1.id, item_type="lost", name="iPhone 12", description="Black iPhone 12 with cracked screen", location="Cafeteria", date_time=datetime.utcnow() - timedelta(days=1))
        db.add(iphone_lost)
    if not backpack_found:
        backpack_found = Item(user_id=student2.id, item_type="found", name="Backpack", description="Blue backpack found near entrance", location="Main Entrance", date_time=datetime.utcnow() - timedelta(days=1))
        db.add(backpack_found)
    if not phone_found:
        phone_found = Item(user_id=student2.id, item_type="found", name="Phone", description="Black smartphone found in cafeteria", location="Cafeteria", date_time=datetime.utcnow() - timedelta(hours=12))
        db.add(phone_found)
    db.commit()

    # Get item IDs
    backpack_lost = db.query(Item).filter(Item.name == "Blue Backpack").first()
    iphone_lost = db.query(Item).filter(Item.name == "iPhone 12").first()
    backpack_found = db.query(Item).filter(Item.name == "Backpack").first()
    phone_found = db.query(Item).filter(Item.name == "Phone").first()

    if not backpack_lost or not iphone_lost or not backpack_found or not phone_found:
        return {"error": "Failed to create items"}

    # Create sample matches
    match1 = db.query(Match).filter(Match.lost_item_id == backpack_lost.id, Match.found_item_id == backpack_found.id).first()
    match2 = db.query(Match).filter(Match.lost_item_id == iphone_lost.id, Match.found_item_id == phone_found.id).first()
    
    if not match1:
        match1 = Match(lost_item_id=backpack_lost.id, found_item_id=backpack_found.id, similarity_score=0.85, image_similarity=0.0, image_similarity_type='none', text_similarity=0.8, location_match=False, time_proximity=24.0, status="suggested")
        db.add(match1)
    if not match2:
        match2 = Match(lost_item_id=iphone_lost.id, found_item_id=phone_found.id, similarity_score=0.92, image_similarity=0.0, image_similarity_type='none', text_similarity=0.9, location_match=True, time_proximity=12.0, status="suggested")
        db.add(match2)
    db.commit()

    return {"message": "Seed data created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, 
                 server_header=False,
                 log_config=None)