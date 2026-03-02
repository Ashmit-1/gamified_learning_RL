import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { Play, Trophy, BookOpen, Clock, Search, Plus } from 'lucide-react';
import { authStore } from '../state/authStore';

const StudentDashboard = () => {
    const [topics, setTopics] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [customTopic, setCustomTopic] = useState('');
    const [creating, setCreating] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [topicsRes, statsRes] = await Promise.all([
                    client.get('/student/topics'),
                    client.get('/student/dashboard')
                ]);
                setTopics(topicsRes.data);
                setStats(statsRes.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const startQuiz = (topicId) => {
        navigate(`/quiz/${topicId}`);
    };

    // Student can type any topic — backend will create it if it doesn't exist
    const handleCustomTopic = async (e) => {
        e.preventDefault();
        const name = customTopic.trim();
        if (!name) return;
        setCreating(true);
        try {
            // Try to find existing topic first
            let found = topics.find(t => t.name.toLowerCase() === name.toLowerCase());
            if (!found) {
                // Create the topic (students can also create topics via /student/create-topic)
                const res = await client.post('/student/create-topic', { name });
                found = res.data;
                setTopics(prev => [...prev, found]);
            }
            navigate(`/quiz/${found.id}`);
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.detail || 'Could not create topic. Please retry.');
        } finally {
            setCreating(false);
        }
    };

    if (loading) return (
        <div className="container" style={{ textAlign: 'center', marginTop: '5rem' }}>
            <div className="loader" style={{ margin: '0 auto' }}></div>
        </div>
    );

    return (
        <div className="container">
            <h1 style={{ marginBottom: '0.25rem' }}>
                Welcome back, <span style={{ color: 'var(--accent)' }}>{authStore.getUser()}</span> 👋
            </h1>
            <p style={{ color: 'var(--text-muted)', marginTop: 0 }}>
                Choose a topic below or enter your own to begin a survival training session.
            </p>

            {/* Stats Row */}
            <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="card stats-card">
                    <Trophy size={28} color="var(--accent)" />
                    <div className="stat-value">{stats?.avg_score.toFixed(1) ?? '0.0'}</div>
                    <div className="stat-label">Average Score</div>
                </div>
                <div className="card stats-card">
                    <Clock size={28} color="var(--accent)" />
                    <div className="stat-value">{stats?.total_quizzes ?? 0}</div>
                    <div className="stat-label">Quizzes Completed</div>
                </div>
                <div className="card stats-card">
                    <BookOpen size={28} color="var(--accent)" />
                    <div className="stat-value">{stats?.topics_covered ?? 0}</div>
                    <div className="stat-label">Topics Explored</div>
                </div>
            </div>

            {/* Custom topic entry */}
            <div className="card" style={{ marginTop: '2.5rem', background: 'linear-gradient(135deg, #1e293b, #312e81)' }}>
                <h3 style={{ marginTop: 0 }}>
                    <Search size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                    Start a Quiz on Any Topic
                </h3>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Type any subject — Mathematics, Quantum Physics, World War II, Python, etc.
                    The AI will adapt questions to your level.
                </p>
                <form onSubmit={handleCustomTopic} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <input
                        type="text"
                        className="form-input"
                        style={{ flex: 1, margin: 0 }}
                        placeholder="e.g. Linear Algebra, Machine Learning, Thermodynamics..."
                        value={customTopic}
                        onChange={e => setCustomTopic(e.target.value)}
                    />
                    <button
                        type="submit"
                        className="auth-btn"
                        style={{ width: 'auto', whiteSpace: 'nowrap', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                        disabled={creating || !customTopic.trim()}
                    >
                        <Plus size={18} />
                        {creating ? 'Starting...' : 'Start Quiz'}
                    </button>
                </form>
            </div>

            {/* Topic Grid */}
            <h2 style={{ marginTop: '2.5rem' }}>Quick-Start Topics</h2>
            <div className="grid">
                {topics.map(topic => (
                    <div key={topic.id} className="card topic-card">
                        <div className="topic-icon">📚</div>
                        <h3 style={{ margin: '0.5rem 0' }}>{topic.name}</h3>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                            RL-adaptive questions that scale with your mastery.
                        </p>
                        <button
                            className="auth-btn"
                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', margin: 0 }}
                            onClick={() => startQuiz(topic.id)}
                        >
                            <Play size={16} /> Start Training
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default StudentDashboard;
