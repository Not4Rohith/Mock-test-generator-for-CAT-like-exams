import React, { useState, useEffect, Component } from 'react';
import 'katex/dist/katex.min.css';
import Latex from 'react-katex';
import { Timer, ChevronRight, ChevronLeft } from 'lucide-react';

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
          <img 
            src={src.startsWith('http') ? src : `/${src.startsWith('/') ? src.slice(1) : src}`} 
            alt={`Figure ${idx + 1}`} 
            className="max-w-full h-auto"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </div>
      ))}
    </div>
  );
};

export default function PracticeInterface({ testData, settings, onExit }) {
  // --- SESSION PERSISTENCE ---
  // Note: Since practice IDs are random, we use a generic 'current_practice_session' 
  // OR rely on App.jsx sending the same testData ID. App.jsx saves activeData, so ID is stable.
  const SESSION_KEY = `session_${testData.id || 'practice'}`;
  
  const loadSession = () => {
    const saved = localStorage.getItem(SESSION_KEY);
    return saved ? JSON.parse(saved) : null;
  };
  const initialSession = loadSession() || {};

  const [currentQIndex, setCurrentQIndex] = useState(initialSession.currentQIndex || 0);
  const [answers, setAnswers] = useState(initialSession.answers || {});
  const [timeLeft, setTimeLeft] = useState(initialSession.timeLeft !== undefined ? initialSession.timeLeft : settings.timeLimit * 60);

  // --- SAVE STATE ---
  useEffect(() => {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
        currentQIndex,
        answers,
        timeLeft
    }));
  }, [currentQIndex, answers, timeLeft, SESSION_KEY]);


  useEffect(() => {
    if (settings.timeLimit === 0) return; 
    const timer = setInterval(() => {
        setTimeLeft((prev) => {
            if (prev <= 1) {
                if(window.confirm("Time's up! Submit?")) onExit(answers);
                return 0;
            }
            return prev - 1;
        });
    }, 1000);
    return () => clearInterval(timer);
  }, [settings.timeLimit]);

  const questions = testData.questions;
  const currentQuestion = questions[currentQIndex];

  const clean = (text) => {
      if(!text) return "";
      return String(text).replace(/â€™/g, "'").replace(/â€œ/g, '"').replace(/â€/g, '"').replace(/&nbsp;/g, " ").replace(/<[^>]+>/g, '');
  };

  const RenderText = ({ text }) => {
    if (!text) return null;
    return <span className="leading-7 tracking-wide whitespace-pre-line"><SafeLatex>{clean(text)}</SafeLatex></span>;
  };

  const handleOptionSelect = (optId) => {
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: optId }));
  };

  const hasPassage = currentQuestion?.context_passage && String(currentQuestion.context_passage).length > 50;

  return (
    <div className="flex flex-col h-screen bg-obsidian text-gray-200 font-sans">
      
      {/* HEADER */}
      <div className="h-16 border-b border-subtle flex items-center justify-between px-6 bg-charcoal shrink-0">
        <div>
           <h2 className="font-bold text-white">Practice Mode</h2>
           <span className="text-xs text-accent uppercase tracking-widest">{settings.section} • {settings.count} Qs</span>
        </div>
        
        {settings.timeLimit > 0 && (
            <div className="bg-black/40 px-4 py-2 rounded-lg border border-gray-800 flex items-center gap-3">
                <Timer size={20} className="text-accent" />
                <span className={`font-mono text-xl font-bold ${timeLeft < 60 ? 'text-red-500' : 'text-white'}`}>
                    {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                </span>
            </div>
        )}
      </div>

      {/* CONTENT AREA */}
      <div className="flex-1 overflow-hidden flex flex-row">
        {hasPassage && (
            <div className="w-1/2 border-r border-subtle h-full overflow-y-auto p-8 bg-[#161616] custom-scrollbar">
                <div className="text-lg leading-8 text-gray-300 font-serif"><RenderText text={currentQuestion.context_passage} /></div>
                <ImageDisplay images={currentQuestion.images} singleUrl={currentQuestion.image_url} />
            </div>
        )}
        <div className={`h-full overflow-y-auto p-8 flex flex-col custom-scrollbar ${hasPassage ? 'w-1/2' : 'w-full max-w-5xl mx-auto'}`}>
            <div className="flex justify-between items-end mb-6 border-b border-gray-800 pb-4">
                <span className="text-accent font-mono font-bold text-lg">Q.{currentQIndex + 1}</span>
            </div>
            <div className="text-xl font-medium text-white mb-2 leading-relaxed"><RenderText text={currentQuestion.question_text} /></div>
            {!hasPassage && <ImageDisplay images={currentQuestion.images} singleUrl={currentQuestion.image_url} />}

            <div className="space-y-4 mb-10 mt-6">
                {currentQuestion.options && currentQuestion.options.length > 0 ? (
                    currentQuestion.options.map((opt, idx) => {
                        const optText = typeof opt === 'string' ? opt : opt.text; 
                        const isSelected = answers[currentQuestion.id] === (opt.id || optText); 
                        return (
                            <button key={idx} onClick={() => handleOptionSelect(opt.id || optText)} className={`w-full text-left p-5 rounded-xl border transition-all flex items-start gap-4 ${isSelected ? 'bg-emerald-900/20 border-accent text-white' : 'bg-charcoal border-subtle text-gray-400'}`}>
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

      {/* FOOTER */}
      <div className="h-20 border-t border-subtle bg-charcoal flex items-center justify-between px-8 shrink-0">
        <button onClick={() => setCurrentQIndex(Math.max(0, currentQIndex-1))} disabled={currentQIndex === 0} className="text-gray-400 hover:text-white flex items-center gap-2"><ChevronLeft size={20} /> Prev</button>
        <button onClick={() => { if(window.confirm("Submit Practice Session?")) onExit(answers); }} className="text-red-400 border border-red-900/50 px-6 py-2 rounded hover:bg-red-900/20">Finish</button>
        <button onClick={() => setCurrentQIndex(Math.min(questions.length-1, currentQIndex+1))} disabled={currentQIndex === questions.length-1} className="bg-accent text-black font-bold px-8 py-3 rounded-full flex items-center gap-2">Next <ChevronRight size={20} /></button>
      </div>
    </div>
  );
}