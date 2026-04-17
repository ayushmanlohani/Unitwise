import React, { useState, useRef, useMemo } from 'react';
import SubjectChatGroup from './SubjectChatGroup';
import StarredChatsGroup from './StarredChatsGroup';

// --- SVG Icons ---
const SidebarToggleIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);
const PlusIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);
const LogoutIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
    </svg>
);

export default function Sidebar({
    isOpen,
    setIsOpen,
    createNewChat,
    chatSessions,
    currentChatId,
    loadMessagesForChat,
    session,
    handleSignOut
}) {
    const [customWidth, setCustomWidth] = useState(280);
    const sidebarRef = useRef(null);
    const isResizing = useRef(false);

    const currentWidth = isOpen ? customWidth : 68;

    const startResizing = (e) => {
        if (!isOpen) return;
        isResizing.current = true;

        if (sidebarRef.current) {
            sidebarRef.current.style.transition = 'none';
        }

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResizing);
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    };

    const handleMouseMove = (e) => {
        if (!isResizing.current) return;
        if (sidebarRef.current) {
            const newWidth = e.clientX;
            if (newWidth >= 240 && newWidth <= 500) {
                sidebarRef.current.style.width = `${newWidth}px`;
            }
        }
    };

    const stopResizing = () => {
        isResizing.current = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResizing);
        document.body.style.cursor = 'default';
        document.body.style.userSelect = 'auto';

        if (sidebarRef.current) {
            sidebarRef.current.style.transition = 'all 300ms ease-in-out';
            setCustomWidth(sidebarRef.current.offsetWidth);
        }
    };

    const { starredChats, subjectGroups } = useMemo(() => {
        const starred = chatSessions.filter(chat => chat.is_starred);
        const nonStarred = chatSessions.filter(chat => !chat.is_starred);
        
        const groups = {};
        nonStarred.forEach(chat => {
            const subject = chat.subject || 'Unknown';
            if (!groups[subject]) {
                groups[subject] = [];
            }
            groups[subject].push(chat);
        });

        return { starredChats: starred, subjectGroups: groups };
    }, [chatSessions]);

    const subjectList = Object.keys(subjectGroups).sort();

    return (
        <aside
            ref={sidebarRef}
            style={{ width: `${currentWidth}px` }}
            className="relative flex flex-col shrink-0 bg-ivory border-r border-border-cream transition-all duration-300 ease-in-out overflow-hidden"
        >
            {isOpen && (
                <div
                    onMouseDown={startResizing}
                    className="absolute right-0 top-0 w-1 h-full cursor-col-resize hover:bg-brand-terracotta/40 z-50 transition-colors"
                />
            )}

            {/* HEADER */}
            <div className={`p-4 flex items-center shrink-0 h-16 ${!isOpen ? 'justify-center' : 'justify-between'}`}>
                {isOpen && (
                    <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap transition-opacity duration-300">
                        <img src="/logo.png" alt="logo" className="w-6 h-6 shrink-0" />
                        <span className="font-serif text-lg font-bold text-near-black">Unitwise</span>
                    </div>
                )}
                <button
                    className="bg-transparent border-none text-olive-gray cursor-pointer p-1 hover:text-near-black transition-colors shrink-0"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <SidebarToggleIcon />
                </button>
            </div>

            {/* NEW SESSION BUTTON */}
            <div className="px-4 mb-6 flex justify-center">
                <button
                    className={`flex items-center justify-center gap-2 bg-warm-sand text-near-black border-none rounded-lg text-[15px] font-medium cursor-pointer shadow-ring-warm hover:bg-[#d1cfc5] transition-all duration-300 shrink-0 ${isOpen ? 'w-full py-2 px-3' : 'w-10 h-10 p-0'
                        }`}
                    onClick={createNewChat}
                >
                    <PlusIcon />
                    {isOpen && <span className="whitespace-nowrap">New Session</span>}
                </button>
            </div>

            {/* HISTORY SECTION */}
            <div className={`flex-1 overflow-y-auto overflow-x-hidden px-4 transition-opacity duration-300 ${!isOpen ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                {/* Starred Chats Group */}
                {starredChats.length > 0 && (
                    <StarredChatsGroup 
                        chats={starredChats}
                        currentChatId={currentChatId}
                        onSelectChat={loadMessagesForChat}
                    />
                )}

                {/* Old Chats Heading */}
                {subjectList.length > 0 && (
                    <div className="text-[11px] font-bold text-stone-gray uppercase tracking-widest px-2 pt-2 pb-3">Old Chats</div>
                )}

                {/* Subject Groups */}
                {subjectList.length > 0 ? (
                    subjectList.map(subject => (
                        <SubjectChatGroup
                            key={subject}
                            subject={subject}
                            chats={subjectGroups[subject]}
                            currentChatId={currentChatId}
                            onSelectChat={loadMessagesForChat}
                        />
                    ))
                ) : (
                    <div className="text-[13px] text-stone-gray/60 px-2 py-2 italic">No recent sessions</div>
                )}
            </div>

            {/* FOOTER */}
            <footer className={`p-4 border-t border-border-cream flex items-center shrink-0 bg-ivory/50 transition-all duration-300 ${!isOpen ? 'justify-center' : 'justify-between gap-3'}`}>
                {isOpen && (
                    <div className="flex-1 min-w-0 truncate text-[13px] text-olive-gray font-medium cursor-help" title={session?.user?.email}>
                        {session?.user?.email}
                    </div>
                )}
                <button
                    onClick={handleSignOut}
                    className={`bg-[#fef2f2] text-[#ef4444] border border-[#fca5a5] transition-all duration-300 flex items-center justify-center cursor-pointer hover:bg-[#fee2e2] ${isOpen ? 'px-3 py-1.5 rounded text-[12px] font-semibold' : 'w-10 h-10 rounded-full'
                        }`}
                >
                    {!isOpen ? <LogoutIcon /> : <span>Log Out</span>}
                </button>
            </footer>
        </aside>
    );
}