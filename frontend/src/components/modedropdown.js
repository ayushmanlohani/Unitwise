import React, { useState, useRef, useEffect } from 'react';

const modes = [
  { id: 'Academic', icon: '🎓', desc: 'Formal & Detailed' },
  { id: 'Simplified', icon: '💡', desc: 'Simple & Clear' },
  { id: 'Exam Prep', icon: '📝', desc: 'High-Yield Points' },
  { id: 'Quick Summary', icon: '⚡', desc: 'Concise TL;DR' },
  { id: 'Analogy', icon: '🎭', desc: 'Real-world Examples' },
];

export default function ModeDropdown({ selectedMode, setSelectedMode }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/40 backdrop-blur-md border border-stone-200/50 hover:bg-white/60 transition-all duration-200 cursor-pointer shadow-sm"
      >
        <span className="text-[14px]">{modes.find(m => m.id === selectedMode)?.icon}</span>
        <span className="text-[13px] font-medium text-stone-800">{selectedMode}</span>
        <svg 
            width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" 
            className={`transition-transform duration-300 ${isOpen ? 'rotate-180' : ''} text-stone-500`}
        >
            <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {/* macOS Style Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-52 origin-top-right bg-white/70 backdrop-blur-2xl border border-white/20 rounded-2xl shadow-2xl p-1.5 z-50 ring-1 ring-black/5 animate-in fade-in zoom-in duration-200">
          <div className="px-3 py-1.5 text-[10px] font-bold text-stone-400 uppercase tracking-widest">
            Response Style
          </div>
          <div className="flex flex-col gap-0.5">
            {modes.map((mode) => (
              <button
                key={mode.id}
                onClick={() => {
                  setSelectedMode(mode.id);
                  setIsOpen(false);
                }}
                className={`flex items-center gap-3 w-full px-2.5 py-2 rounded-[10px] transition-all duration-200 border-none cursor-pointer text-left
                  ${selectedMode === mode.id 
                    ? 'bg-stone-800 text-white shadow-lg shadow-stone-800/20' 
                    : 'hover:bg-stone-800/5 text-stone-700'
                  }`}
              >
                <span className="text-[16px]">{mode.icon}</span>
                <div className="flex flex-col">
                  <span className="text-[13px] font-semibold leading-tight">{mode.id}</span>
                  <span className={`text-[10px] ${selectedMode === mode.id ? 'text-white/70' : 'text-stone-400'}`}>
                    {mode.desc}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
