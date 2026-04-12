import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function AmbientMotion() {
    const [particles, setParticles] = useState([]);

    useEffect(() => {
        // 1. CONFIGURATION: Change this number to add more or fewer leaves
        const particleCount = 25;
        const newParticles = [];

        for (let i = 0; i < particleCount; i++) {
            // 2. MATH: Calculate a random angle and distance for the "dispersion" from center
            const angle = Math.random() * Math.PI * 2;
            // Distance pushes them outward. Mobile screens need less distance, desktop needs more.
            const distance = Math.random() * 60 + 20;

            newParticles.push({
                id: i,
                // Randomize size between 0.5 and 1.5
                scale: Math.random() * 1 + 0.5,
                // Randomize rotation
                rotation: Math.random() * 360,
                // Calculate the exact X and Y endpoint based on the angle
                xOffset: Math.cos(angle) * distance,
                yOffset: Math.sin(angle) * distance,
                // Randomize how long the animation takes (between 15 and 30 seconds)
                duration: Math.random() * 15 + 15,
                // Randomize when the leaf starts moving so they don't all move at once
                delay: Math.random() * -20,
            });
        }
        setParticles(newParticles);
    }, []);

    return (
        // The container is absolutely positioned behind everything (z-0) and ignores mouse clicks
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0 flex items-center justify-center">

            {particles.map((p) => (
                <motion.div
                    key={p.id}
                    className="absolute w-6 h-6 rounded-full opacity-0"
                    // Alternating colors using our custom design tokens!
                    style={{
                        backgroundColor: p.id % 3 === 0 ? '#c96442' : '#e8e6dc', // Terracotta or Warm Sand
                        filter: 'blur(4px)', // Softens the edges so it feels out-of-focus
                    }}

                    // STARTING POSITION: Dead center, tiny, and invisible
                    initial={{
                        x: '0vw',
                        y: '0vh',
                        scale: 0,
                        rotate: 0,
                        opacity: 0,
                    }}

                    // ENDING POSITION: Dispersed outward, rotating, fading in then out
                    animate={{
                        x: `${p.xOffset}vw`,
                        y: `${p.yOffset}vh`,
                        scale: [0, p.scale, p.scale * 1.2, p.scale],
                        rotate: p.rotation + 360, // Spin a full circle
                        opacity: [0, 0.15, 0.15, 0], // Peak at 15% opacity so it's very subtle
                    }}

                    // HOW IT MOVES: Smooth, infinitely looping, and bouncing back and forth
                    transition={{
                        duration: p.duration,
                        repeat: Infinity,
                        repeatType: 'mirror',
                        ease: "easeInOut",
                        delay: p.delay,
                    }}
                />
            ))}
        </div>
    );
}