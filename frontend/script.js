const API_URL = 'http://localhost:8000';

let questions = [];
let currentIndex = 0;
let score = 0;
let userResponses = [];

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
}

function handleAnswer(selectedOption, button) {
    const question = questions[currentIndex];
    const allButtons = optionsContainer.querySelectorAll('.option-btn');

    // Disable all buttons after selection
    allButtons.forEach(btn => btn.style.pointerEvents = 'none');

    const isCorrect = selectedOption === question.correct_answer;

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

    // Move to next question after delay
    setTimeout(() => {
        currentIndex++;
        if (currentIndex < questions.length) {
            showQuestion();
        } else {
            showResult();
        }
    }, 1500);
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
}
