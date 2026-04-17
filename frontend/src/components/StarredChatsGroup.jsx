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

const StarIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

export default function StarredChatsGroup({ chats, currentChatId, onSelectChat }) {
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
    <div className="mb-4">
      <div 
        className="flex items-center justify-between p-2 rounded-lg cursor-pointer hover:bg-border-cream/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <div className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md bg-amber-500 text-ivory shadow-sm">
            <StarIcon />
          </div>
          <div className="flex flex-col">
            <span className="text-[14px] font-semibold text-near-black">Starred Chats</span>
            {lastChatTime && (
              <span className="text-[11px] text-stone-gray">{lastChatTime}</span>
            )}
          </div>
        </div>
        <ChevronIcon isOpen={isOpen} />
      </div>

      {isOpen && (
        <div className="mt-1 ml-4 pl-3 border-l-2 border-amber-200 flex flex-col gap-1 max-h-60 overflow-y-auto">
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
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div className="shrink-0 w-6 h-6 flex items-center justify-center rounded-md bg-brand-terracotta/20 text-brand-terracotta text-[10px] font-bold">
                  {getSubjectInitials(chat.subject)}
                </div>
                <p className="truncate text-[13px] font-medium">
                  {chat.title || "Study Session"}
                </p>
              </div>
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