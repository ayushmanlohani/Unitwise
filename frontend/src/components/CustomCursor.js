import React, { useEffect, useState } from 'react';
import { motion, useSpring, useMotionValue } from 'framer-motion';

/**
 * CustomCursor Component
 * An immersive, gas-like glowing cursor with zero-latency tracking, 
 * a fluid smoky trail, and idle swirl animations.
 */
const CustomCursor = () => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Motion values for instant tracking (zero lag core)
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Spring configuration for the fluid smoky trail
  const trailX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const trailY = useSpring(mouseY, { stiffness: 50, damping: 20 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      // Direct set for immediate response
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);

      const target = e.target;
      const isInteractive = 
        target.closest('button') || 
        target.closest('a') || 
        target.closest('input') ||
        target.closest('.cursor-hover');
      
      setIsHovered(!!isInteractive);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  return (
    <>
      {/* Smoky Fluid Trail */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[9998] rounded-full blur-[40px]"
        style={{
          x: trailX,
          y: trailY,
          width: isHovered ? 200 : 150,
          height: isHovered ? 200 : 150,
          translateX: '-50%',
          translateY: '-50%',
          background: 'radial-gradient(circle, rgba(201, 100, 66, 0.4) 0%, rgba(201, 100, 66, 0.1) 40%, transparent 70%)',
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.2, 0.4, 0.2],
          rotate: [0, -180], // Counter-rotation for the trail
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Main Gas Ball - Zero Latency */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[9999]"
        style={{
          x: mouseX,
          y: mouseY,
          translateX: '-50%',
          translateY: '-50%',
        }}
      >
        {/* The "Swirl" Container */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          className="relative flex items-center justify-center"
        >
          {/* Outer Glow */}
          <motion.div
            className="absolute rounded-full blur-3xl opacity-40 bg-[#c96442]"
            animate={{
              width: isHovered ? 240 : 160,
              height: isHovered ? 240 : 160,
            }}
          />

          {/* Core Gas Cloud - No Hard Edges */}
          <motion.div
            className="rounded-full blur-xl"
            style={{
              background: 'radial-gradient(circle, rgba(201, 100, 66, 0.8) 0%, rgba(201, 100, 66, 0.3) 45%, transparent 70%)',
            }}
            animate={{
              width: isHovered ? 180 : 120,
              height: isHovered ? 180 : 120,
              scale: [1, 1.1, 1],
            }}
            transition={{
              scale: { duration: 3, repeat: Infinity, ease: "easeInOut" },
              width: { duration: 0.3 },
              height: { duration: 0.3 },
            }}
          />
          
          {/* Subtle Internal "Tendrils" (Simulated by an offset cloud) */}
          <motion.div
            className="absolute rounded-full blur-2xl opacity-30 bg-[#c96442]"
            style={{ x: 20, y: -10 }}
            animate={{
              width: isHovered ? 100 : 60,
              height: isHovered ? 100 : 60,
              scale: [1, 1.3, 1],
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.div>
      </motion.div>
    </>
  );
};

export default CustomCursor;
