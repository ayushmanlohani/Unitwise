import React, { useState } from 'react';
import { formatChatTime, formatChatDate, getSubjectInitials } from '../utils/dateFormatter';

const ChevronIcon = ({ isOpen }) => (
  <svg 
    width="14" 
    height="14" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
    style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
  >
    <path d="M6 9l6 6 6-6" />
  </svg>
);

export function getSubjectFullName(shortCode) {
  const map = {
    'CN': 'Computer Networks',
    'DIP': 'Digital Image Processing',
    'EML': 'Essentials of Machine Learning',
    'SCT': 'Soft Computing Techniques',
    'DMW': 'Data Mining and Warehousing',
    'QC': 'Quantum Computing',
    'OS': 'Operating System',
    'DBMS': 'Database Management System',
    'CN/CO': 'Computer Network',
    'TOC': 'Theory of Computation',
    'AI': 'Artificial Intelligence',
    'ML': 'Machine Learning',
    'DL': 'Deep Learning',
    'CNS': 'Computer Network & Security',
    'SE': 'Software Engineering',
    'CD': 'Compiler Design',
    'AT': 'Automata Theory',
    'CG': 'Computer Graphics',
    'WT': 'Web Technology',
    'JAVA': 'Java Programming',
    'PYTHON': 'Python Programming',
    'C': 'C Programming',
    'CPP': 'C++ Programming',
    'DS': 'Data Structures',
    'ALGO': 'Algorithms',
    'DM': 'Discrete Mathematics',
    'MATH': 'Mathematics',
    'COA': 'Computer Organization & Architecture',
    'MICRO': 'Microprocessor',
    'DCN': 'Data Communication & Networks',
  };
  
  const normalized = shortCode?.toUpperCase().trim();
  return map[normalized] || shortCode || 'Unknown';
}

export default function SubjectChatGroup({ subject, chats, currentChatId, onSelectChat }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!chats || chats.length === 0) return null;

  const sortedChats = [...chats].sort((a, b) => {
    if (!a.created_at) return 1;
    if (!b.created_at) return -1;
    return new Date(b.created_at) - new Date(a.created_at);
  });

  const lastChat = sortedChats[0];
  const lastChatTime = lastChat?.created_at ? formatChatTime(lastChat.created_at) : '';

  const handleChatClick = (chatId) => {
    setIsOpen(true);
    onSelectChat(chatId);
  };

  return (
    <div className="mb-3">
      <div 
        className="flex items-center justify-between p-2 rounded-lg cursor-pointer hover:bg-border-cream/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <div className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md bg-brand-terracotta text-ivory text-[11px] font-bold shadow-sm">
            {getSubjectInitials(subject)}
          </div>
          <div className="flex flex-col">
            <span className="text-[14px] font-semibold text-near-black">{getSubjectFullName(subject)}</span>
            {lastChatTime && (
              <span className="text-[11px] text-stone-gray">Last Chat at: {lastChatTime}</span>
            )}
          </div>
        </div>
        <ChevronIcon isOpen={isOpen} />
      </div>

      {isOpen && (
        <div className="mt-1 ml-4 pl-3 border-l-2 border-border-cream flex flex-col gap-1 max-h-60 overflow-y-auto">
          {sortedChats.map((chat) => (
            <div
              key={chat.id}
              className={`group flex items-center justify-between gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                currentChatId === chat.id 
                  ? 'bg-border-cream text-near-black' 
                  : 'hover:bg-parchment text-charcoal-warm'
              }`}
              onClick={() => handleChatClick(chat.id)}
            >
              <p className="truncate text-[13px] font-medium flex-1 min-w-0">
                {chat.title || "Study Session"}
              </p>
              <div className="shrink-0 flex flex-col items-end text-[10px] text-stone-gray">
                <span>{formatChatTime(chat.created_at)}</span>
                <span>{formatChatDate(chat.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}