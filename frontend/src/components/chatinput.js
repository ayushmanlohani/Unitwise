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
    onSubjectChange,
    isLoading,
    sendMessage,
    isCentered
}) {
    const textareaRef = useRef(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [inputValue]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isLoading && inputValue.trim()) {
                sendMessage(e);
            }
        }
    };

    return (
        <div className={`w-full max-w-[800px] px-6 box-border ${isCentered ? 'mx-auto' : 'mx-auto mb-10'}`}>
            <form
                className="flex items-end bg-ivory border border-border-warm rounded-xl p-2 shadow-whisper transition-all duration-200"
                onSubmit={sendMessage}
            >
                <textarea
                    ref={textareaRef}
                    // Set exact min-height to 48px
                    className="flex-1 border-none bg-transparent py-3 px-3 text-[16px] text-near-black outline-none font-sans resize-none overflow-y-auto min-h-[48px] max-h-[200px] leading-relaxed"
                    rows={1}
                    placeholder="Ask a question about your syllabus..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                />

                {/* Added mb-1.5 (6px) to perfectly center the 36px controls inside the 48px textarea */}
                <div className="flex items-center gap-2 shrink-0 mb-1.5 mr-1">

                    {/* Forced height to exactly 36px */}
                    <div className="relative flex items-center h-[36px]">
                        <select
                            className="appearance-none h-full bg-parchment border border-border-cream hover:border-border-warm text-charcoal-warm text-[13px] font-semibold pl-3 pr-8 rounded-md cursor-pointer outline-none transition-all shadow-sm focus:ring-1 focus:ring-border-warm"
                            value={subject}
                            onChange={(e) => onSubjectChange(e.target.value)}
                        >
                            <option value="CN">Computer Networks</option>
                            <option value="DIP">Digital Image Processing</option>
                            <option value="EML">Essentials of Machine Learning</option>
                            <option value="SCT">Soft Computing Techniques</option>
                            <option value="DMW">Data Mining and Warehousing</option>
                            <option value="QC">Quantum Computing</option>
                        </select>

                        <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-stone-gray">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M6 9l6 6 6-6" />
                            </svg>
                        </div>
                    </div>

                    {/* Forced height to exactly 36px and fixed width */}
                    <button
                        type="submit"
                        className={`bg-brand-terracotta text-ivory border-none rounded-lg h-[36px] w-[44px] flex items-center justify-center transition-opacity ${isLoading || !inputValue.trim() ? 'opacity-60' : 'opacity-100 hover:opacity-90 shadow-ring-brand cursor-pointer'}`}
                        disabled={isLoading || !inputValue.trim()}
                    >
                        <SendIcon />
                    </button>
                </div>
            </form>
        </div>
    );
}