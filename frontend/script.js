const API_URL = 'http://localhost:8000';

let questions = [];
let currentIndex = 0;
let score = 0;
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

// Event Listeners
startBtn.addEventListener('click', generateQuiz);
restartBtn.addEventListener('click', resetQuiz);
reviewBtn.addEventListener('click', toggleReview);

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
        isMoving: true, // Start moving immediately
        outcome: null // 'jump' or 'hit'
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

        // Check for trigger point (near player)
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
            // Hurdle has finished its turn
            setTimeout(proceedToNextQuestion, 500);
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


async function generateQuiz() {
    const topic = topicInput.value.trim();
    if (!topic) {
        alert('Please enter a topic!');
        return;
    }

    startScreen.classList.add('hidden');
    loadingScreen.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/generate-quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic }),
        });

        if (!response.ok) {
            throw new Error('Failed to generate quiz');
        }

        const data = await response.json();
        questions = data.questions;
        startQuiz();
    } catch (error) {
        console.error(error);
        alert('An error occurred while generating the quiz. Check if the backend is running and configured.');
        resetQuiz();
    }
}

function startQuiz() {
    currentIndex = 0;
    score = 0;
    userResponses = [];
    currentScoreSpan.textContent = '0';
    loadingScreen.classList.add('hidden');
    quizScreen.classList.remove('hidden');
    reviewSection.classList.add('hidden');

    initGame();
    showQuestion();
}


function showQuestion() {
    const question = questions[currentIndex];
    questionText.textContent = question.text;
    progressText.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
    progressFill.style.width = `${((currentIndex + 1) / questions.length) * 100}%`;

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


function handleAnswer(selectedOption, button) {
    const question = questions[currentIndex];
    const allButtons = optionsContainer.querySelectorAll('.option-btn');

    // Disable all buttons after selection
    allButtons.forEach(btn => btn.style.pointerEvents = 'none');

    const isCorrect = selectedOption === question.correct_answer;

    // Set game outcome and start movement
    if (hurdle) {
        hurdle.outcome = isCorrect ? 'jump' : 'hit';
        hurdle.isMoving = true;
    }

    // Save response
    userResponses.push({
        question: question.text,
        selected: selectedOption,
        correct: question.correct_answer,
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
            if (btn.textContent === question.correct_answer) {
                btn.classList.add('correct');
            }
        });
    }
}

function proceedToNextQuestion() {
    currentIndex++;
    if (currentIndex < questions.length) {
        showQuestion();
    } else {
        gameActive = false;
        showResult();
    }
}



function showResult() {
    quizScreen.classList.add('hidden');
    resultScreen.classList.remove('hidden');
    finalScore.textContent = score;
    totalQuestionsSpan.textContent = questions.length;

    // Build Review UI
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
        // Scroll to review
        setTimeout(() => {
            reviewSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    } else {
        reviewSection.classList.add('hidden');
        reviewBtn.textContent = 'Review Answers';
    }
}

function resetQuiz() {
    resultScreen.classList.add('hidden');
    loadingScreen.classList.add('hidden');
    quizScreen.classList.add('hidden');
    startScreen.classList.remove('hidden');
    topicInput.value = '';
    gameActive = false;
}

