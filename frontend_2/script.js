const API_URL = 'http://localhost:8000';

// Session state for RL-based quiz
let sessionId = null;
let currentQuestion = null;
let score = 0;
let questionCount = 0;
let totalQuestions = 10;
let userResponses = [];

// Game Variables
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
let gameActive = false;
let hurdle = null;
let player = {
    x: 50,
    y: 100,
    width: 30,
    height: 30,
    dy: 0,
    jumpForce: -12,
    gravity: 0.6,
    isJumping: false,
    groundY: 100,
    isHit: false
};

// DOM Elements
const startScreen = document.getElementById('start-screen');
const loadingScreen = document.getElementById('loading-screen');
const quizScreen = document.getElementById('quiz-screen');
const resultScreen = document.getElementById('result-screen');
const topicInput = document.getElementById('topic-input');
const startBtn = document.getElementById('start-btn');
const restartBtn = document.getElementById('restart-btn');
const reviewBtn = document.getElementById('review-btn');
const reviewSection = document.getElementById('review-section');
const reviewContainer = document.getElementById('review-container');
const questionText = document.getElementById('question-text');
const optionsContainer = document.getElementById('options-container');
const progressText = document.getElementById('progress-text');
const progressFill = document.getElementById('progress-fill');
const currentScoreSpan = document.getElementById('current-score');
const finalScore = document.getElementById('final-score');
const totalQuestionsSpan = document.getElementById('total-questions');
const feedbackText = document.getElementById('feedback-text');
const nextIterBtn = document.getElementById('next-iter-btn');


// Event Listeners
startBtn.addEventListener('click', startQuiz);
nextIterBtn.addEventListener('click', () => {
    resultScreen.classList.add('hidden');
    startQuiz();
});
restartBtn.addEventListener('click', resetQuiz);
reviewBtn.addEventListener('click', toggleReview);


// Game functions
function initGame() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    player.groundY = canvas.height - 40;
    player.y = player.groundY;
    gameActive = true;
    requestAnimationFrame(updateGame);
}

function spawnHurdle() {
    hurdle = {
        x: canvas.width,
        y: canvas.height - 40,
        width: 15,
        height: 30,
        speed: 5,
        passed: false,
        triggered: false,
        isMoving: true,
        outcome: null
    };
}

function updateGame() {
    if (!gameActive) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Floor
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height - 10);
    ctx.lineTo(canvas.width, canvas.height - 10);
    ctx.stroke();

    // Player Physics
    if (player.isJumping) {
        player.dy += player.gravity;
        player.y += player.dy;
        if (player.y >= player.groundY) {
            player.y = player.groundY;
            player.isJumping = false;
            player.dy = 0;
        }
    }

    // Draw Player
    ctx.fillStyle = player.isHit ? '#ef4444' : '#6366f1';
    ctx.shadowBlur = 15;
    ctx.shadowColor = player.isHit ? '#ef4444' : '#6366f1';
    ctx.fillRect(player.x, player.y, player.width, player.height);
    ctx.shadowBlur = 0;

    // Hurdle Logic
    if (hurdle) {
        if (hurdle.isMoving) {
            hurdle.x -= hurdle.speed;

            // Stop near the player if hasn't been answered yet
            if (!hurdle.outcome && hurdle.x < player.x + 170) {
                hurdle.x = player.x + 170;
                hurdle.isMoving = false;
            }
        }

        // Draw Hurdle
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(hurdle.x, hurdle.y, hurdle.width, hurdle.height);

        // Check for trigger point
        if (hurdle.isMoving && hurdle.x < player.x + 80 && !hurdle.triggered && hurdle.outcome) {
            hurdle.triggered = true;
            if (hurdle.outcome === 'jump') {
                jump();
            }
        }

        // Collision Check
        if (hurdle.isMoving && hurdle.x < player.x + player.width &&
            hurdle.x + hurdle.width > player.x &&
            hurdle.y < player.y + player.height &&
            !hurdle.passed) {

            if (!player.isJumping) {
                player.isHit = true;
                setTimeout(() => player.isHit = false, 500);
                hurdle.passed = true;
            }
        }

        if (hurdle.x + hurdle.width < 0) {
            hurdle = null;
        }
    }

    if (gameActive) {
        requestAnimationFrame(updateGame);
    }
}

function jump() {
    if (!player.isJumping) {
        player.isJumping = true;
        player.dy = player.jumpForce;
    }
}

// RL Quiz Functions
// RL Quiz Functions
async function startQuiz() {
    let topic = topicInput.value.trim();

    // Check local storage if no input
    if (!topic) {
        topic = localStorage.getItem('current_topic');
    }

    if (!topic) {
        alert('Please enter a topic!');
        return;
    }

    // Save topic
    localStorage.setItem('current_topic', topic);

    console.log('[Frontend] Starting quiz for topic:', topic);

    startScreen.classList.add('hidden');
    loadingScreen.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/start-quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic }),
        });

        if (!response.ok) {
            throw new Error('Failed to start quiz');
        }

        const data = await response.json();
        sessionId = data.session_id;
        currentQuestion = data.question;

        // Initialize quiz state
        score = 0;
        questionCount = 1;
        userResponses = [];
        currentScoreSpan.textContent = '0';

        loadingScreen.classList.add('hidden');
        quizScreen.classList.remove('hidden');
        reviewSection.classList.add('hidden');

        initGame();
        showQuestion(currentQuestion);

    } catch (error) {
        console.error('[Frontend] Error in startQuiz:', error);
        alert('An error occurred while starting the quiz. Check if the backend is running.');
        resetQuiz("startQuiz_error");
    }
}

function showQuestion(question) {
    questionText.textContent = question.text;
    progressText.textContent = `Question ${questionCount} of ${totalQuestions}`;
    progressFill.style.width = `${(questionCount / totalQuestions) * 100}%`;

    optionsContainer.innerHTML = '';
    question.options.forEach(option => {
        const button = document.createElement('button');
        button.textContent = option;
        button.classList.add('option-btn');
        button.addEventListener('click', () => handleAnswer(option, button));
        optionsContainer.appendChild(button);
    });

    spawnHurdle();
}

async function handleAnswer(selectedOption, button) {
    const allButtons = optionsContainer.querySelectorAll('.option-btn');

    // Disable all buttons
    allButtons.forEach(btn => btn.style.pointerEvents = 'none');

    const isCorrect = selectedOption === currentQuestion.correct_answer;

    // Set game outcome
    if (hurdle) {
        hurdle.outcome = isCorrect ? 'jump' : 'hit';
        hurdle.isMoving = true;
    }

    // Save response
    userResponses.push({
        question: currentQuestion.text,
        selected: selectedOption,
        correct: currentQuestion.correct_answer,
        isCorrect: isCorrect
    });

    if (isCorrect) {
        score++;
        currentScoreSpan.textContent = score;
        button.classList.add('correct');
    } else {
        button.classList.add('wrong');
        // Show correct answer
        allButtons.forEach(btn => {
            if (btn.textContent === currentQuestion.correct_answer) {
                btn.classList.add('correct');
            }
        });
    }

    // Submit answer to backend
    try {
        const response = await fetch(`${API_URL}/submit-answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                answer: selectedOption,
                question_id: currentQuestion.id
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to submit answer');
        }

        const data = await response.json();
        console.log('[Frontend] Submit response:', data);

        // Wait for game animation
        setTimeout(() => {
            try {
                if (data.quiz_complete) {
                    console.log('[Frontend] Quiz complete! Showing results...');
                    console.log('[Frontend] Summary:', data.summary);
                    gameActive = false;
                    showResult(data.summary);
                } else {
                    questionCount++;
                    currentQuestion = data.next_question;
                    showQuestion(currentQuestion);
                }
            } catch (err) {
                console.error('[Frontend] Error in setTimeout callback:', err);
            }
        }, 2000);

    } catch (error) {
        console.error('[Frontend] Error submitting answer:', error);
        alert('Error submitting answer. Please try again.');
    }
}

function showResult(summary) {
    console.log('[Frontend] showResult called with:', summary);

    // Safety check
    if (!summary) {
        console.error('[Frontend] showResult: summary is null/undefined!');
        // Fall back to local data
        summary = {
            correct_answers: score,
            questions_answered: questionCount,
            accuracy: score / questionCount,
            learning_maturity: 'Unknown',
            epsilon: 0
        };
    }

    quizScreen.classList.add('hidden');
    resultScreen.classList.remove('hidden');
    console.log('[Frontend] Result screen should now be visible');

    finalScore.textContent = summary.correct_answers || score;
    totalQuestionsSpan.textContent = summary.questions_answered || questionCount;

    const accuracy = ((summary.accuracy || 0) * 100).toFixed(1);
    const epsilon = summary.epsilon ? summary.epsilon.toFixed(3) : '0.000';
    const maturity = summary.learning_maturity || 'Unknown';

    feedbackText.innerHTML = `
        Accuracy: ${accuracy}%<br>
        RL Maturity: <strong>${maturity}</strong><br>
        Current ε (Exploration): ${epsilon}
    `;

    buildReview();
}


function buildReview() {
    reviewContainer.innerHTML = '';
    userResponses.forEach((res, index) => {
        const item = document.createElement('div');
        item.className = `review-item ${res.isCorrect ? 'correct' : 'wrong'}`;

        item.innerHTML = `
            <span class="review-q">${index + 1}. ${res.question}</span>
            <div class="review-ans">Your Answer: <span class="${res.isCorrect ? 'text-success' : 'text-error'}">${res.selected}</span></div>
            ${!res.isCorrect ? `<div class="review-ans">Correct Answer: <span class="text-success">${res.correct}</span></div>` : ''}
        `;
        reviewContainer.appendChild(item);
    });
}

function toggleReview() {
    const isHidden = reviewSection.classList.contains('hidden');
    if (isHidden) {
        reviewSection.classList.remove('hidden');
        reviewBtn.textContent = 'Hide Review';
        setTimeout(() => {
            reviewSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    } else {
        reviewSection.classList.add('hidden');
        reviewBtn.textContent = 'Review Answers';
    }
}

function resetQuiz(reason = "user_action") {
    console.log('[Frontend] Resetting quiz. Reason:', reason);
    localStorage.removeItem('current_topic');

    resultScreen.classList.add('hidden');
    loadingScreen.classList.add('hidden');
    quizScreen.classList.add('hidden');

    startScreen.classList.remove('hidden');

    topicInput.value = '';
    gameActive = false;
    sessionId = null;
    currentQuestion = null;
}
