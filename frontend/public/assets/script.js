const API_URL = 'http://localhost:8000';

// Session state
let sessionId = null;
let currentQuestion = null;
let score = 0;
let questionCount = 0;
let userResponses = [];

// Unified state management
const sessionState = {
    rlProgress: { 
        currentQuestion: null,
        sessionActive: true,
        questionCount: 0,
        quizComplete: false
    },
    gameState: { 
        playerAlive: true,
        zombiesRemaining: 3,
        gameOver: false
    },
    gameFlow: { 
        waitingForAnimation: false,
        readyForNext: true
    }
};

/**************** GAME ENGINE ****************/

const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');

let gameActive = false;
let lastTime = 0;

/******** Background Music ********/
const bgMusic = new Audio("static/music.mp3");
bgMusic.loop = true;
bgMusic.volume = 0.5; // adjust 0–1

/******** Result Screens ********/
const winImg = new Image();
winImg.src = "static/ui/win.png";

const diedImg = new Image();
diedImg.src = "static/ui/died.png";

let gameResult = null; // "win" or "lose"
let pendingLose = false;

/******** Background ********/
const bgImg = new Image();
bgImg.src = "static/background/bg.png";

/******** Soldier ********/
const soldierAnimations = {
    idle: new Image(),
    shoot: new Image(),
    reload: new Image(),
    dead: new Image()
};

soldierAnimations.idle.src = "static/soldier/idle.png";
soldierAnimations.shoot.src = "static/soldier/shoot.png";
soldierAnimations.reload.src = "static/soldier/reload.png";
soldierAnimations.dead.src = "static/soldier/dead.png";

const soldier = {
    x: 40,
    y: 0,
    width: 240,
    height: 240,
    groundOffset: 10,
    state: "idle",
    frame: 0,
    frameTimer: 0,
    frameCount: { idle: 7, shoot: 4, reload: 13, dead: 4 }
};

/******** Zombies ********/
const zombieSprites = {};

for (let i = 1; i <= 3; i++) {
    zombieSprites[i] = {
        walk: new Image(),
        hurt: new Image(),
        attack: new Image(),
        dead: new Image()
    };

    zombieSprites[i].walk.src = `static/zombie/${i}/walk.png`;
    zombieSprites[i].hurt.src = `static/zombie/${i}/hurt.png`;
    zombieSprites[i].attack.src = `static/zombie/${i}/attack.png`;
    zombieSprites[i].dead.src = `static/zombie/${i}/dead.png`;
}

const frameCounts = {
    1: { walk: 10, hurt: 4, attack: 5, dead: 5 },
    2: { walk: 10, hurt: 4, attack: 4, dead: 5 },
    3: { walk: 12, hurt: 4, attack: 10, dead: 5 }
};

let zombies = [];
let zombieSpeed = 0;

function spawnZombie() {
    zombies = [];

    const spacing = 120;
    const hpValues = [2, 3, 2];

    for (let i = 0; i < 3; i++) {
        zombies.push({
            id: i + 1,
            x: canvas.width - 80 +
                i * spacing +
                (Math.random() * 60 - 30),
            hp: hpValues[i],
            state: "walk",
            frame: Math.floor(Math.random() * 8),
            frameTimer: Math.random() * 0.2,
            speedFactor: 0.85 + Math.random() * 0.35
        });
    }

    const travelDistance =
        zombies[0].x - soldier.x - 20;

    zombieSpeed = travelDistance / 30;
}

/******** Game Loop ********/
function initGame() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    bgMusic.currentTime = 0;
    bgMusic.play().catch(() => { });

    soldier.y =
        canvas.height - soldier.height - soldier.groundOffset;
    soldier.state = "idle";
    soldier.frame = 0;

    spawnZombie();

    gameActive = true;
    gameResult = null;
    pendingLose = false;
    lastTime = performance.now();
    requestAnimationFrame(updateGame);
}

function updateGame(timestamp) {
    if (!gameActive) return;

    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    /* ---------- WIN SCREEN ---------- */
    if (gameResult === "win") {
        bgMusic.pause();

        if (winImg.complete) {
            ctx.drawImage(
                winImg,
                0,
                0,
                canvas.width,
                canvas.height
            );
        }
        return;
    }

    /* ---------- LOSE SCREEN ---------- */
    if (gameResult === "lose") {
        bgMusic.pause();

        if (diedImg.complete) {
            ctx.drawImage(
                diedImg,
                0,
                0,
                canvas.width,
                canvas.height
            );
        }
        return;
    }

    /* ---------- NORMAL GAME ---------- */
    if (bgImg.complete) {
        ctx.drawImage(
            bgImg,
            0,
            0,
            canvas.width,
            canvas.height
        );
    }

    updateSoldier(dt);
    drawSoldier();

    updateZombie(dt);
    drawZombie();

    requestAnimationFrame(updateGame);
}

/******** Soldier ********/
function updateSoldier(dt) {
    const maxFrames =
        soldier.frameCount[soldier.state];

    const animSpeed =
        soldier.state === "dead" ? 0.25 : 0.12;

    soldier.frameTimer += dt;

    if (soldier.frameTimer > animSpeed) {
        soldier.frameTimer = 0;

        if (
            soldier.state === "dead" &&
            soldier.frame >= maxFrames - 1
        ) {
            soldier.frame = maxFrames - 1;

            if (pendingLose) {
                console.log("Soldier died! Game over.");
                gameResult = "lose";
                sessionState.gameState.gameOver = true;
                sessionState.rlProgress.sessionActive = false;
                pendingLose = false;
                setTimeout(() => showResult(), 1500);
            }

            return;
        }

        soldier.frame++;

        if (soldier.frame >= maxFrames) {
            if (soldier.state !== "dead") {
                soldier.state = "idle";
                soldier.frame = 0;
            } else {
                soldier.frame = maxFrames - 1;
            }
        }
    }
}

function drawSoldier() {
    const img = soldierAnimations[soldier.state];
    if (!img.width) return;

    const fw =
        img.width / soldier.frameCount[soldier.state];

    ctx.drawImage(
        img,
        soldier.frame * fw,
        0,
        fw,
        img.height,
        soldier.x,
        soldier.y,
        soldier.width,
        soldier.height
    );
}

/******** Zombies ********/
function updateZombie(dt) {

    zombies.forEach(z => {

        const counts = frameCounts[z.id];
        const animSpeed =
            z.state === "dead" ? 0.3 : 0.15;

        z.frameTimer += dt;
        let stepMove = false;

        if (z.frameTimer > animSpeed) {
            z.frameTimer = 0;

            const maxFrames = counts[z.state];

            if (z.state === "dead") {
                if (z.frame > 0) z.frame--;
            }
            else {
                z.frame++;

                if (z.frame >= maxFrames) {
                    if (z.state === "hurt")
                        z.state = "walk";

                    z.frame = 0;
                }

                if (z.state === "walk")
                    stepMove = true;
            }
        }

        if (stepMove) {
            const stepDistance =
                zombieSpeed * animSpeed * z.speedFactor;
            z.x -= stepDistance;
        }

        if (
            z.state === "walk" &&
            z.x < soldier.x + 90 &&
            soldier.state !== "dead"
        ) {
            console.log("Zombie reached soldier! Game over imminent.");
            z.state = "attack";
            z.frame = 0;
            soldier.state = "dead";
            soldier.frame = 0;

            pendingLose = true;
            sessionState.gameState.playerAlive = false;
        }

        if (z.hp <= 0 &&
            z.state !== "dead") {
            z.state = "dead";
            z.frame = counts.dead - 1;
        }
    });

    // Check Win Condition: All zombies dead
    const aliveZombies = zombies.filter(z => z.hp > 0).length;
    if (aliveZombies === 0 && gameResult === null && !pendingLose) {
        // Player has killed all zombies - game win
        console.log("All zombies defeated! Game win.");
        gameResult = "win";
        sessionState.gameState.gameOver = true;
        sessionState.rlProgress.sessionActive = false;
        setTimeout(() => showResult(), 1500);
    }
}

function drawZombie() {
    zombies.forEach(z => {

        const img =
            zombieSprites[z.id][z.state];

        if (!img.complete) return;

        const frameCount =
            frameCounts[z.id][z.state];

        const fw = img.width / frameCount;
        const fh = img.height;

        const scale = 1.6;

        const drawW = fw * scale;
        const drawH = fh * scale;

        const groundY = canvas.height - 15;
        const drawY = groundY - drawH;

        ctx.drawImage(
            img,
            z.frame * fw,
            0,
            fw,
            fh,
            z.x,
            drawY,
            drawW,
            drawH
        );
    });
}

/******** Combat ********/
function soldierShoot() {

    if (soldier.state === "dead") return;

    soldier.state = "shoot";
    soldier.frame = 0;

    const target =
        zombies.find(z => z.hp > 0);

    if (!target) return;

    target.hp--;

    if (target.hp > 0) {
        target.state = "hurt";
        target.frame = 0;
    }
}

function soldierReload() {
    if (soldier.state === "dead") return;
    soldier.state = "reload";
    soldier.frame = 0;
}


/* ================= QUIZ LOGIC ================= */

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

startBtn.addEventListener('click', generateQuiz);
restartBtn.addEventListener('click', resetQuiz);
reviewBtn.addEventListener('click', toggleReview);

async function generateQuiz() {
    const topic = topicInput.value.trim();
    if (!topic) return alert('Enter topic!');

    startScreen.classList.add('hidden');
    loadingScreen.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/start-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });

        if (!response.ok) throw new Error('Start quiz failed');

        const data = await response.json();
        sessionId = data.session_id;
        currentQuestion = data.question;

        startQuiz();
    } catch (err) {
        console.error(err);
        alert("Quiz generation failed. Check if backend is running.");
        resetQuiz();
    }
}

function startQuiz() {
    score = 0;
    questionCount = 1;
    userResponses = [];

    currentScoreSpan.textContent = '0';

    loadingScreen.classList.add('hidden');
    quizScreen.classList.remove('hidden');

    initGame();
    renderQuestion(currentQuestion);
}

function renderQuestion(q) {
    if (!q) return;

    questionText.textContent = q.text;
    progressText.textContent = `Survival Progress: Question ${questionCount}`;
    progressFill.style.width = `100%`;

    optionsContainer.innerHTML = '';

    q.options.forEach(option => {
        const btn = document.createElement('button');
        btn.textContent = option;
        btn.classList.add('option-btn');
        btn.onclick = () => handleAnswer(option, btn);
        optionsContainer.appendChild(btn);
    });
}

// Helper function to wait for animation completion
function waitForAnimationCompletion() {
    return new Promise(resolve => {
        const checkAnimation = () => {
            // Check if soldier is in idle state (animation complete)
            if (soldier.state === "idle" || soldier.state === "dead") {
                resolve();
            } else {
                // Check again in 100ms
                setTimeout(checkAnimation, 100);
            }
        };
        
        // Start checking after a small delay to ensure animation starts
        setTimeout(checkAnimation, 100);
    });
}

// Function to notify backend when game actually ends
async function notifyGameEnd(result) {
    if (!sessionId) {
        console.log("No session ID, skipping game end notification");
        return;
    }
    
    console.log(`Notifying backend that game ended with result: ${result}`);
    try {
        const response = await fetch(`${API_URL}/game-over`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                game_result: result
            })
        });
        
        if (response.ok) {
            console.log("Successfully notified backend of game end");
        } else {
            console.error("Failed to notify backend of game end:", response.status);
        }
    } catch (err) {
        console.error("Error notifying game end:", err);
    }
}

async function handleAnswer(selectedOption, button) {
    const allButtons = optionsContainer.querySelectorAll('.option-btn');
    allButtons.forEach(b => b.style.pointerEvents = 'none');

    const isCorrect = selectedOption === currentQuestion.correct_answer;

    // Game Action - trigger immediately
    if (isCorrect) {
        soldierShoot();
        score++;
        currentScoreSpan.textContent = score;
        button.classList.add('correct');
    } else {
        soldierReload();
        button.classList.add('wrong');
        allButtons.forEach(b => {
            if (b.textContent === currentQuestion.correct_answer)
                b.classList.add('correct');
        });
    }

    // Save for review
    userResponses.push({
        question: currentQuestion.text,
        selected: selectedOption,
        correct: currentQuestion.correct_answer,
        isCorrect: isCorrect
    });

    // Backend Submit - don't block on game animations
    try {
        const response = await fetch(`${API_URL}/submit-answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                answer: selectedOption,
                question_id: currentQuestion.id || ""
            })
        });

        const data = await response.json();
        
        // Wait for game animation to complete before proceeding
        await waitForAnimationCompletion();

        // Always continue with next question since game goes on until actual end
        if (data.next_question && !sessionState.gameState.gameOver && gameResult === null) {
            questionCount++;
            currentQuestion = data.next_question;
            renderQuestion(currentQuestion);
        } else if (!sessionState.gameState.gameOver && gameResult === null) {
            // Handle case where no next question but game isn't over
            console.warn("No next question received but game not over");
            // Continue with current setup
            renderQuestion(currentQuestion);
        }

    } catch (err) {
        console.error("Error submitting answer:", err);
        // Even if backend fails, wait for animation to complete
        await waitForAnimationCompletion();
        
        // Continue gameplay if game isn't visually ended
        if (!sessionState.gameState.gameOver && gameResult === null) {
            // Try to get next question or show error
            console.log("Attempting to continue despite backend error...");
        }
    }
}

function showResult(summary = null) {
    gameActive = false;
    quizScreen.classList.add('hidden');
    resultScreen.classList.remove('hidden');

    finalScore.textContent = score;
    totalQuestionsSpan.textContent = questionCount;

    const outcomeText = gameResult === "win" ? "VICTORY! All zombies eliminated." : "GAME OVER! The gunman has fallen.";
    feedbackText.innerHTML = `${outcomeText}<br>Accuracy: ${((score / questionCount) * 100).toFixed(1)}%`;

    // Notify backend that game is actually over
    notifyGameEnd(gameResult);
    
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
    reviewSection.classList.toggle('hidden');
}

function resetQuiz() {
    bgMusic.pause();
    resultScreen.classList.add('hidden');
    quizScreen.classList.add('hidden');
    startScreen.classList.remove('hidden');
    reviewSection.classList.add('hidden');

    topicInput.value = '';
    gameActive = false;
    gameResult = null;
    pendingLose = false;
    
    // Reset session state
    sessionState.rlProgress = { 
        currentQuestion: null,
        sessionActive: true,
        questionCount: 0,
        quizComplete: false
    };
    sessionState.gameState = { 
        playerAlive: true,
        zombiesRemaining: 3,
        gameOver: false
    };
    sessionState.gameFlow = { 
        waitingForAnimation: false,
        readyForNext: true
    };
    
    // Reset game variables
    sessionId = null;
    currentQuestion = null;
    score = 0;
    questionCount = 0;
    userResponses = [];
    currentScoreSpan.textContent = '0';
}
