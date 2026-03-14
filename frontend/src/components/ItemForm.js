import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ItemForm.css';

function ItemForm() {
  const [formData, setFormData] = useState({
    item_type: 'lost',
    name: '',
    description: '',
    location: '',
    date_time: '',
    image: null
  });
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({
        ...prev,
        image: file
      }));

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const submitData = new FormData();
      Object.keys(formData).forEach(key => {
        if (formData[key] !== null) {
          submitData.append(key, formData[key]);
        }
      });

      await axios.post('/items/', submitData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      navigate('/dashboard');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to submit item');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="item-form-container">
      <div className="item-form-card">
        <h1>Report {formData.item_type === 'lost' ? 'Lost' : 'Found'} Item</h1>

        <div className="privacy-warning">
          <strong>Privacy Notice:</strong> Do not upload images containing faces or personal information.
          Only upload images of the lost/found item itself.
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Item Type</label>
            <select
              name="item_type"
              value={formData.item_type}
              onChange={handleInputChange}
            >
              <option value="lost">Lost Item</option>
              <option value="found">Found Item</option>
            </select>
          </div>

          <div className="form-group">
            <label>Item Name/Type *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="e.g., Blue Backpack, iPhone 12, Water Bottle"
              required
            />
          </div>

          <div className="form-group">
            <label>Description *</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Describe the item, including color, brand, distinctive features..."
              rows="4"
              required
            />
          </div>

          <div className="form-group">
            <label>Location *</label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleInputChange}
              placeholder="e.g., Library, Cafeteria, Main Entrance"
              required
            />
          </div>

          <div className="form-group">
            <label>Date & Time *</label>
            <input
              type="datetime-local"
              name="date_time"
              value={formData.date_time}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Item Photo (Optional)</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
            />
            {imagePreview && (
              <div className="image-preview">
                <img src={imagePreview} alt="Item preview" />
              </div>
            )}
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="form-actions">
            <button type="button" onClick={() => navigate('/dashboard')} className="cancel-btn">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ItemForm;