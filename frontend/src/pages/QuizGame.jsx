import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import GameCanvas from '../components/GameCanvas';
import QuestionCard from '../components/QuestionCard';

const QuizGame = () => {
    const { topicId } = useParams();
    const navigate = useNavigate();
    const canvasRef = useRef(null);

    const [sessionId, setSessionId] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [isGameOver, setIsGameOver] = useState(false);
    const [gameResult, setGameResult] = useState(null); // 'win' | 'lose' | 'completed'
    const [score, setScore] = useState(0);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    // Called by GameCanvas when the game ends naturally (zombie reach / all zombies dead)
    const handleGameNaturalEnd = useCallback((result) => {
        setGameResult(result);
        setIsGameOver(true);
    }, []);

    const hasStarted = useRef(false);

    useEffect(() => {
        if (hasStarted.current) return;
        hasStarted.current = true;

        const startSession = async () => {
            try {
                const res = await client.post(`/student/start-quiz?topic_id=${topicId}`);
                setSessionId(res.data.session_id);
                setCurrentQuestion(res.data.first_question);
            } catch (err) {
                console.error(err);
                alert("Failed to start quiz. Please try again.");
                navigate('/student/dashboard');
            } finally {
                setLoading(false);
            }
        };
        startSession();
    }, [topicId, navigate]);

    // Start the game only once question is ready — delay to let assets load
    useEffect(() => {
        if (!loading && currentQuestion && canvasRef.current) {
            setTimeout(() => {
                canvasRef.current?.resetGame(handleGameNaturalEnd);
            }, 300);
        }
    }, [loading]);

    const handleAnswer = async (selectedOption) => {
        if (submitting || isGameOver) return;
        setSubmitting(true);

        // We'll decide animation after server response
        // Show immediate feedback placeholder (will be updated after response)
        setFeedback({
            selected: selectedOption,
            correct: null,
            is_correct: null
        });

        try {
            const res = await client.post('/student/submit-answer', {
                session_id: sessionId,
                question_id: currentQuestion.id,
                selected_answer: selectedOption
            });

            // Update animation based on server correctness
            if (res.data.is_correct) {
                canvasRef.current?.shoot();
            } else {
                canvasRef.current?.reload();
            }

            // Update feedback with actual correctness
            setFeedback({
                selected: selectedOption,
                correct: currentQuestion.correct_answer,
                is_correct: res.data.is_correct
            });

            // Update scores
            setScore(res.data.score);
            setTotal(res.data.total_questions);

            // Wait so player can read the feedback
            setTimeout(() => {
                if (isGameOver) return; // Game ended naturally via zombie reach/win, don't do anything

                if (res.data.game_over) {
                    // 10 questions completed
                    setIsGameOver(true);
                    setGameResult('completed');
                } else {
                    setFeedback(null);
                    setCurrentQuestion(res.data.next_question);
                    setSubmitting(false);
                }
            }, 1500);
        } catch (err) {
            console.error(err);
            setFeedback(null);
            setSubmitting(false);
        }
    };

    if (loading) return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
            <div>
                <div className="loader" style={{ margin: '0 auto 1rem' }}></div>
                <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>Generating your first question...</p>
            </div>
        </div>
    );

    return (
        <div className="quiz-page">
            {/* TOP: Game Canvas */}
            <div className="game-section">
                <GameCanvas ref={canvasRef} />
                {/* Score HUD on top of game */}
                <div className="game-hud">
                    <span>🎯 Score: <strong>{score}</strong></span>
                    <span>❓ Question: <strong>{total + 1} / 10</strong></span>
                    {feedback && (
                        <span style={{ color: feedback.is_correct ? 'var(--success)' : 'var(--error)', fontWeight: 700 }}>
                            {feedback.is_correct ? '✅ Correct! Zombie hit!' : '❌ Miss! Reloading...'}
                        </span>
                    )}
                </div>
            </div>

            {/* BOTTOM: Question Panel */}
            <div className="question-section">
                {!isGameOver && currentQuestion ? (
                    <QuestionCard
                        question={currentQuestion}
                        onAnswer={handleAnswer}
                        disabled={submitting}
                        feedback={feedback}
                    />
                ) : !isGameOver ? (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                        <div className="loader"></div>
                    </div>
                ) : null}
            </div>

            {/* Game Over Modal */}
            {isGameOver && (
                <div className="modal-overlay">
                    <div className="modal">
                        {gameResult === 'win' && <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏆</div>}
                        {gameResult === 'lose' && <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💀</div>}
                        {gameResult === 'completed' && <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎓</div>}

                        <h2 style={{ color: gameResult === 'win' ? 'var(--success)' : gameResult === 'lose' ? 'var(--error)' : 'var(--accent)' }}>
                            {gameResult === 'win' && 'VICTORY!'}
                            {gameResult === 'lose' && 'OVERRUN!'}
                            {gameResult === 'completed' && 'QUIZ COMPLETE!'}
                        </h2>

                        <div className="stat-label">Final Score</div>
                        <div className="result-score">{score} / {total}</div>
                        <p style={{ color: 'var(--text-muted)' }}>
                            Accuracy: <strong style={{ color: 'var(--accent)' }}>
                                {total > 0 ? ((score / total) * 100).toFixed(1) : 0}%
                            </strong>
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1.5rem' }}>
                            <button className="auth-btn" style={{ margin: 0 }} onClick={() => navigate(`/quiz/${topicId}`)}>
                                Play Again
                            </button>
                            <button
                                className="auth-btn"
                                style={{ margin: 0, background: 'var(--panel)', border: '1px solid var(--text-muted)' }}
                                onClick={() => navigate('/student/dashboard')}
                            >
                                Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuizGame;
