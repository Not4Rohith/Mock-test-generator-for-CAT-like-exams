import React, { useState, useEffect, useRef, Component, useCallback } from 'react';
import 'katex/dist/katex.min.css';
import Latex from 'react-katex';
import { Timer, ChevronRight, ChevronLeft, GripVertical } from 'lucide-react';

class SafeLatex extends Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() { if (this.state.hasError) return <span>{this.props.children}</span>; return <Latex>{this.props.children}</Latex>; }
}

const ImageDisplay = ({ images, singleUrl }) => {
  const imgs = (images && images.length > 0) ? images : (singleUrl ? [singleUrl] : []);
  if (imgs.length === 0) return null;
  return (
    <div className="flex flex-col gap-4 my-6">
      {imgs.map((src, idx) => (
        <div key={idx} className="border border-gray-700 rounded p-2 bg-black inline-block self-start">
          <img src={src.startsWith('http') ? src : `/${src.startsWith('/') ? src.slice(1) : src}`} alt={`Figure ${idx + 1}`} className="max-w-full h-auto" onError={(e) => { e.target.style.display = 'none'; }} />
        </div>
      ))}
    </div>
  );
};

export default function PracticeInterface({ testData, settings, onExit }) {
  const SESSION_KEY = `session_${testData.id || 'practice'}`;
  
  const loadSession = () => {
    const saved = localStorage.getItem(SESSION_KEY);
    return saved ? JSON.parse(saved) : null;
  };
  const initialSession = loadSession() || {};

  const [currentQIndex, setCurrentQIndex] = useState(initialSession.currentQIndex || 0);
  const [answers, setAnswers] = useState(initialSession.answers || {});
  const [visited, setVisited] = useState(initialSession.visited || {}); 
  const [timeLeft, setTimeLeft] = useState(initialSession.timeLeft !== undefined ? initialSession.timeLeft : settings.timeLimit * 60);
  const isSubmitting = useRef(false);

  const [sidebarWidth, setSidebarWidth] = useState(260); 
  const [passageWidth, setPassageWidth] = useState(50);
  const [isResizing, setIsResizing] = useState(null);

  const questions = testData.questions;
  const currentQuestion = questions[currentQIndex];

  const startResizing = useCallback((type) => setIsResizing(type), []);
  const stopResizing = useCallback(() => setIsResizing(null), []);

  const resize = useCallback((e) => {
    if (isResizing === 'sidebar') {
      const newWidth = e.clientX;
      if (newWidth > 70 && newWidth < 600) setSidebarWidth(newWidth);
    } 
    else if (isResizing === 'passage') {
        const contentLeft = sidebarWidth;
        const totalContentWidth = window.innerWidth - contentLeft;
        const relativeX = e.clientX - contentLeft;
        const newPercent = (relativeX / totalContentWidth) * 100;
        if (newPercent > 20 && newPercent < 80) setPassageWidth(newPercent);
    }
  }, [isResizing, sidebarWidth]);

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    } else {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    }
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  useEffect(() => {
      setVisited(prev => ({ ...prev, [questions[currentQIndex].id]: true }));
  }, [currentQIndex, questions]);

  useEffect(() => {
    if (!isSubmitting.current) {
        localStorage.setItem(SESSION_KEY, JSON.stringify({ currentQIndex, answers, visited, timeLeft }));
    }
  }, [currentQIndex, answers, visited, timeLeft, SESSION_KEY]);

  const handleSubmit = () => {
      isSubmitting.current = true;
      onExit(answers);
  };

  useEffect(() => {
    if (settings.timeLimit === 0) return; 
    const timer = setInterval(() => {
        setTimeLeft((prev) => {
            if (prev <= 1) { alert("Time's up!"); handleSubmit(); return 0; }
            return prev - 1;
        });
    }, 1000);
    return () => clearInterval(timer);
  }, [settings.timeLimit]);

  const clean = (text) => String(text || "").replace(/â€™/g, "'").replace(/â€œ/g, '"').replace(/â€/g, '"').replace(/&nbsp;/g, " ").replace(/<[^>]+>/g, '');
  const RenderText = ({ text }) => text ? <span className="leading-7 tracking-wide whitespace-pre-line"><SafeLatex>{clean(text)}</SafeLatex></span> : null;

  const handleOptionSelect = (optId) => setAnswers(prev => ({ ...prev, [currentQuestion.id]: optId }));
  const hasPassage = currentQuestion?.context_passage && String(currentQuestion.context_passage).length > 50;

  const getStatusColor = (qId, idx) => {
      if (currentQIndex === idx) return "border-blue-500 border-2 bg-blue-900/30 text-white";
      if (answers[qId]) return "bg-emerald-600 text-white border-emerald-600";
      if (visited[qId]) return "bg-red-900/50 text-red-200 border-red-800";
      return "bg-charcoal text-gray-500 border-gray-700";
  };

  return (
    <div className="flex h-screen bg-obsidian text-gray-200 font-sans overflow-hidden">
      
      {/* SIDEBAR */}
      <div style={{ width: sidebarWidth }} className="bg-charcoal border-r border-subtle flex flex-col shrink-0 z-20">
          <div className="p-4 border-b border-subtle">
              <h2 className="font-bold text-white mb-1 truncate">Palette</h2>
              <p className="text-xs text-gray-500 truncate">Questions</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
              <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(40px, 1fr))' }}>
                  {questions.map((q, idx) => (
                      <button key={q.id} onClick={() => setCurrentQIndex(idx)} className={`h-10 w-10 rounded-lg flex items-center justify-center text-sm font-bold border transition-all hover:scale-105 ${getStatusColor(q.id, idx)}`}>
                          {idx + 1}
                      </button>
                  ))}
              </div>
          </div>
          <div className="p-4 border-t border-subtle bg-black/20">
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-4">
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-emerald-600"></div> <span className="truncate">Ans</span></div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-red-900/50 border border-red-800"></div> <span className="truncate">Skip</span></div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-charcoal border border-gray-700"></div> <span className="truncate">New</span></div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded border-2 border-blue-500"></div> <span className="truncate">Now</span></div>
              </div>
              <button onClick={() => { if(window.confirm("Submit Practice?")) handleSubmit(); }} className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg transition-colors truncate">Submit</button>
          </div>
      </div>

      {/* --- SIDEBAR RESIZER (NAVY BLUE) --- */}
      <div 
        onMouseDown={() => startResizing('sidebar')} 
        className="w-1.5 bg-blue-950 hover:bg-blue-600 cursor-col-resize z-30 flex items-center justify-center transition-colors border-l border-r border-black/20"
      >
        <div className="h-8 w-0.5 bg-blue-400/30 rounded-full" />
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col min-w-0">
          <div className="h-16 border-b border-subtle flex items-center justify-between px-8 bg-charcoal shrink-0">
            <div><h2 className="font-bold text-white text-lg">Practice Mode</h2><span className="text-xs text-accent uppercase tracking-widest">{settings.section}</span></div>
            {settings.timeLimit > 0 && (
                <div className="bg-black/40 px-4 py-2 rounded-lg border border-gray-800 flex items-center gap-3">
                    <Timer size={20} className="text-accent" />
                    <span className={`font-mono text-xl font-bold ${timeLeft < 60 ? 'text-red-500' : 'text-white'}`}>{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</span>
                </div>
            )}
          </div>

          <div className="flex-1 overflow-hidden flex flex-row">
            {hasPassage && (
                <>
                    <div style={{ width: `${passageWidth}%` }} className="border-r border-subtle h-full overflow-y-auto p-8 bg-[#161616] custom-scrollbar">
                        <div className="text-lg leading-8 text-gray-300 font-serif"><RenderText text={currentQuestion.context_passage} /></div>
                        <ImageDisplay images={currentQuestion.images} singleUrl={currentQuestion.image_url} />
                    </div>
                    {/* --- PASSAGE RESIZER (NAVY BLUE) --- */}
                    <div 
                        onMouseDown={() => startResizing('passage')} 
                        className="w-1.5 bg-blue-950 hover:bg-blue-600 cursor-col-resize z-30 flex items-center justify-center transition-colors border-l border-r border-black/20"
                    >
                        <GripVertical size={12} className="text-blue-400/50" />
                    </div>
                </>
            )}
            <div className="flex-1 h-full overflow-y-auto p-8 flex flex-col custom-scrollbar">
                <div className="flex justify-between items-end mb-6 border-b border-gray-800 pb-4"><span className="text-accent font-mono font-bold text-lg">Q.{currentQIndex + 1}</span></div>
                <div className="text-xl font-medium text-white mb-2 leading-relaxed"><RenderText text={currentQuestion.question_text} /></div>
                {!hasPassage && <ImageDisplay images={currentQuestion.images} singleUrl={currentQuestion.image_url} />}
                <div className="space-y-4 mb-10 mt-6">
                    {currentQuestion.options && currentQuestion.options.length > 0 ? (
                        currentQuestion.options.map((opt, idx) => {
                            const optText = typeof opt === 'string' ? opt : opt.text; 
                            const isSelected = answers[currentQuestion.id] === (opt.id || optText); 
                            return (
                                <button key={idx} onClick={() => handleOptionSelect(opt.id || optText)} className={`w-full text-left p-5 rounded-xl border transition-all flex items-start gap-4 ${isSelected ? 'bg-emerald-900/20 border-accent text-white shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'bg-charcoal border-subtle text-gray-400 hover:bg-[#252525]'}`}>
                                    <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shrink-0 ${isSelected ? 'bg-accent border-accent text-black' : 'border-gray-600'}`}>{String.fromCharCode(65 + idx)}</div>
                                    <div className="text-lg pt-0.5"><RenderText text={optText} /></div>
                                </button>
                            )
                        })
                    ) : (
                        <div className="bg-black/30 p-6 rounded-xl border border-dashed border-gray-700">
                            <label className="text-gray-400 text-sm block mb-3">TITA / No Options:</label>
                            <input type="text" className="w-full bg-charcoal border border-subtle p-4 rounded text-white font-mono text-xl" placeholder="Enter answer..." onChange={(e) => handleOptionSelect(e.target.value)} value={answers[currentQuestion.id] || ''} />
                        </div>
                    )}
                </div>
            </div>
          </div>

          <div className="h-20 border-t border-subtle bg-charcoal flex items-center justify-between px-8 shrink-0">
            <button onClick={() => setCurrentQIndex(Math.max(0, currentQIndex-1))} disabled={currentQIndex === 0} className="text-gray-400 hover:text-white flex items-center gap-2"><ChevronLeft size={20} /> Previous</button>
            <button onClick={() => setCurrentQIndex(Math.min(questions.length-1, currentQIndex+1))} disabled={currentQIndex === questions.length-1} className="bg-accent text-black font-bold px-8 py-3 rounded-full flex items-center gap-2 hover:bg-emerald-400 shadow-lg shadow-emerald-900/20 transition-all">Save & Next <ChevronRight size={20} /></button>
          </div>
      </div>
    </div>
  );
}