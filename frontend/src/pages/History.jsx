import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Calendar, Award, BookOpen } from 'lucide-react';

const History = () => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await client.get('/student/history');
                setHistory(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    if (loading) return <div className="container" style={{ textAlign: 'center', marginTop: '5rem' }}><div className="loader"></div></div>;

    return (
        <div className="container">
            <h1>Quiz History</h1>
            <p style={{ color: 'var(--text-muted)' }}>Review your survival progress over time.</p>

            <div className="card" style={{ marginTop: '2rem', overflowX: 'auto' }}>
                <table>
                    <thead>
                        <tr>
                            <th>Topic</th>
                            <th>Score</th>
                            <th>Accuracy (%)</th>
                            <th>Date</th>
                            <th>Verdict</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history.map((h) => {
                            const accuracy = ((h.score / h.total_questions) * 100).toFixed(1);
                            return (
                                <tr key={h.id}>
                                    <td><BookOpen size={16} style={{ marginRight: '0.5rem' }} /> {h.topic_name}</td>
                                    <td>{h.score} / {h.total_questions}</td>
                                    <td style={{ fontWeight: 'bold', color: accuracy > 70 ? 'var(--success)' : accuracy > 40 ? 'var(--warning)' : 'var(--error)' }}>
                                        {accuracy}%
                                    </td>
                                    <td><Calendar size={16} style={{ marginRight: '0.5rem' }} /> {new Date(h.created_at).toLocaleDateString()}</td>
                                    <td>
                                        {accuracy > 70 ? (
                                            <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                                <Award size={16} /> Mastery
                                            </span>
                                        ) : (
                                            <span style={{ color: 'var(--text-muted)' }}>Developing</span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                        {history.length === 0 && (
                            <tr>
                                <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>No history found. Start your first quiz!</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default History;
