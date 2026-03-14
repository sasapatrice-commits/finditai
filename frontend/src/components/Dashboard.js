import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import './Dashboard.css';

function Dashboard() {
  const [items, setItems] = useState([]);
  const [matches, setMatches] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [itemsRes, matchesRes, notificationsRes] = await Promise.all([
        axios.get('/items/'),
        axios.get('/matches/'),
        axios.get('/notifications/')
      ]);

      setItems(itemsRes.data);
      setMatches(matchesRes.data);
      setNotifications(notificationsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  const recentItems = items.slice(0, 5);
  const highMatches = matches.filter(m => m.similarity_score > 0.7).slice(0, 5);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>FindIt AI Dashboard</h1>
          <div className="user-info">
            <span>Welcome, {user.username} ({user.role})</span>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>

      <nav className="dashboard-nav">
        <Link to="/submit-item" className="nav-btn">Report Item</Link>
        <Link to="/matches" className="nav-btn">View Matches</Link>
        <Link to="/notifications" className="nav-btn">Notifications ({notifications.length})</Link>
      </nav>

      <div className="dashboard-content">
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Your Items</h3>
            <div className="stat-value">{items.length}</div>
          </div>
          <div className="stat-card">
            <h3>Potential Matches</h3>
            <div className="stat-value">{matches.length}</div>
          </div>
          <div className="stat-card">
            <h3>High Confidence Matches</h3>
            <div className="stat-value">{highMatches.length}</div>
          </div>
          <div className="stat-card">
            <h3>Notifications</h3>
            <div className="stat-value">{notifications.length}</div>
          </div>
        </div>

        <div className="dashboard-sections">
          <section className="recent-items">
            <h2>Recent Items</h2>
            {recentItems.length > 0 ? (
              <div className="items-list">
                {recentItems.map(item => (
                  <div key={item.id} className="item-card">
                    <h4>{item.name}</h4>
                    <p>{item.item_type} - {item.location}</p>
                    <small>{new Date(item.date_time).toLocaleDateString()}</small>
                  </div>
                ))}
              </div>
            ) : (
              <p>No items reported yet. <Link to="/submit-item">Report your first item</Link></p>
            )}
          </section>

          <section className="high-matches">
            <h2>High Confidence Matches</h2>
            {highMatches.length > 0 ? (
              <div className="matches-list">
                {highMatches.map(match => (
                  <div key={match.id} className="match-card">
                    <div className="match-items">
                      <div className="match-item">
                        <strong>Lost:</strong> {match.lost_item.name}
                      </div>
                      <div className="match-item">
                        <strong>Found:</strong> {match.found_item.name}
                      </div>
                    </div>
                    <div className="match-score">
                      Similarity: {(match.similarity_score * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No high confidence matches found yet.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;