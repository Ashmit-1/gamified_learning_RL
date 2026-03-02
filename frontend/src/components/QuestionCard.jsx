import React from 'react';

const difficultyClass = { easy: 'badge-easy', medium: 'badge-medium', hard: 'badge-hard' };

const QuestionCard = ({ question, onAnswer, disabled, feedback }) => {
    if (!question) return null;

    return (
        <div className="question-panel">
            {/* Meta badges */}
            <div className="question-meta">
                <span className={`badge ${difficultyClass[question.difficulty] || 'badge-medium'}`}>
                    {question.difficulty}
                </span>
                <span className="badge badge-type">{question.type}</span>
            </div>

            {/* Question text */}
            <h3>{question.question_text}</h3>

            {/* Options — 2-column grid */}
            <div className="options-grid">
                {question.options.map((option, index) => {
                    let className = "option-btn";
                    if (feedback && feedback.correct) {
                        if (option === feedback.correct) className += " correct";
                        else if (option === feedback.selected && !feedback.is_correct) className += " incorrect";
                    }

                    return (
                        <button
                            key={index}
                            className={className}
                            onClick={() => onAnswer(option)}
                            disabled={disabled}
                        >
                            <span style={{ fontWeight: 700, marginRight: '0.5rem', color: 'var(--text-muted)' }}>
                                {String.fromCharCode(65 + index)}.
                            </span>
                            {option}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default QuestionCard;
