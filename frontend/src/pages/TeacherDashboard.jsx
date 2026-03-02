import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Plus, BarChart2, Users, Target } from 'lucide-react';

const TeacherDashboard = () => {
    const [analytics, setAnalytics] = useState(null);
    const [topicName, setTopicName] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const fetchAnalytics = async () => {
        try {
            const res = await client.get('/teacher/analytics');
            setAnalytics(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const createTopic = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await client.post('/teacher/create-test', { name: topicName });
            setTopicName('');
            alert('Topic created successfully!');
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to create topic');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return <div className="container" style={{ textAlign: 'center', marginTop: '5rem' }}><div className="loader"></div></div>;

    return (
        <div className="container">
            <h1>Teacher Dashboard</h1>

            <div className="grid">
                <div className="card stats-card">
                    <BarChart2 size={32} color="var(--accent)" />
                    <div className="stat-value">{(analytics?.avg_score || 0).toFixed(1)}%</div>
                    <div className="stat-label">Average Accuracy</div>
                </div>
                <div className="card stats-card">
                    <Users size={32} color="var(--accent)" />
                    <div className="stat-value">{analytics?.total_attempts || 0}</div>
                    <div className="stat-label">Total Attempts</div>
                </div>
                <div className="card" style={{ gridColumn: 'span 1' }}>
                    <h3 style={{ marginTop: 0 }}>Create New Topic</h3>
                    <form onSubmit={createTopic}>
                        <div className="form-group">
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Topic Name (e.g. Physics)"
                                value={topicName}
                                onChange={(e) => setTopicName(e.target.value)}
                                required
                            />
                        </div>
                        <button type="submit" className="auth-btn" disabled={submitting}>
                            <Plus size={18} /> {submitting ? 'Creating...' : 'Create Topic'}
                        </button>
                    </form>
                </div>
            </div>

            <h2 style={{ marginTop: '3rem' }}>Topic-Wise Performance Breakdown</h2>
            <div className="card" style={{ marginTop: '1.5rem', overflowX: 'auto', background: 'var(--card-bg)' }}>
                <table>
                    <thead>
                        <tr>
                            <th>Topic Name</th>
                            <th>Avg. Accuracy (%)</th>
                            <th>Total Attempts</th>
                            <th>Popularity</th>
                        </tr>
                    </thead>
                    <tbody>
                        {analytics?.topic_performance.map((tp, i) => (
                            <tr key={i}>
                                <td>{tp.topic_name}</td>
                                <td style={{ fontWeight: 'bold' }}>{tp.avg_score.toFixed(1)}%</td>
                                <td>{tp.total_attempts}</td>
                                <td>
                                    <div style={{ width: '100px', height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                                        <div style={{
                                            width: `${Math.min(100, (tp.total_attempts / (analytics.total_attempts || 1)) * 100)}%`,
                                            height: '100%',
                                            background: 'var(--accent)'
                                        }}></div>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <h2 style={{ marginTop: '3rem' }}>Student Performance Ranking</h2>
            <div className="card" style={{ marginTop: '1.5rem', overflowX: 'auto' }}>
                <table>
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Avg. Score (%)</th>
                            <th>Total Attempts</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {analytics?.student_performance.map((p, i) => (
                            <tr key={i}>
                                <td>{p.username}</td>
                                <td style={{ fontWeight: 'bold', color: p.avg_score > 70 ? 'var(--success)' : p.avg_score > 40 ? 'var(--warning)' : 'var(--error)' }}>
                                    {p.avg_score.toFixed(1)}%
                                </td>
                                <td>{p.total_attempts}</td>
                                <td>
                                    {p.avg_score > 70 ? 'Elite' : p.avg_score > 40 ? 'Developing' : 'At Risk'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <h2 style={{ marginTop: '3rem' }}>Recent Quiz Activity</h2>
            <div className="card" style={{ marginTop: '1.5rem', overflowX: 'auto', marginBottom: '3rem' }}>
                <table>
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Topic</th>
                            <th>Score</th>
                            <th>Accuracy</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {analytics?.recent_responses.map((r, i) => (
                            <tr key={i}>
                                <td>{r.username}</td>
                                <td>{r.topic}</td>
                                <td>{r.score} / {r.total}</td>
                                <td style={{ fontWeight: 'bold' }}>
                                    {((r.score / r.total) * 100).toFixed(1)}%
                                </td>
                                <td>{new Date(r.date).toLocaleString()}</td>
                            </tr>
                        ))}
                        {analytics?.recent_responses.length === 0 && (
                            <tr><td colSpan="5" style={{ textAlign: 'center', padding: '1rem' }}>No recent attempts found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TeacherDashboard;
