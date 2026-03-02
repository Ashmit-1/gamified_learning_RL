import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';

const GameCanvas = forwardRef((props, ref) => {
    const canvasRef = useRef(null);
    const onGameEndRef = useRef(null); // callback passed in via resetGame()

    const gameRef = useRef({
        ctx: null,
        gameActive: false,
        lastTime: 0,
        soldier: {
            x: 40,
            y: 0,
            width: 200,
            height: 200,
            state: "idle",
            frame: 0,
            frameTimer: 0,
            frameCount: { idle: 7, shoot: 4, reload: 13, dead: 4 }
        },
        zombies: [],
        zombieSpeed: 0,
        gameResult: null,
        pendingLose: false,
        animFrameId: null,
        assets: {
            bg: null,
            win: null,
            died: null,
            soldier: { idle: null, shoot: null, reload: null, dead: null },
            zombies: {
                1: { walk: null, hurt: null, attack: null, dead: null },
                2: { walk: null, hurt: null, attack: null, dead: null },
                3: { walk: null, hurt: null, attack: null, dead: null }
            }
        }
    });

    const frameCounts = {
        1: { walk: 10, hurt: 4, attack: 5, dead: 5 },
        2: { walk: 10, hurt: 4, attack: 4, dead: 5 },
        3: { walk: 12, hurt: 4, attack: 10, dead: 5 }
    };

    const loadImage = (src) => {
        const img = new Image();
        img.src = src;
        return img;
    };

    useEffect(() => {
        const g = gameRef.current;

        // Load all assets once
        g.assets.bg = loadImage("/assets/static/background/bg.png");
        g.assets.win = loadImage("/assets/static/ui/win.png");
        g.assets.died = loadImage("/assets/static/ui/died.png");

        g.assets.soldier.idle = loadImage("/assets/static/soldier/idle.png");
        g.assets.soldier.shoot = loadImage("/assets/static/soldier/shoot.png");
        g.assets.soldier.reload = loadImage("/assets/static/soldier/reload.png");
        g.assets.soldier.dead = loadImage("/assets/static/soldier/dead.png");

        for (let i = 1; i <= 3; i++) {
            g.assets.zombies[i].walk = loadImage(`/assets/static/zombie/${i}/walk.png`);
            g.assets.zombies[i].hurt = loadImage(`/assets/static/zombie/${i}/hurt.png`);
            g.assets.zombies[i].attack = loadImage(`/assets/static/zombie/${i}/attack.png`);
            g.assets.zombies[i].dead = loadImage(`/assets/static/zombie/${i}/dead.png`);
        }

        const canvas = canvasRef.current;
        g.ctx = canvas.getContext('2d');

        const handleResize = () => {
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            g.soldier.y = canvas.height - g.soldier.height - 10;
        };
        window.addEventListener('resize', handleResize);
        handleResize();

        return () => {
            window.removeEventListener('resize', handleResize);
            g.gameActive = false;
            if (g.animFrameId) cancelAnimationFrame(g.animFrameId);
        };
    }, []);

    // --- Exposed API ---
    useImperativeHandle(ref, () => ({
        shoot() {
            const g = gameRef.current;
            if (g.soldier.state === "dead" || !g.gameActive) return;
            g.soldier.state = "shoot";
            g.soldier.frame = 0;
            const target = g.zombies.find(z => z.hp > 0);
            if (target) {
                target.hp--;
                if (target.hp > 0) { target.state = "hurt"; target.frame = 0; }
            }
        },
        reload() {
            const g = gameRef.current;
            if (g.soldier.state === "dead" || !g.gameActive) return;
            g.soldier.state = "reload";
            g.soldier.frame = 0;
        },
        resetGame(onGameEnd) {
            onGameEndRef.current = onGameEnd || null;
            initGame();
        },
        isIdle() {
            const g = gameRef.current;
            return g.soldier.state === "idle";
        }
    }));

    // --- Game init ---
    const initGame = () => {
        const g = gameRef.current;
        // Stop previous loop
        g.gameActive = false;
        if (g.animFrameId) cancelAnimationFrame(g.animFrameId);

        g.gameResult = null;
        g.pendingLose = false;
        g.soldier.state = "idle";
        g.soldier.frame = 0;
        spawnZombies();

        g.gameActive = true;
        g.lastTime = performance.now();
        g.animFrameId = requestAnimationFrame(loop);
    };

    const spawnZombies = () => {
        const g = gameRef.current;
        const canvas = canvasRef.current;
        g.zombies = [];
        const spacing = 140;
        const hpValues = [2, 3, 2];
        for (let i = 0; i < 3; i++) {
            g.zombies.push({
                id: i + 1,
                x: canvas.width - 80 + i * spacing + (Math.random() * 40 - 20),
                hp: hpValues[i],
                state: "walk",
                frame: Math.floor(Math.random() * 8),
                frameTimer: Math.random() * 0.2,
                speedFactor: 0.85 + Math.random() * 0.3
            });
        }
        // Travel across the entire canvas width in ~90 seconds
        const travelDistance = g.zombies[0].x - g.soldier.x - 80;
        g.zombieSpeed = travelDistance / 90;
    };

    // --- Main loop ---
    const loop = (timestamp) => {
        const g = gameRef.current;
        if (!g.gameActive) return;

        const dt = Math.min((timestamp - g.lastTime) / 1000, 0.05); // cap dt to avoid jumps
        g.lastTime = timestamp;

        const canvas = canvasRef.current;
        const ctx = g.ctx;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Win / Lose screens
        if (g.gameResult === "win") {
            if (g.assets.win?.complete) ctx.drawImage(g.assets.win, 0, 0, canvas.width, canvas.height);
            return; // stop loop
        }
        if (g.gameResult === "lose") {
            if (g.assets.died?.complete) ctx.drawImage(g.assets.died, 0, 0, canvas.width, canvas.height);
            return; // stop loop
        }

        // Background
        if (g.assets.bg?.complete) ctx.drawImage(g.assets.bg, 0, 0, canvas.width, canvas.height);

        updateSoldier(dt);
        drawSoldier();
        updateZombies(dt);
        drawZombies();

        g.animFrameId = requestAnimationFrame(loop);
    };

    // --- Soldier ---
    const updateSoldier = (dt) => {
        const g = gameRef.current;
        const s = g.soldier;
        const maxFrames = s.frameCount[s.state];
        const animSpeed = s.state === "dead" ? 0.25 : 0.12;
        s.frameTimer += dt;
        if (s.frameTimer > animSpeed) {
            s.frameTimer = 0;
            if (s.state === "dead" && s.frame >= maxFrames - 1) {
                s.frame = maxFrames - 1;
                // Trigger lose after die animation
                if (g.pendingLose) {
                    g.pendingLose = false;
                    g.gameResult = "lose";
                    g.gameActive = false;
                    setTimeout(() => {
                        onGameEndRef.current?.("lose");
                    }, 800);
                }
                return;
            }
            s.frame++;
            if (s.frame >= maxFrames) {
                s.state !== "dead" ? (s.state = "idle", s.frame = 0) : (s.frame = maxFrames - 1);
            }
        }
    };

    const drawSoldier = () => {
        const g = gameRef.current;
        const s = g.soldier;
        const img = g.assets.soldier[s.state];
        if (!img || !img.width) return;
        const fw = img.width / s.frameCount[s.state];
        g.ctx.drawImage(img, s.frame * fw, 0, fw, img.height, s.x, s.y, s.width, s.height);
    };

    // --- Zombies ---
    const updateZombies = (dt) => {
        const g = gameRef.current;
        let aliveCount = 0;

        g.zombies.forEach(z => {
            if (z.hp <= 0 && z.state !== "dead") {
                z.state = "dead";
                z.frame = frameCounts[z.id].dead - 1;
            }
            if (z.hp > 0) aliveCount++;

            const counts = frameCounts[z.id];
            const animSpeed = z.state === "dead" ? 0.3 : 0.15;
            z.frameTimer += dt;
            let stepMove = false;

            if (z.frameTimer > animSpeed) {
                z.frameTimer = 0;
                const maxF = counts[z.state];
                if (z.state === "dead") {
                    if (z.frame > 0) z.frame--;
                } else {
                    z.frame++;
                    if (z.frame >= maxF) {
                        if (z.state === "hurt") z.state = "walk";
                        z.frame = 0;
                    }
                    if (z.state === "walk") stepMove = true;
                }
            }

            if (stepMove) z.x -= g.zombieSpeed * animSpeed * z.speedFactor;

            // Zombie reaches soldier
            if (z.state === "walk" && z.x < g.soldier.x + 90 && g.soldier.state !== "dead") {
                z.state = "attack";
                z.frame = 0;
                g.soldier.state = "dead";
                g.soldier.frame = 0;
                g.pendingLose = true;
            }
        });

        // All zombies dead → win
        if (aliveCount === 0 && g.gameResult === null && !g.pendingLose) {
            g.gameResult = "win";
            g.gameActive = false;
            setTimeout(() => {
                onGameEndRef.current?.("win");
            }, 800);
        }
    };

    const drawZombies = () => {
        const g = gameRef.current;
        const canvas = canvasRef.current;
        g.zombies.forEach(z => {
            const img = g.assets.zombies[z.id][z.state];
            if (!img || !img.complete) return;
            const fCount = frameCounts[z.id][z.state];
            const fw = img.width / fCount;
            const fh = img.height;
            const scale = 1.6;
            const drawW = fw * scale;
            const drawH = fh * scale;
            const drawY = canvas.height - 15 - drawH;
            g.ctx.drawImage(img, z.frame * fw, 0, fw, fh, z.x, drawY, drawW, drawH);
        });
    };

    return (
        <div className="game-canvas-container">
            <canvas ref={canvasRef} />
        </div>
    );
});

export default GameCanvas;
