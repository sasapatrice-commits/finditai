import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import './Matches.css';

function Matches() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    try {
      const response = await axios.get('/matches/');
      setMatches(response.data);
    } catch (error) {
      console.error('Error fetching matches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyMatch = async (matchId, status) => {
    // Removed staff check since backend now allows owners
    try {
      await axios.put(`/matches/${matchId}/verify?status=${status}`);
      fetchMatches(); // Refresh the list
    } catch (error) {
      console.error('Error verifying match:', error);
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          error.response?.data ||
                          error.message ||
                          'Unknown error';
      alert(`Failed to verify match: ${JSON.stringify(errorMessage)}`);
    }
  };

  const filteredMatches = matches.filter(match => {
    if (filter === 'all') return true;
    if (filter === 'high') return match.similarity_score > 0.7;
    if (filter === 'medium') return match.similarity_score > 0.5 && match.similarity_score <= 0.7;
    if (filter === 'low') return match.similarity_score <= 0.5;
    return true;
  });

  const getScoreColor = (score) => {
    if (score > 0.8) return 'high';
    if (score > 0.6) return 'medium';
    return 'low';
  };

  if (loading) {
    return <div className="loading">Loading matches...</div>;
  }

  return (
    <div className="matches-container">
      <header className="matches-header">
        <h1>Potential Matches</h1>
        <button onClick={() => navigate('/dashboard')} className="back-btn">Back to Dashboard</button>
      </header>

      <div className="matches-controls">
        <div className="filter-controls">
          <label>Filter by confidence:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Matches</option>
            <option value="high">High Confidence (&gt;80%)</option>
            <option value="medium">Medium Confidence (50-80%)</option>
            <option value="low">Low Confidence (&lt;50%)</option>
          </select>
        </div>
        <div className="matches-count">
          Showing {filteredMatches.length} of {matches.length} matches
        </div>
      </div>

      <div className="matches-list">
        {filteredMatches.length > 0 ? (
          filteredMatches.map(match => (
            <div key={match.id} className="match-card">
              <div className="match-header">
                <div className={`match-score ${getScoreColor(match.similarity_score)}`}>
                  {(match.similarity_score * 100).toFixed(1)}% Match
                </div>
                <div className="match-status">
                  Status: {match.status}
                </div>
              </div>

              <div className="match-items">
                <div className="match-item lost-item">
                  <h3>Lost Item</h3>
                  <div className="item-details">
                    <h4>{match.lost_item.name}</h4>
                    <p>{match.lost_item.description}</p>
                    <div className="item-meta">
                      <span>Location: {match.lost_item.location}</span>
                      <span>Date: {new Date(match.lost_item.date_time).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="match-divider">
                  <span>↔</span>
                </div>

                <div className="match-item found-item">
                  <h3>Found Item</h3>
                  <div className="item-details">
                    <h4>{match.found_item.name}</h4>
                    <p>{match.found_item.description}</p>
                    <div className="item-meta">
                      <span>Location: {match.found_item.location}</span>
                      <span>Date: {new Date(match.found_item.date_time).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="match-details">
                <div className="detail-row">
                  <span>Text Similarity: {(match.text_similarity * 100).toFixed(1)}%</span>
                  <span>Image Similarity: {
                    match.image_similarity_type === 'ai' ? (match.image_similarity * 100).toFixed(1) + '%' :
                    match.image_similarity_type === 'basic' ? 'Basic comparison' :
                    'No images'
                  }</span>
                </div>
                <div className="detail-row">
                  <span>Location Match: {match.location_match ? 'Yes' : 'No'}</span>
                  <span>Time Proximity: {match.time_proximity.toFixed(1)} hours</span>
                </div>
              </div>

              {(user.role === 'staff' || match.lost_item.user_id === user.id || match.found_item.user_id === user.id) && match.status === 'suggested' && (
                <div className="match-actions">
                  <button
                    onClick={() => handleVerifyMatch(match.id, 'verified')}
                    className="verify-btn"
                  >
                    Verify Match
                  </button>
                  <button
                    onClick={() => handleVerifyMatch(match.id, 'rejected')}
                    className="reject-btn"
                  >
                    Reject Match
                  </button>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="no-matches">
            <p>No matches found with the current filter.</p>
            <p>Try adjusting the filter or check back later for new matches.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Matches;