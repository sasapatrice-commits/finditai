import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Notifications.css';

function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get('/notifications/');
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading notifications...</div>;
  }

  return (
    <div className="notifications-container">
      <header className="notifications-header">
        <h1>Notifications</h1>
        <button onClick={() => navigate('/dashboard')} className="back-btn">Back to Dashboard</button>
      </header>

      <div className="notifications-list">
        {notifications.length > 0 ? (
          notifications.map(notification => (
            <div key={notification.id} className="notification-card">
              <div className="notification-content">
                <p>{notification.message}</p>
                <div className="notification-meta">
                  <span className="notification-score">
                    Match Confidence: {(notification.similarity_score * 100).toFixed(1)}%
                  </span>
                  <span className="notification-date">
                    {new Date(notification.created_at).toLocaleDateString()} {new Date(notification.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
              <div className="notification-actions">
                <button onClick={() => navigate('/matches')} className="view-matches-btn">
                  View Matches
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="no-notifications">
            <p>No new notifications.</p>
            <p>You'll be notified when potential matches are found for your items.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Notifications;