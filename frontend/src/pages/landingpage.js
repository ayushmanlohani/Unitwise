import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, CheckCircle2,
  ChevronDown, Send,
  ShieldCheck, Cpu
} from 'lucide-react';

// Real Unitwise Subjects and multi-mode data from syllabus.yaml
const REAL_SUBJECTS = {
  CN: {
    code: "NCS-601",
    short: "CN",
    name: "Computer Networks",
    unit: "Unit IV: Transport Layer & TCP Protocols",
    question: "Explain the TCP 3-Way Handshake and why Initial Sequence Numbers (ISN) are randomized.",
    sources: [
      "Tanenbaum — Computer Networks, 5th Ed. §6.2 (pp. 498–505)",
      "Forouzan — Data Communications and Networking, 4th Ed. §23.3 (pp. 712–718)"
    ],
    modes: {
      'Exam Prep': {
        icon: '📝',
        summary: 'Structured 10-Mark Answer with Protocol Sequence',
        blocks: [
          {
            title: "1. Definition & Core Objective",
            content: "The TCP 3-Way Handshake is a state synchronization protocol designed to establish a reliable, full-duplex byte-stream connection between client and server before data transfer begins."
          },
          {
            title: "2. The 3-Step Handshake Protocol",
            isCode: true,
            content: `Step 1: Client -> Server [SYN, seq = x]
        Client enters SYN-SENT. Advertises its Initial Sequence Number (ISN_c = x).

Step 2: Server -> Client [SYN-ACK, seq = y, ack = x + 1]
        Server enters SYN-RCVD. Acknowledges client's ISN and provides its own (ISN_s = y).

Step 3: Client -> Server [ACK, ack = y + 1]
        Client enters ESTABLISHED. Server enters ESTABLISHED upon receipt.`
          },
          {
            title: "3. Why ISN Must Be Randomized (Security & Replay Protection)",
            content: "• Prevents Old Duplicate Collision: Stale delayed packets from terminated connections cannot be misinterpreted as part of the new stream.\n• TCP Sequence Prediction Attacks: If ISN increments predictably (e.g., +64k/sec), an off-path attacker can forge packets and hijack sessions (Kevin Mitnick / Bellovin vulnerability)."
          }
        ]
      },
      'Academic': {
        icon: '🎓',
        summary: 'Rigorous Formal Derivation & State Machine Analysis',
        blocks: [
          {
            title: "Theoretical Necessity of Three Messages",
            content: "In an unreliable channel with packet loss and arbitrary transmission delay, two messages are provably insufficient to achieve mutual consensus on initial sequence numbers (Solving the Two Generals Paradox for transport layers)."
          },
          {
            title: "Formal Sequence Consumption Invariant",
            content: "The SYN and FIN control flags each logically consume exactly 1 sequence number space ($$x \\to x + 1$$) to guarantee reliable acknowledgment through the standard TCP cumulative ACK mechanism, even though they carry zero payload bytes."
          }
        ]
      },
      'Revision': {
        icon: '⚡',
        summary: 'High-Yield Memory Trigger (60-Second Cram)',
        blocks: [
          {
            title: "Quick Formula & Diagram",
            isCode: true,
            content: `SYN (x)  -->  SYN-ACK (y, x+1)  -->  ACK (y+1)
• SYN consumes 1 byte in seq space.
• Random ISN prevents sequence guessing and delayed duplicate ghost packets.
• States: LISTEN -> SYN-SENT -> SYN-RCVD -> ESTABLISHED.`
          }
        ]
      }
    }
  },
  DIP: {
    code: "NCS-602",
    short: "DIP",
    name: "Digital Image Processing",
    unit: "Unit II: Spatial Domain & Histogram Processing",
    question: "Derive the Histogram Equalization transformation function and explain why it flattens the CDF.",
    sources: [
      "Gonzalez & Woods — Digital Image Processing, 4th Ed. §3.3 (pp. 135–144)",
      "Jayaraman — Digital Image Processing §5.2 (pp. 250–258)"
    ],
    modes: {
      'Exam Prep': {
        icon: '📝',
        summary: '10-Mark Marking Scheme Answer',
        blocks: [
          {
            title: "1. Concept & Transformation Function",
            content: "Histogram Equalization is a spatial-domain contrast enhancement technique that spreads pixel intensity distributions uniformly across the entire dynamic range [0, L - 1]."
          },
          {
            title: "2. Continuous Mathematical Derivation",
            content: "Given continuous normalized intensity r ∈ [0, 1] with PDF p_r(r), the transformation is defined via the Cumulative Distribution Function (CDF):\n\ns = T(r) = ∫ p_r(w) dw  (from 0 to r)\n\nApplying fundamental probability transformation rule p_s(s) = p_r(r) * |dr/ds|:\nSince ds/dr = d/dr [∫ p_r(w) dw] = p_r(r), we get:\np_s(s) = p_r(r) * (1 / p_r(r)) = 1 (Uniform Distribution)."
          },
          {
            title: "3. Discrete Mapping Formula for Image Pixels",
            isCode: true,
            content: `s_k = T(r_k) = round[ (L - 1) * Σ (n_j / MN) ]  for j = 0 to k
Where:
• MN = total pixels
• n_j = frequency of gray level r_j
• L = total intensity levels (256 for 8-bit images)`
          }
        ]
      },
      'Academic': {
        icon: '🎓',
        summary: 'Rigorous Probability Integral Transform',
        blocks: [
          {
            title: "Monotonicity Invariant",
            content: "T(r) is strictly monotonically increasing for 0 ≤ r ≤ 1, ensuring that the original gray-scale order is preserved and inverse mapping T⁻¹(s) is mathematically well-defined."
          }
        ]
      },
      'Revision': {
        icon: '⚡',
        summary: 'Ultra-Condensed Formula Sheet',
        blocks: [
          {
            title: "Exam Key Points",
            isCode: true,
            content: `Formula: s_k = round( (L-1) * CDF(k) )
• CDF of any random variable transforms its output into a Uniform Distribution.
• Result: Maximized global contrast, flat continuous histogram.`
          }
        ]
      }
    }
  },
  EML: {
    code: "NAI-601",
    short: "EML",
    name: "Essentials of Machine Learning",
    unit: "Unit III: Neural Networks & Optimization",
    question: "Derive the Backpropagation gradient update rule for hidden-to-output weights using the Chain Rule.",
    sources: [
      "Alpaydin — Introduction to Machine Learning §11.3 (pp. 271–280)",
      "Geron — Hands-On Machine Learning with Scikit-Learn and TF Ch. 10"
    ],
    modes: {
      'Exam Prep': {
        icon: '📝',
        summary: '10-Mark Step-by-Step Derivation',
        blocks: [
          {
            title: "1. Network Architecture & Loss Function",
            content: "Consider a network with Mean Squared Error loss E = 0.5 * Σ (t_k - y_k)², where output activation y_k = σ(z_k) and net input z_k = Σ w_kj * h_j."
          },
          {
            title: "2. Output Weight Gradient Derivation via Chain Rule",
            content: "∂E / ∂w_kj = (∂E / ∂y_k) * (∂y_k / ∂z_k) * (∂z_k / ∂w_kj)\n\n• Term 1: ∂E / ∂y_k = -(t_k - y_k)\n• Term 2: ∂y_k / ∂z_k = σ'(z_k) = y_k * (1 - y_k) [for Sigmoid]\n• Term 3: ∂z_k / ∂w_kj = h_j (hidden neuron output)\n\nDefining Error Gradient δ_k = (t_k - y_k) * y_k * (1 - y_k), the final weight update is:\nΔw_kj = η * δ_k * h_j"
          }
        ]
      },
      'Academic': {
        icon: '🎓',
        summary: 'Generalized Vectorized Backprop & Hessian Conditioning',
        blocks: [
          {
            title: "Jacobian Form Formulation",
            content: "∇_W E = δ · (h)^T. Vanishing gradient occurs when σ'(z) → 0 for saturated activations, leading to the theoretical adoption of ReLU: max(0, z)."
          }
        ]
      },
      'Revision': {
        icon: '⚡',
        summary: 'Core Equation & Cheat Formula',
        blocks: [
          {
            title: "3-Step Chain Rule Summary",
            isCode: true,
            content: `Δw_kj = η * δ_k * h_j
Where:
• Output layer error: δ_k = (t_k - y_k) * σ'(z_k)
• Hidden layer error: δ_j = [Σ δ_k * w_kj] * σ'(z_j)`
          }
        ]
      }
    }
  }
};

const ALL_MODES = [
  { id: 'Exam Prep', icon: '📝', desc: 'High-Yield 10-Mark Format' },
  { id: 'Academic', icon: '🎓', desc: 'Formal Textbook Derivations' },
  { id: 'Revision', icon: '⚡', desc: 'Concise 60-Sec TL;DR' },
  { id: 'Simplified', icon: '💡', desc: 'Simple & Clear Concepts' },
  { id: 'Analogy', icon: '🎭', desc: 'Real-world Metaphors' }
];

export default function LandingPage() {
  const navigate = useNavigate();
  const [selectedSubjectKey, setSelectedSubjectKey] = useState('CN');
  const [selectedModeKey, setSelectedModeKey] = useState('Exam Prep');
  const [sourcesOpen, setSourcesOpen] = useState(true);

  const currentSubject = REAL_SUBJECTS[selectedSubjectKey];
  const currentModeData = currentSubject.modes[selectedModeKey] || currentSubject.modes['Exam Prep'];

  return (
    <div className="min-h-screen bg-[#f5f4ed] text-[#141413] selection:bg-[#e8e6dc] selection:text-[#141413] font-sans antialiased relative overflow-x-hidden">
      
      {/* 1. Global Typography Injections */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        .font-serif-editorial {
          font-family: 'Instrument Serif', Georgia, serif;
        }
        .font-mono-code {
          font-family: 'JetBrains Mono', monospace;
        }
        .paper-grain {
          background-image: radial-gradient(rgba(20, 20, 19, 0.04) 1px, transparent 1px);
          background-size: 24px 24px;
        }
      `}</style>

      {/* Subtle academic background grain */}
      <div className="fixed inset-0 pointer-events-none paper-grain opacity-70 z-0" />

      {/* 2. Top Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[#faf9f5]/85 border-b border-[#f0eee6]">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between relative">

          {/* Logo & Identity */}
          <div className="flex items-center gap-0.5 cursor-pointer" onClick={() => navigate('/')}>
            <img
              src={`${process.env.PUBLIC_URL}/unitwise-logo.png`}
              alt="Unitwise"
              className="w-12 h-12 md:w-[52px] md:h-[52px] object-contain shrink-0 select-none"
            />
            <div className="flex flex-col justify-center">
              <span className="font-serif-editorial text-[27px] tracking-tight font-medium text-[#141413] leading-[1.05]">
                Unitwise
              </span>
              <span className="font-mono-code text-[11px] tracking-widest text-[#87867f] uppercase mt-0.5">
                Curriculum Intelligence
              </span>
            </div>
          </div>

          {/* Academic Status Pill (Mathematically Centered) */}
          <div className="hidden md:flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-[#e8e6dc] bg-[#faf9f5] text-xs text-[#5e5d59] shadow-sm absolute left-1/2 -translate-x-1/2">
            <span className="w-2 h-2 rounded-full bg-[#34A853] animate-pulse" />
            <span className="font-mono-code text-[11px] font-medium tracking-wide">
              SYLLABUS ARCHIVE // 6TH SEMESTER B.TECH
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-xs font-medium text-[#5e5d59] hover:text-[#141413] px-3.5 py-2 rounded-lg transition-colors cursor-pointer"
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-xs font-semibold text-[#faf9f5] bg-[#141413] hover:bg-[#2a2926] px-4 py-2.5 rounded-lg transition-all shadow-sm flex items-center gap-1.5 cursor-pointer group active:scale-95"
            >
              <span>Start Studying</span>
              <span className="text-[13px] text-[#faf9f5]/80 group-hover:translate-x-0.5 transition-transform">→</span>
            </button>
          </div>
        </div>
      </header>

      {/* 3. Hero Copy */}
      <section className="relative z-10 pt-16 pb-10 px-6 max-w-5xl mx-auto text-center">

        {/* Master Headline */}
        <h1 className="font-serif-editorial text-5xl sm:text-7xl md:text-8xl tracking-tight text-[#141413] leading-[1.05] mb-6 font-normal">
          Your syllabus, beautifully <br />
          <em className="italic font-serif-editorial text-[#c96442]">understood</em> and exam-ready.
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-[#5e5d59] max-w-2xl mx-auto leading-relaxed mb-8 font-normal">
          Stop hunting for seniors’ notes and wasting hours on random YouTube lectures that aren’t even on the LU exam. Just ask your question and get a syllabus-locked, 10-mark answer ready to write.
        </p>

        {/* Subject & Mode Interactive Filters directly on the Hero */}
        <div className="flex flex-col items-center gap-4 mb-10">

          {/* Real Subjects Selector */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="font-mono-code text-xs text-[#87867f] uppercase tracking-wider mr-2 font-medium">
              Active Course:
            </span>
            {[
              { key: 'CN', label: 'Computer Networks (CN)' },
              { key: 'DIP', label: 'Digital Image Processing (DIP)' },
              { key: 'EML', label: 'Machine Learning (EML)' },
            ].map(item => (
              <button
                key={item.key}
                type="button"
                onClick={() => setSelectedSubjectKey(item.key)}
                className={`font-mono-code text-xs px-3.5 py-1.5 rounded-lg border transition-all cursor-pointer ${selectedSubjectKey === item.key
                  ? 'bg-[#141413] text-[#faf9f5] border-[#141413] shadow-sm'
                  : 'bg-[#faf9f5] text-[#4d4c48] border-[#e8e6dc] hover:border-[#87867f]'
                  }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Real 5 Study Modes Selector */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="font-mono-code text-xs text-[#87867f] uppercase tracking-wider mr-2 font-medium">
              Study Mode:
            </span>
            {ALL_MODES.map(mode => {
              const isSelected = selectedModeKey === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => setSelectedModeKey(mode.id)}
                  className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all cursor-pointer ${isSelected
                    ? 'bg-[#c96442] text-[#faf9f5] border-[#c96442] shadow-sm font-semibold'
                    : 'bg-[#faf9f5] text-[#5e5d59] border-[#e8e6dc] hover:border-[#87867f]'
                    }`}
                >
                  <span>{mode.icon}</span>
                  <span>{mode.id}</span>
                </button>
              );
            })}
          </div>

        </div>
      </section>

      {/* 4. THE AUTHENTIC UNITWISE DASHBOARD CARD (Reflecting ChatDashboard) */}
      <section className="relative z-10 px-4 sm:px-6 max-w-6xl mx-auto mb-24">

        {/* Outer Dashboard Window Container with Parchment / Ivory Depth */}
        <div className="rounded-2xl border border-[#e8e6dc] bg-[#faf9f5] shadow-whisper overflow-hidden flex flex-col md:flex-row min-h-[580px]">

          {/* LEFT: Mini Unitwise Sidebar */}
          <aside className="w-full md:w-64 bg-[#f5f4ed] border-b md:border-b-0 md:border-r border-[#f0eee6] p-4 flex flex-col justify-between shrink-0">
            <div>
              {/* App Brand & New Chat */}
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                  <img
                    src={`${process.env.PUBLIC_URL}/unitwise-logo.png`}
                    alt="Unitwise"
                    className="w-6 h-6 object-contain shrink-0 select-none"
                  />
                  <span className="font-serif-editorial text-lg font-medium text-[#141413] leading-none">
                    Unitwise
                  </span>
                </div>
                <span className="text-[10px] font-mono-code px-2 py-0.5 rounded bg-[#e8e6dc] text-[#5e5d59]">
                  v2.4
                </span>
              </div>

              {/* Fake New Chat Button */}
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="w-full mb-6 py-2 px-3 rounded-lg border border-[#e8e6dc] bg-[#faf9f5] text-xs font-medium text-[#4d4c48] flex items-center justify-between shadow-sm cursor-pointer hover:bg-[#f0eee6] transition-colors"
              >
                <span>+ New Study Session</span>
                <span className="font-mono-code text-[10px] text-[#87867f]">⌘K</span>
              </button>

              {/* Recent Sessions List (Real Subjects) */}
              <div className="text-[11px] font-mono-code text-[#87867f] uppercase tracking-wider mb-2 px-1">
                Recent Chats
              </div>
              <div className="space-y-1">
                {[
                  { title: "TCP 3-Way Handshake", sub: "CN", active: selectedSubjectKey === 'CN' },
                  { title: "Histogram Equalization", sub: "DIP", active: selectedSubjectKey === 'DIP' },
                  { title: "Backprop Gradient Math", sub: "EML", active: selectedSubjectKey === 'EML' },
                  { title: "Fuzzy Logic Rules", sub: "SCT", active: false },
                  { title: "Apriori Itemsets", sub: "DMW", active: false },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className={`px-2.5 py-2 rounded-md text-xs flex items-center justify-between transition-colors ${item.active
                      ? 'bg-[#e8e6dc] text-[#141413] font-medium'
                      : 'text-[#5e5d59] hover:bg-[#faf9f5]/60'
                      }`}
                  >
                    <span className="truncate max-w-[140px]">{item.title}</span>
                    <span className="font-mono-code text-[9px] px-1.5 py-0.5 rounded bg-[#f5f4ed] border border-[#e8e6dc] text-[#87867f]">
                      {item.sub}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Profile Pill */}
            <div className="pt-4 border-t border-[#f0eee6] flex items-center justify-between mt-4">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-[#c96442] text-[#faf9f5] flex items-center justify-center text-xs font-medium shadow-ring-brand">
                  A
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-medium text-[#141413]">Student Session</span>
                  <span className="font-mono-code text-[10px] text-[#87867f]">B.Tech 6th Sem</span>
                </div>
              </div>
            </div>
          </aside>

          {/* RIGHT: Authentic Unitwise Chat Workspace */}
          <main className="flex-1 flex flex-col justify-between bg-[#faf9f5]">

            {/* Real Unitwise Top Workspace Header */}
            <header className="px-6 py-3.5 border-b border-[#f0eee6] bg-[#faf9f5]/80 backdrop-blur-sm flex items-center justify-between">

              {/* Mode Dropdown Visual */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/70 border border-stone-200 shadow-sm text-xs font-medium text-[#141413]">
                  <span>{currentModeData.icon || '📝'}</span>
                  <span>{selectedModeKey} Mode</span>
                  <ChevronDown className="w-3.5 h-3.5 text-[#87867f]" />
                </div>

                <span className="text-xs text-[#87867f] hidden sm:inline">
                  — {currentModeData.summary}
                </span>
              </div>

              {/* Subject Badge */}
              <div className="flex items-center gap-2">
                <span className="font-mono-code text-xs px-2.5 py-1 rounded-md bg-[#f5f4ed] border border-[#e8e6dc] text-[#4d4c48]">
                  {`${currentSubject.code} // ${currentSubject.short}`}
                </span>
              </div>
            </header>

            {/* Chat Messages Body */}
            <div className="p-6 sm:p-8 flex-1 overflow-y-auto space-y-6">

              {/* 1. Student Message Bubble */}
              <div className="flex justify-end">
                <div className="max-w-[85%] flex flex-col items-end">
                  <div className="bg-[#e8e6dc] text-[#141413] text-sm leading-relaxed p-4 rounded-xl shadow-sm">
                    {currentSubject.question}
                  </div>

                  {/* Mode Badge underneath User Message */}
                  <div className="mt-1 px-2 py-0.5 bg-stone-100 rounded text-[10px] text-stone-500 font-medium flex items-center gap-1">
                    <span>{currentModeData.icon}</span>
                    <span>{selectedModeKey}</span>
                  </div>
                </div>
              </div>

              {/* 2. Unitwise Assistant Answer */}
              <div className="flex justify-start">
                <div className="max-w-[92%] flex flex-col items-start w-full">
                  <div className="bg-[#faf9f5] text-[#141413] border border-[#f0eee6] shadow-whisper p-5 sm:p-6 rounded-xl w-full">

                    {/* Unit & Curriculum Sub-header */}
                    <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#f0eee6]">
                      <span className="font-mono-code text-xs font-semibold text-[#c96442] tracking-wide">
                        {currentSubject.unit}
                      </span>
                      <span className="font-mono-code text-[11px] text-[#87867f]">
                        Syllabus-Anchored Model Answer
                      </span>
                    </div>

                    {/* Content Blocks */}
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={`${selectedSubjectKey}-${selectedModeKey}`}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.2 }}
                        className="space-y-4"
                      >
                        {currentModeData.blocks.map((block, i) => (
                          <div key={i} className="space-y-1.5">
                            <h4 className="font-serif text-base font-semibold text-[#141413]">
                              {block.title}
                            </h4>
                            {block.isCode ? (
                              <pre className="font-mono-code text-xs bg-[#f5f4ed] p-3.5 rounded-lg border border-[#e8e6dc] text-[#141413] overflow-x-auto whitespace-pre-wrap leading-relaxed">
                                {block.content}
                              </pre>
                            ) : (
                              <p className="text-sm text-[#4d4c48] leading-relaxed whitespace-pre-line">
                                {block.content}
                              </p>
                            )}
                          </div>
                        ))}
                      </motion.div>
                    </AnimatePresence>

                    {/* Real Source Accordion */}
                    <div className="mt-5 border border-[#f0eee6] rounded-lg overflow-hidden bg-[#f5f4ed]/50">
                      <button
                        type="button"
                        onClick={() => setSourcesOpen(!sourcesOpen)}
                        className="w-full flex items-center justify-between px-3.5 py-2.5 text-xs text-[#4d4c48] font-medium hover:bg-[#f0eee6]/60 transition-colors border-none cursor-pointer bg-transparent"
                      >
                        <span className="flex items-center gap-2">
                          <BookOpen className="w-3.5 h-3.5 text-[#c96442]" />
                          <span>View Prescribed Sources ({currentSubject.sources.length})</span>
                        </span>
                        <ChevronDown
                          className="w-3.5 h-3.5 text-[#87867f] transition-transform duration-200"
                          style={{ transform: sourcesOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
                        />
                      </button>

                      {sourcesOpen && (
                        <div className="p-3 pt-1 flex flex-col gap-1.5 border-t border-[#f0eee6]">
                          {currentSubject.sources.map((src, i) => (
                            <div key={i} className="text-xs font-mono-code text-[#5e5d59] bg-[#faf9f5] p-2 rounded border border-[#e8e6dc] shadow-sm">
                              {src}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              </div>

            </div>

            {/* Simulated ChatInput Bar */}
            <div className="p-4 bg-[#faf9f5] border-t border-[#f0eee6]">
              <div 
                onClick={() => navigate('/login')}
                className="relative flex items-center rounded-xl bg-[#faf9f5] border border-[#e8e6dc] shadow-whisper p-2 cursor-pointer hover:border-[#c96442]/40 transition-colors"
              >
                <input
                  type="text"
                  readOnly
                  placeholder="Ask a question about your syllabus..."
                  className="flex-1 bg-transparent border-none px-3 text-sm text-[#141413] outline-none font-sans cursor-pointer"
                />

                <div className="flex items-center gap-2 shrink-0">
                  {/* Subject Dropdown Pill */}
                  <div className="relative flex items-center h-[34px]">
                    <div className="bg-[#f5f4ed] border border-[#f0eee6] text-[#4d4c48] text-xs font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5">
                      <span>{currentSubject.name}</span>
                      <ChevronDown className="w-3 h-3 text-[#87867f]" />
                    </div>
                  </div>

                  {/* Terracotta Send Button */}
                  <div className="bg-[#c96442] text-[#faf9f5] rounded-lg h-[34px] w-[40px] flex items-center justify-center shadow-ring-brand opacity-90">
                    <Send className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            </div>

          </main>
        </div>
      </section>

      {/* 5. THE PROJECT ARCHITECTURE (3-STAGE PIPELINE) */}
      <section className="relative z-10 px-6 max-w-6xl mx-auto mb-28">

        <div className="text-center max-w-4xl mx-auto mb-14">
          <span className="font-mono-code text-xs uppercase tracking-widest text-[#87867f] block mb-2 font-medium">
            System Design & Workflow
          </span>
          <h2 className="font-serif-editorial text-4xl sm:text-5xl text-[#141413] font-normal leading-tight">
            How Unitwise is engineered under the hood.
          </h2>
          <p className="text-sm text-[#5e5d59] mt-3 font-normal leading-relaxed max-w-4xl mx-auto">
            A production 3-stage RAG pipeline built with strict syllabus guardrails, cross-encoder neural reranking, and automated golden evaluation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Stage 1: Query Gating & Subject Isolation */}
          <div className="p-7 rounded-2xl bg-[#faf9f5] border border-[#e8e6dc] shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-[#f5f4ed] border border-[#e8e6dc] flex items-center justify-center text-[#c96442] mb-5">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="font-mono-code text-[11px] text-[#c96442] font-semibold tracking-wider uppercase block mb-1">
                Stage 01 // Ingestion & Gating
              </span>
              <h3 className="font-serif-editorial text-2xl text-[#141413] font-medium mb-3">
                Curriculum Gating & Vector Search
              </h3>
              <p className="text-sm text-[#5e5d59] leading-relaxed mb-6">
                Queries pass through a tier gatekeeper to block out-of-scope prompts, followed by strict metadata filtering in ChromaDB to prevent cross-subject contamination.
              </p>
            </div>

            {/* Structured Technical Highlights */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[#f5f4ed] border border-[#e8e6dc]">
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#c96442] font-bold">01</span>
                <span>Tier Gate: Blocks off-syllabus noise</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#c96442] font-bold">02</span>
                <span>Metadata Lock: (subject == target)</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#c96442] font-bold">03</span>
                <span>Dense Search: Cosine candidate pool</span>
              </div>
            </div>
          </div>

          {/* Stage 2: Cross-Encoder Reranking */}
          <div className="p-7 rounded-2xl bg-[#faf9f5] border border-[#e8e6dc] shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-[#f5f4ed] border border-[#e8e6dc] flex items-center justify-center text-[#2D5A46] mb-5">
                <Cpu className="w-5 h-5" />
              </div>
              <span className="font-mono-code text-[11px] text-[#2D5A46] font-semibold tracking-wider uppercase block mb-1">
                Stage 02 // Neural Re-ranking
              </span>
              <h3 className="font-serif-editorial text-2xl text-[#141413] font-medium mb-3">
                Cross-Encoder Precision Re-scoring
              </h3>
              <p className="text-sm text-[#5e5d59] leading-relaxed mb-6">
                Cosine similarity alone misses deep exam context. A dedicated Cross-Encoder jointly scores query-chunk pairs to distill the candidates down to the top-7 highest-signal passages.
              </p>
            </div>

            {/* Structured Technical Highlights */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[#f5f4ed] border border-[#e8e6dc]">
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#2D5A46] font-bold">01</span>
                <span>Joint Attention: Full pair re-scoring</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#2D5A46] font-bold">02</span>
                <span>Top-7 Distill: Textbook precision</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#2D5A46] font-bold">03</span>
                <span>Resilient: Silent cosine fallback</span>
              </div>
            </div>
          </div>

          {/* Stage 3: Multi-Mode Generation & Golden Evals */}
          <div className="p-7 rounded-2xl bg-[#faf9f5] border border-[#e8e6dc] shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-[#f5f4ed] border border-[#e8e6dc] flex items-center justify-center text-[#141413] mb-5">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="font-mono-code text-[11px] text-[#87867f] font-semibold tracking-wider uppercase block mb-1">
                Stage 03 // Synthesis & Evaluation
              </span>
              <h3 className="font-serif-editorial text-2xl text-[#141413] font-medium mb-3">
                Multi-Mode Output & LLM Judge
              </h3>
              <p className="text-sm text-[#5e5d59] leading-relaxed mb-6">
                Generates 5 tailored study modes with verifiable citations. Validated continuously against a golden evaluation test suite measuring chunk recall and answer faithfulness.
              </p>
            </div>

            {/* Structured Technical Highlights */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[#f5f4ed] border border-[#e8e6dc]">
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#141413] font-bold">01</span>
                <span>5 Study Modes: 10-Mark, TL;DR, Theory</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#141413] font-bold">02</span>
                <span>Strict Citations: Verified book & page</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono-code text-[#4d4c48]">
                <span className="text-[#141413] font-bold">03</span>
                <span>Judge Evals: Faithfulness & recall checks</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* 6. MINIMALIST ARCHIVAL FOOTER */}
      <footer className="border-t border-[#e8e6dc] bg-[#f5f4ed] py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-[#87867f] relative">

          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate('/')}>
            <img
              src={`${process.env.PUBLIC_URL}/unitwise-logo.png`}
              alt="Unitwise"
              className="w-6 h-6 object-contain shrink-0 opacity-90 select-none"
            />
            <span className="font-serif-editorial text-xl font-medium text-[#141413] leading-none">
              Unitwise
            </span>
          </div>

          <p className="font-serif-editorial text-sm italic text-[#5e5d59] md:absolute md:left-1/2 md:-translate-x-1/2 text-center pointer-events-none">
            "Built for university students who respect their time."
          </p>

          <div className="font-mono-code text-[11px] text-[#87867f] tracking-wider uppercase">
            Made by Ayushman Lohani
          </div>
        </div>
      </footer>

    </div>
  );
}