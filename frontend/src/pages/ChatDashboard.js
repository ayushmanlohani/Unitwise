/**
 * ChatDashboard.js — Main authenticated view for the Unitwise app.
 *
 * Displays a header with user info and sign-out, a sidebar for chat history,
 * and a fully functional RAG chat interface communicating with the FastAPI backend.
 *
 * Props:
 *   session — the active Supabase auth session object.
 */

import { useState, useRef, useEffect } from 'react';
import { supabase } from '../config/supabaseClient';

// ---------------------------------------------------------------------------
// Styles — dark academic theme
// ---------------------------------------------------------------------------

const styles = {
  /* ---------- Full-page wrapper ---------- */
  page: {
    height: '100vh',
    background: 'linear-gradient(160deg, #0f0c29 0%, #1a1a2e 40%, #16213e 100%)',
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    color: '#f0f0f0',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },

  /* ---------- Top header bar ---------- */
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1rem 2rem',
    background: 'rgba(255, 255, 255, 0.04)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    flexShrink: 0,
    zIndex: 10,
  },
  headerTitle: {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: 700,
    letterSpacing: '-0.01em',
    background: 'linear-gradient(135deg, #667eea, #a78bfa)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  email: {
    fontSize: '0.85rem',
    color: 'rgba(255, 255, 255, 0.55)',
  },
  signOutBtn: {
    padding: '0.4rem 0.9rem',
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#fca5a5',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.25)',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background 0.2s, transform 0.15s',
  },

  /* ---------- Main Layout (Sidebar + Chat) ---------- */
  mainArea: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },

  /* ---------- Sidebar ---------- */
  sidebar: {
    width: '250px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRight: '1px solid rgba(255, 255, 255, 0.05)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    transition: 'width 0.3s',
  },
  sidebarInner: {
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  newChatBtn: {
    width: '100%',
    padding: '0.75rem',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
    color: '#fff',
    fontWeight: 600,
    cursor: 'pointer',
    marginBottom: '1rem',
    transition: 'background 0.2s',
  },
  chatList: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  chatListItem: (isActive) => ({
    padding: '0.75rem',
    background: isActive ? 'rgba(102, 126, 234, 0.2)' : 'transparent',
    border: isActive ? '1px solid rgba(102, 126, 234, 0.5)' : '1px solid transparent',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background 0.2s',
  }),
  chatListTitle: {
    fontSize: '0.9rem',
    fontWeight: 600,
    marginBottom: '0.2rem',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  chatListSubject: {
    fontSize: '0.75rem',
    color: 'rgba(255, 255, 255, 0.5)',
  },

  /* ---------- Chat Container ---------- */
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
  },
  messageListWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    maxWidth: '900px',
    margin: '0 auto',
    overflow: 'hidden',
  },
  messageList: {
    flex: 1,
    overflowY: 'auto',
    padding: '2rem 1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  messageRow: {
    display: 'flex',
    width: '100%',
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  assistantRow: {
    justifyContent: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    padding: '1rem 1.25rem',
    borderRadius: '16px',
    fontSize: '0.95rem',
    lineHeight: 1.5,
  },
  userBubble: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    borderBottomRightRadius: '4px',
    boxShadow: '0 4px 15px rgba(102, 126, 234, 0.2)',
  },
  assistantBubble: {
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    color: '#f0f0f0',
    borderBottomLeftRadius: '4px',
    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
  },

  /* Sources */
  sourcesContainer: {
    marginTop: '1rem',
    paddingTop: '0.75rem',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
  },
  sourceTitle: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#a78bfa',
    marginBottom: '0.6rem',
  },
  sourcePillContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
  },
  sourcePill: {
    background: 'rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '0.3rem 0.6rem',
    fontSize: '0.75rem',
    color: 'rgba(255, 255, 255, 0.75)',
  },

  /* Loading Indicator */
  typingIndicator: {
    alignSelf: 'flex-start',
    padding: '0.75rem 1.25rem',
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '16px',
    borderBottomLeftRadius: '4px',
    fontSize: '0.9rem',
    color: 'rgba(255, 255, 255, 0.5)',
  },

  /* ---------- Input Form ---------- */
  formContainer: {
    padding: '1.5rem',
    background: 'rgba(0, 0, 0, 0.2)',
    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
    width: '100%',
  },
  form: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'center',
    maxWidth: '900px',
    margin: '0 auto',
    width: '100%',
  },
  select: {
    padding: '0.8rem',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '0.9rem',
    outline: 'none',
    cursor: 'pointer',
  },
  selectOption: {
    background: '#1a1a2e',
    color: '#fff',
  },
  input: {
    flex: 1,
    padding: '0.8rem 1.25rem',
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '24px',
    fontSize: '0.95rem',
    color: '#fff',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    padding: '0.8rem 1.5rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: '24px',
    color: '#fff',
    fontWeight: 600,
    fontSize: '0.95rem',
    cursor: 'pointer',
    transition: 'opacity 0.2s',
  },
};

const DEFAULT_MESSAGE = {
  role: 'assistant',
  content: 'Hello! What concept from the syllabus can I help you with today?',
  sources: [],
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ChatDashboard({ session }) {
  // ---- State ----
  const [messages, setMessages] = useState([DEFAULT_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [subject, setSubject] = useState('Computer Networks');
  const [isLoading, setIsLoading] = useState(false);

  // Layout & DB State
  const [chatSessions, setChatSessions] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // ---- Refs & Effects ----
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat sessions on mount
  useEffect(() => {
    loadChatSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- Database Helpers ----
  async function loadChatSessions() {
    const { data, error } = await supabase
      .from('chats')
      .select('*')
      .eq('user_id', session.user.id)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error loading chat sessions:', error);
    } else {
      setChatSessions(data || []);
    }
  }

  const loadMessagesForChat = async (chatId) => {
    // 1. Fetch the data (keep your existing supabase query)
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .eq('chat_id', chatId)
      .order('created_at', { ascending: true });

    if (error) {
      console.error("Error loading messages:", error);
      return;
    }

    // 2. The Fix: Safely parse the sources
    const formattedMessages = data.map((msg) => {
      let safeSources = [];

      // Only try to parse if it's a string. If Supabase already made it an array, just use it.
      if (typeof msg.sources === 'string' && msg.sources.trim() !== '') {
        try {
          safeSources = JSON.parse(msg.sources);
        } catch (e) {
          console.error("Failed to parse sources for message:", msg.id);
        }
      } else if (Array.isArray(msg.sources)) {
        safeSources = msg.sources;
      }

      return {
        role: msg.role,
        content: msg.content,
        sources: safeSources,
      };
    });

    // 3. Update the state
    setMessages(formattedMessages);
    setCurrentChatId(chatId);
  };

  function createNewChat() {
    setCurrentChatId(null);
    setMessages([DEFAULT_MESSAGE]);
  }

  // ---- Handlers ----
  async function handleSignOut() {
    await supabase.auth.signOut();
  }

  async function sendMessage(e) {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userContent = inputValue.trim();
    const userMessage = { role: 'user', content: userContent };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    let activeChatId = currentChatId;

    try {
      // 1. Create a new chat session if one doesn't exist
      if (!activeChatId) {
        const { data: chatData, error: chatError } = await supabase
          .from('chats')
          .insert([
            {
              user_id: session.user.id,
              title: userContent.slice(0, 30) + (userContent.length > 30 ? '...' : ''), // Basic title 
              subject: subject,
            },
          ])
          .select()
          .single();

        if (chatError) throw chatError;
        activeChatId = chatData.id;
        setCurrentChatId(activeChatId);
      }

      // 2. Save the user's message to Supabase
      const { error: userMsgError } = await supabase
        .from('messages')
        .insert([
          {
            chat_id: activeChatId,
            role: 'user',
            content: userContent,
          },
        ]);

      if (userMsgError) throw userMsgError;

      // 3. Fetch from FastAPI
      const response = await fetch('http://127.0.0.1:8000/api/v1/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          subject: subject,
          chat_history: messages
            .filter((msg) => msg.role !== 'system') // Filter if needed, default message is 'assistant' so we pass it
            .map((msg) => ({ role: msg.role, content: msg.content })),
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };

      // Update Local State
      setMessages((prev) => [...prev, assistantMessage]);

      // 4. Save the AI's answer to Supabase
      const { error: assistantMsgError } = await supabase
        .from('messages')
        .insert([
          {
            chat_id: activeChatId,
            role: 'assistant',
            content: data.answer,
            sources: JSON.stringify(data.sources || []),
          },
        ]);

      if (assistantMsgError) throw assistantMsgError;

      // Refresh sidebar
      loadChatSessions();
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error connecting to the backend or database.',
          sources: [],
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  // ---- Render ----
  return (
    <div style={styles.page}>
      {/* ---- Header ---- */}
      <header style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Optional: button to toggle sidebar on smaller screens */}
          <button
            style={{ ...styles.signOutBtn, background: 'transparent', color: '#fff', border: 'none' }}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            ☰
          </button>
          <h1 style={styles.headerTitle}>Unitwise Dashboard</h1>
        </div>

        <div style={styles.headerRight}>
          <span style={styles.email}>{session.user.email}</span>
          <button onClick={handleSignOut} style={styles.signOutBtn}>
            Sign Out
          </button>
        </div>
      </header>

      {/* ---- Main Layout ---- */}
      <div style={styles.mainArea}>
        {/* Sidebar */}
        {isSidebarOpen && (
          <aside style={styles.sidebar}>
            <div style={styles.sidebarInner}>
              <button style={styles.newChatBtn} onClick={createNewChat}>
                + New Chat
              </button>

              <div style={styles.chatList}>
                {chatSessions.map((chat) => (
                  <div
                    key={chat.id}
                    style={styles.chatListItem(currentChatId === chat.id)}
                    onClick={() => loadMessagesForChat(chat.id)}
                  >
                    <div style={styles.chatListTitle}>{chat.title || "Study Session"}</div>
                    <div style={styles.chatListSubject}>{chat.subject}</div>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        )}

        {/* ---- Main Chat Area ---- */}
        <main style={styles.chatContainer}>
          <div style={styles.messageListWrapper}>
            {/* Messages List */}
            <div style={styles.messageList}>
              {messages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={idx}
                    style={{
                      ...styles.messageRow,
                      ...(isUser ? styles.userRow : styles.assistantRow),
                    }}
                  >
                    <div
                      style={{
                        ...styles.bubble,
                        ...(isUser ? styles.userBubble : styles.assistantBubble),
                      }}
                    >
                      <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                      {/* Render Sources if available */}
                      {!isUser && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                        <div style={styles.sourcesContainer}>
                          <div style={styles.sourceTitle}>Sources:</div>
                          <div style={styles.sourcePillContainer}>
                            {msg.sources.map((src, i) => (
                              <span key={i} style={styles.sourcePill}>{src}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Loading Indicator */}
              {isLoading && (
                <div style={styles.typingIndicator}>
                  Typing...
                </div>
              )}

              {/* Dummy div to scroll to bottom */}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Form */}
          <div style={styles.formContainer}>
            <form style={styles.form} onSubmit={sendMessage}>
              <select
                style={styles.select}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                <option value="Computer Networks" style={styles.selectOption}>
                  Computer Networks
                </option>
                <option value="Data Structures" style={styles.selectOption}>
                  Data Structures
                </option>
                <option value="Operating Systems" style={styles.selectOption}>
                  Operating Systems
                </option>
              </select>

              <input
                style={styles.input}
                type="text"
                placeholder="Ask a question about the syllabus..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isLoading}
              />

              <button
                type="submit"
                style={{
                  ...styles.sendBtn,
                  opacity: isLoading || !inputValue.trim() ? 0.6 : 1,
                }}
                disabled={isLoading || !inputValue.trim()}
              >
                Send
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
