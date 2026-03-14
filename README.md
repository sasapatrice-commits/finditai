# FindIt AI: Smart Lost-and-Found Matching System for Schools

A comprehensive lost-and-found system that uses AI to automatically match lost and found items on campus. The system features computer vision for image analysis and natural language processing for text similarity matching.

## Features

### Core Functionality
- **User Authentication**: Student and Staff/Admin roles with role-based access
- **Item Reporting**: Submit lost or found items with photos, descriptions, location, and timestamp
- **AI-Powered Matching**: Automatic matching using image similarity and text analysis
- **Staff Verification**: Staff can verify and approve matches
- **Notifications**: Real-time notifications for potential matches
- **Privacy Protection**: No face recognition, warnings about personal information

### AI Features
- **Computer Vision**: Pretrained ResNet model extracts visual features from item images
- **Natural Language Processing**: Sentence transformers analyze item descriptions
- **Similarity Scoring**: Combined scoring from image, text, location, and time factors

## Architecture

### Backend (FastAPI + Python)
- **Framework**: FastAPI for high-performance API
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **AI Models**:
  - PyTorch/ResNet50 for image feature extraction
  - Sentence Transformers for text similarity
- **File Storage**: Local directory for uploaded images

### Frontend (React)
- **Framework**: React with React Router
- **Styling**: Custom CSS with responsive design
- **State Management**: React Context for authentication
- **HTTP Client**: Axios for API communication

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    hashed_password VARCHAR,
    role VARCHAR,  -- 'student' or 'staff'
    created_at DATETIME
);
```

### Items Table
```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item_type VARCHAR,  -- 'lost' or 'found'
    name VARCHAR,
    description TEXT,
    location VARCHAR,
    date_time DATETIME,
    image_path VARCHAR,
    image_features TEXT,  -- JSON string of features
    text_features TEXT,   -- JSON string of features
    status VARCHAR DEFAULT 'active',  -- 'active', 'matched', 'claimed'
    created_at DATETIME
);
```

### Matches Table
```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    lost_item_id INTEGER REFERENCES items(id),
    found_item_id INTEGER REFERENCES items(id),
    similarity_score FLOAT,
    image_similarity FLOAT,
    text_similarity FLOAT,
    location_match BOOLEAN,
    time_proximity FLOAT,  -- hours difference
    status VARCHAR DEFAULT 'suggested',  -- 'suggested', 'verified', 'rejected'
    verified_by INTEGER REFERENCES users(id),
    created_at DATETIME
);
```

## AI Matching Algorithm

The matching score is calculated using a weighted combination of four factors:

### 1. Image Similarity (0-40% weight)
- Uses pretrained ResNet50 model to extract 2048-dimensional feature vectors
- Cosine similarity between lost and found item images
- Only applied when both items have images

### 2. Text Similarity (30% weight)
- Uses 'all-MiniLM-L6-v2' sentence transformer
- Compares item names and descriptions
- Cosine similarity on 384-dimensional embeddings

### 3. Location Match (20% weight)
- Binary score: 1.0 if locations match exactly, 0.0 otherwise
- Case-insensitive comparison

### 4. Time Proximity (10% weight)
- Calculates hours between reported times
- Score = max(0, 1 - (hours_diff / 24))
- Higher score for items reported closer in time

### Overall Score Formula
```
overall_score = (image_similarity × 0.4 × image_weight) +
                (text_similarity × 0.3) +
                (location_match × 0.2) +
                time_weight
```

Matches with scores > 0.3 are suggested to users.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend server**:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```
   The app will be available at `http://localhost:3000`

### Database Initialization

The database and tables are created automatically when the backend starts. To populate with sample data:

1. **Start the backend server**
2. **Make a POST request to seed data**:
   ```bash
   curl -X POST http://localhost:8000/seed-data
   ```

This creates sample users and items for testing.

## Usage

### User Registration
1. Visit `http://localhost:3000`
2. Click "Register" and create an account
3. Choose role: Student or Staff/Admin

### Reporting Items
1. Login to your account
2. Click "Report Item" from the dashboard
3. Fill in item details:
   - Type: Lost or Found
   - Name and description
   - Location and date/time
   - Optional: Upload item photo
4. Submit the report

### Viewing Matches
1. Go to "View Matches" from the dashboard
2. Filter matches by confidence level
3. Staff users can verify matches
4. High-confidence matches (>80%) are highlighted

### Staff Features
- View all reported items (not just their own)
- Verify and approve matches
- Access to all match data for resolution

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### Items
- `POST /items/` - Submit new item report
- `GET /items/` - Get user's items (or all for staff)

### Matches
- `GET /matches/` - Get potential matches
- `PUT /matches/{match_id}/verify` - Verify match (staff only)

### Notifications
- `GET /notifications/` - Get user notifications

### Development
- `POST /seed-data` - Populate with sample data

## Security Considerations

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Students see only their items, staff see all
- **Input Validation**: Server-side validation on all inputs
- **File Upload Security**: Restricted to image files only
- **Privacy Protection**: No facial recognition, clear privacy warnings

## Future Enhancements

- **Real Dataset Training**: Train custom models on school-specific lost/found data
- **Mobile App**: React Native mobile application
- **Email Notifications**: SMTP integration for email alerts
- **Advanced Matching**: Incorporate item categories and subcategories
- **Analytics Dashboard**: Detailed reporting for staff
- **Bulk Import**: CSV import for existing lost/found databases

## Testing

### Sample Test Data
After running `/seed-data`, the system includes:
- 2 sample users (student1/staff1)
- 4 sample items (2 lost, 2 found)
- Pre-calculated matches demonstrating the AI scoring

### Manual Testing
1. Register as a student and staff member
2. Submit lost/found items with and without images
3. Check automatic match generation
4. Test staff verification workflow
5. Verify notification system

## Troubleshooting

### Common Issues

**Backend won't start**:
- Ensure Python 3.8+ is installed
- Check if port 8000 is available
- Verify all dependencies are installed

**Frontend won't load**:
- Ensure Node.js 16+ is installed
- Check if port 3000 is available
- Clear browser cache and cookies

**AI matching not working**:
- Ensure PyTorch and sentence-transformers are properly installed
- Check console for AI-related errors
- Verify image processing libraries (PIL/Pillow)

**Database issues**:
- Delete `findit.db` file and restart backend to recreate
- Run seed data endpoint to populate sample data

## License

This project is developed as an educational prototype for demonstrating AI-powered matching systems in educational environments.