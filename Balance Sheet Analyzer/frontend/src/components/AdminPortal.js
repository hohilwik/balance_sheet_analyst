import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const AdminPortal = () => {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  const fetchPendingApprovals = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/pending-approvals');
      setPendingApprovals(response.data);
    } catch (error) {
      console.error('Error fetching approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const approveCompany = async (companyId) => {
    try {
      await axios.post(`http://localhost:5000/api/admin/approve-company/${companyId}`);
      setPendingApprovals(prev => prev.filter(approval => approval.company_id !== companyId));
    } catch (error) {
      console.error('Error approving company:', error);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="admin-portal">
      <header className="admin-header">
        <h1>Admin Portal</h1>
        <div>
          <span>Welcome, {user.username}</span>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div className="approvals-section">
        <h2>Pending Company Approvals</h2>
        {pendingApprovals.length === 0 ? (
          <p>No pending approvals</p>
        ) : (
          <div className="approvals-list">
            {pendingApprovals.map(approval => (
              <div key={approval.company_id} className="approval-item">
                <div className="approval-info">
                  <h3>Company ID: {approval.company_id}</h3>
                  <p>Requested by: {approval.requested_by}</p>
                  <p>Requested at: {new Date(approval.requested_at).toLocaleString()}</p>
                </div>
                <button 
                  onClick={() => approveCompany(approval.company_id)}
                  className="approve-btn"
                >
                  Approve
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPortal;