import { useState, useRef, useEffect } from 'react';
import { supabase } from '../config/supabaseClient';
import Sidebar from '../components/sidebar';
import ChatInput from '../components/chatinput';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

// --- Icons ---
const SidebarToggleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);
const ChevronDownIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg>
);
const StarIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>
);
const RenameIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>
);
const DeleteIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b53333" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6" /></svg>
);

// --- Helper: Format LLM LaTeX delimiters to Markdown Math delimiters ---
const formatMathDelimiters = (text) => {
  if (!text) return '';
  // 1. Replace block math: \[ ... \] becomes $$ ... $$
  let formatted = text.replace(/\\\[(.*?)\\\]/gs, '$$$$$1$$$$');
  // 2. Replace inline math: \( ... \) becomes $ ... $
  formatted = formatted.replace(/\\\((.*?)\\\)/gs, '$$$1$$');
  return formatted;
};

// --- Mini Component: The Sleek Sources Accordion ---
const SourceAccordion = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="mt-4 border border-border-cream/80 rounded-lg overflow-hidden bg-parchment/40">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-[13px] text-charcoal-warm font-medium hover:bg-border-cream/50 transition-colors border-none cursor-pointer bg-transparent"
      >
        <span className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" /></svg>
          View Sources ({sources.length})
        </span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}><path d="M6 9l6 6 6-6" /></svg>
      </button>
      {isOpen && (
        <div className="p-3 pt-1 flex flex-col gap-2 border-t border-border-cream/50">
          {sources.map((src, i) => (
            <div key={i} className="text-[12px] leading-relaxed text-olive-gray bg-ivory p-2 rounded-md border border-border-warm/50 shadow-sm">
              {src}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default function ChatDashboard({ session }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [subject, setSubject] = useState('CN'); // Default to Short Code
  const [isLoading, setIsLoading] = useState(false);
  const [chatSessions, setChatSessions] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Warning Modal State
  const [showSubjectWarning, setShowSubjectWarning] = useState(false);
  const [pendingSubject, setPendingSubject] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    loadChatSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadChatSessions() {
    const { data, error } = await supabase
      .from('chats')
      .select('*')
      .eq('user_id', session.user.id)
      .order('created_at', { ascending: false });
    if (!error) setChatSessions(data || []);
  }

  const loadMessagesForChat = async (chatId) => {
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .eq('chat_id', chatId)
      .order('created_at', { ascending: true });

    if (!error) {
      setMessages(data.map(msg => ({ role: msg.role, content: msg.content, sources: msg.sources })));
      setCurrentChatId(chatId);
      setIsDropdownOpen(false);

      // Update the dropdown to match this chat's subject
      const activeChat = chatSessions.find(c => c.id === chatId);
      if (activeChat) setSubject(activeChat.subject);
    }
  };

  function createNewChat() {
    setCurrentChatId(null);
    setMessages([]);
    setIsDropdownOpen(false);
  }

  // Handle changing subjects mid-chat
  const handleSubjectChange = (newSubject) => {
    if (messages.length > 0 && newSubject !== subject) {
      setPendingSubject(newSubject);
      setShowSubjectWarning(true);
    } else {
      setSubject(newSubject);
    }
  };

  const confirmSubjectChange = () => {
    setSubject(pendingSubject);
    setShowSubjectWarning(false);
    setPendingSubject(null);
    createNewChat(); // Clears the screen and starts fresh
  };

  async function handleSignOut() {
    await supabase.auth.signOut();
  }

  async function sendMessage(e) {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userContent = inputValue.trim();
    setMessages(prev => [...prev, { role: 'user', content: userContent }]);
    setInputValue('');
    setIsLoading(true);

    let activeChatId = currentChatId;

    try {
      if (!activeChatId) {
        const title = userContent.slice(0, 30) + '...';
        const { data: chatData, error: chatError } = await supabase
          .from('chats')
          .insert([{ user_id: session.user.id, title, subject, is_starred: false }])
          .select().single();
        if (chatError) throw chatError;
        activeChatId = chatData.id;
        setCurrentChatId(activeChatId);
      }

      await supabase.from('messages').insert([{ chat_id: activeChatId, role: 'user', content: userContent }]);

      const response = await fetch('http://127.0.0.1:8000/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userContent,
          subject: subject,
          chat_history: messages.map(msg => ({ role: msg.role, content: msg.content })),
        }),
      });

      if (!response.ok) throw new Error('API Error');
      const data = await response.json();

      await supabase.from('messages').insert([{
        chat_id: activeChatId,
        role: 'assistant',
        content: data.answer,
        sources: data.sources // Pushing the JSON array to Supabase
      }]);

      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, sources: data.sources }]);
      loadChatSessions();
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'An error occurred while accessing the library.' }]);
    } finally {
      setIsLoading(false);
    }
  }

  // --- Dropdown Actions ---
  const toggleStar = async () => {
    if (!currentChatId) return;
    const chat = chatSessions.find(c => c.id === currentChatId);
    const newStatus = !chat.is_starred;
    await supabase.from('chats').update({ is_starred: newStatus }).eq('id', currentChatId);
    loadChatSessions();
    setIsDropdownOpen(false);
  };

  const deleteChat = async () => {
    if (!currentChatId) return;
    await supabase.from('chats').delete().eq('id', currentChatId);
    createNewChat();
    loadChatSessions();
    setIsDropdownOpen(false);
  };

  const isChatActive = messages.length > 0;
  const currentChat = chatSessions.find(c => c.id === currentChatId);
  const chatTitle = currentChat ? currentChat.title : "New Study Session";
  const userInitial = session?.user?.email ? session.user.email.charAt(0).toUpperCase() : '?';

  return (
    <div className="h-screen flex bg-parchment text-near-black font-sans overflow-hidden relative">

      {/* WARNING MODAL OVERLAY */}
      {showSubjectWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-near-black/20 backdrop-blur-sm px-4">
          <div className="bg-ivory border border-border-warm rounded-2xl p-8 shadow-whisper max-w-sm w-full">
            <h3 className="font-serif text-2xl font-medium text-near-black mb-3">Change Subject?</h3>
            <p className="font-sans text-[15px] text-olive-gray mb-8 leading-relaxed">
              Switching the subject will close this chat and start a new study session. Do you want to proceed?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowSubjectWarning(false); setPendingSubject(null); }}
                className="px-5 py-2.5 text-[14px] font-medium text-charcoal-warm bg-transparent border-none cursor-pointer hover:bg-border-cream rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmSubjectChange}
                className="px-5 py-2.5 text-[14px] font-medium text-ivory bg-brand-terracotta border-none cursor-pointer hover:opacity-90 rounded-lg shadow-ring-brand transition-colors"
              >
                Yes, Start New
              </button>
            </div>
          </div>
        </div>
      )}

      <Sidebar
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
        createNewChat={createNewChat}
        chatSessions={chatSessions}
        currentChatId={currentChatId}
        loadMessagesForChat={loadMessagesForChat}
        session={session}
        handleSignOut={handleSignOut}
      />

      <main className="flex-1 flex flex-col relative overflow-hidden">

        <header className="sticky top-0 z-20 flex items-center justify-between px-8 py-4 bg-parchment/80 backdrop-blur-md border-b border-border-cream/50">
          <div className="flex items-center gap-4">
            <div className="relative flex items-center">
              <button
                className="flex items-center gap-2 bg-transparent border-none cursor-pointer hover:bg-border-cream/50 px-2 py-1 rounded-md transition-colors"
                onClick={() => isChatActive && setIsDropdownOpen(!isDropdownOpen)}
                disabled={!isChatActive}
              >
                <h2 className="font-serif text-[18px] font-medium text-near-black truncate max-w-[400px]">
                  {chatTitle}
                </h2>
                {isChatActive && <ChevronDownIcon />}
              </button>

              {isDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-ivory border border-border-warm rounded-xl shadow-whisper py-2 z-30">
                  <button onClick={toggleStar} className="w-full flex items-center gap-3 px-4 py-2 text-[14px] text-charcoal-warm hover:bg-parchment cursor-pointer bg-transparent border-none text-left">
                    <StarIcon /> {currentChat?.is_starred ? 'Unstar' : 'Star'}
                  </button>
                  <button className="w-full flex items-center gap-3 px-4 py-2 text-[14px] text-charcoal-warm hover:bg-parchment cursor-pointer bg-transparent border-none text-left">
                    <RenameIcon /> Rename
                  </button>
                  <div className="my-1 border-t border-border-cream"></div>
                  <button onClick={deleteChat} className="w-full flex items-center gap-3 px-4 py-2 text-[14px] text-[#b53333] hover:bg-[#fef2f2] cursor-pointer bg-transparent border-none text-left">
                    <DeleteIcon /> Delete
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center justify-center shrink-0 w-9 h-9 rounded-full bg-brand-terracotta text-ivory font-sans font-medium text-[15px] shadow-ring-brand select-none cursor-default">
            {userInitial}
          </div>
        </header>

        {isChatActive ? (
          <>
            <div
              className="flex-1 overflow-y-auto px-[10%] py-10 flex flex-col gap-8"
              style={{ WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 40px, black)' }}
            >
              {messages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                return (
                  <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>

                      <div className={`text-[17px] leading-relaxed p-4 rounded-xl [&>p]:mb-4 last:[&>p]:mb-0 [&>strong]:font-semibold [&>ul]:list-disc [&>ul]:ml-6 [&>ol]:list-decimal [&>ol]:ml-6 ${isUser ? 'bg-warm-sand text-near-black' : 'bg-ivory text-near-black border border-border-cream shadow-whisper'}`}>
                        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                          {formatMathDelimiters(msg.content)}
                        </ReactMarkdown>
                      </div>

                      {/* THE NEW SOURCES ACCORDION */}
                      {!isUser && msg.sources && msg.sources.length > 0 && (
                        <SourceAccordion sources={msg.sources} />
                      )}

                    </div>
                  </div>
                );
              })}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] text-[17px] leading-relaxed p-4 rounded-xl bg-transparent text-stone-gray italic">
                    Consulting textbook...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <ChatInput
              inputValue={inputValue} setInputValue={setInputValue}
              subject={subject} onSubjectChange={handleSubjectChange}
              isLoading={isLoading} sendMessage={sendMessage}
              isCentered={false}
            />
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <h1 className="font-serif text-4xl font-medium leading-tight text-near-black mb-10">
              How can I help you study?
            </h1>
            <ChatInput
              inputValue={inputValue} setInputValue={setInputValue}
              subject={subject} onSubjectChange={handleSubjectChange}
              isLoading={isLoading} sendMessage={sendMessage}
              isCentered={true}
            />
          </div>
        )}
      </main>
    </div>
  );
}