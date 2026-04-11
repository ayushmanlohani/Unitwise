import React, { useRef, useEffect } from 'react';

const SendIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export default function ChatInput({
    inputValue,
    setInputValue,
    subject,
    setSubject,
    isLoading,
    sendMessage,
    isCentered
}) {
    const textareaRef = useRef(null);

    // Auto-resize magic: Every time inputValue changes, recalculate the height
    useEffect(() => {
        if (textareaRef.current) {
            // Reset height to auto to get the true scrollHeight
            textareaRef.current.style.height = 'auto';
            // Set the height to match the internal text size
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [inputValue]);

    // Handle "Enter" to send, and "Shift+Enter" for a new line
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Stop it from making a new line
            if (!isLoading && inputValue.trim()) {
                sendMessage(e);
            }
        }
    };

    return (
        <div className={`w-full max-w-[850px] px-6 box-border ${isCentered ? 'mx-auto' : 'mx-auto mb-10'}`}>
            {/* Changed items-center to items-end so the button stays at the bottom when the box grows */}
            <form
                className="flex items-end bg-ivory border border-border-warm rounded-xl p-2 shadow-whisper transition-all duration-200"
                onSubmit={sendMessage}
            >
                <textarea
                    ref={textareaRef}
                    className="flex-1 border-none bg-transparent p-3 text-[16px] text-near-black outline-none font-sans resize-none overflow-y-auto min-h-[48px] max-h-[200px] leading-relaxed"
                    rows={1}
                    placeholder="Ask a question about your syllabus..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                />

                {/* Wrapper to keep the dropdown and button perfectly aligned at the bottom right */}
                <div className="flex items-center shrink-0 mb-1 ml-2">
                    {/* Subject Dropdown */}
                    <select
                        className="appearance-none bg-transparent border-none border-l border-border-cream text-olive-gray text-[14px] font-medium py-2 pr-6 pl-3 cursor-pointer outline-none"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                    >
                        <option value="Computer Networks">Computer Networks</option>
                    </select>

                    <button
                        type="submit"
                        className={`bg-brand-terracotta text-ivory border-none rounded-lg py-2.5 px-3.5 cursor-pointer flex items-center ml-2 transition-opacity ${isLoading || !inputValue.trim() ? 'opacity-60' : 'opacity-100 hover:opacity-90'}`}
                        disabled={isLoading || !inputValue.trim()}
                    >
                        <SendIcon />
                    </button>
                </div>
            </form>
        </div>
    );
}