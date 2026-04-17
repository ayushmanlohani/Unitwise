import React, { useState, useRef, useEffect } from 'react';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';

// HOW TO CHANGE ICONS: 
// Just change the emoji inside the 'icon' quotes below.
const modes = [
  { id: 'Academic', icon: '🎓', desc: 'Formal & Detailed' },
  { id: 'Simplified', icon: '💡', desc: 'Simple & Clear' },
  { id: 'Exam Prep', icon: '📝', desc: 'High-Yield Points' },
  { id: 'Revision', icon: '⚡', desc: 'Concise TL;DR' },
  { id: 'Analogy', icon: '🎭', desc: 'Real-world Examples' },
];

const springConfig = { mass: 0.1, stiffness: 150, damping: 12 };

function DockItem({ mode, mouseX, selectedMode, setSelectedMode, setIsOpen }) {
  const ref = useRef(null);
  const [isHovered, setIsHovered] = useState(false);

  const scaleSync = useTransform(mouseX, (val) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
    const distance = val - bounds.x - bounds.width / 2;
    if (Math.abs(distance) > 150) return 1;
    return 1 + 0.5 * Math.cos((distance / 150) * (Math.PI / 2));
  });

  const ySync = useTransform(mouseX, (val) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
    const distance = val - bounds.x - bounds.width / 2;
    if (Math.abs(distance) > 150) return 0;
    return -15 * Math.cos((distance / 150) * (Math.PI / 2));
  });

  const widthSync = useTransform(mouseX, (val) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 };
    const distance = val - bounds.x - bounds.width / 2;
    if (Math.abs(distance) > 150) return 75;
    return 75 + 20 * Math.cos((distance / 150) * (Math.PI / 2));
  });

  const scale = useSpring(scaleSync, springConfig);
  const y = useSpring(ySync, springConfig);
  const width = useSpring(widthSync, springConfig);

  return (
    // 'relative' here ensures the absolute tooltip anchors exactly to the center of this specific slot
    <motion.div
      ref={ref}
      style={{ width }}
      className="relative flex flex-col items-center justify-end h-full pb-2"
    >
      <motion.button
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => {
          setSelectedMode(mode.id);
          setIsOpen(false);
        }}
        style={{ scale, y }}
        className="relative flex flex-col items-center justify-end border-none cursor-pointer bg-transparent origin-bottom"
      >
        {/* Description Box - Anchored to the icon's movement, positioned BELOW */}
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: -10, x: "-50%" }}
            animate={{ opacity: 1, y: 0, x: "-50%" }}
            className="absolute top-full mt-3 left-1/2 w-max z-50 pointer-events-none flex flex-col items-center"
          >
            {/* Pointer arrow (top) */}
            <div className="w-2.5 h-2.5 bg-[#262626] rotate-45 -mb-1.5 border-l border-t border-white/10" />
            <div className="px-2 py-1 bg-[#262626] rounded-lg shadow-xl border border-white/10">
              <span className="text-[10px] font-medium text-white/95 whitespace-nowrap">{mode.desc}</span>
            </div>
          </motion.div>
        )}

        <span className="text-[28px] shrink-0 leading-none drop-shadow-sm">{mode.icon}</span>
        <span className="text-[12px] font-medium text-stone-600 mt-2 tracking-wide whitespace-nowrap">
          {mode.id}
        </span>
      </motion.button>
    </motion.div>
  );
}

export default function ModeDropdown({ selectedMode, setSelectedMode, isNewChat = true }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const mouseX = useMotionValue(99999);

  const displayText = selectedMode ? selectedMode : (isNewChat ? "MODES" : "Select Mode");

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative flex items-center" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/40 backdrop-blur-md border border-stone-200/50 cursor-pointer shadow-sm z-10 hover:bg-white/60 transition-colors"
      >
        {!selectedMode && <span className="text-[15px]">✨</span>}
        {selectedMode && <span className="text-[15px]">{modes.find(m => m.id === selectedMode)?.icon}</span>}
        <span className="text-[14px] font-medium text-stone-800 tracking-wide">{displayText}</span>
      </button>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          onMouseMove={(e) => mouseX.set(e.clientX)}
          onMouseLeave={() => mouseX.set(99999)}
          className="absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 flex items-end justify-center px-4 pt-4 pb-1 bg-white/70 backdrop-blur-2xl border border-white/20 rounded-[20px] shadow-2xl z-0 h-[84px]"
        >
          {modes.map((mode) => (
            <DockItem
              key={mode.id}
              mode={mode}
              mouseX={mouseX}
              selectedMode={selectedMode}
              setSelectedMode={setSelectedMode}
              setIsOpen={setIsOpen}
            />
          ))}
        </motion.div>
      )}
    </div>
  );
}