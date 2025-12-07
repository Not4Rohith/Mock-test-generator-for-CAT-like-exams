import React, { useState, useEffect, Component } from 'react';
import 'katex/dist/katex.min.css';
import Latex from 'react-katex';
import { Timer, ChevronRight, ChevronLeft } from 'lucide-react';

// --- 1. CRASH GUARD FOR MATH ---
class SafeLatex extends Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() { if (this.state.hasError) return <span>{this.props.children}</span>; return <Latex>{this.props.children}</Latex>; }
}

// --- 2. MULTI-IMAGE RENDERER HELPER ---
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

export default function TestInterface({ testData, onExit }) {
  // --- DETECT EXAM TYPE ---
  // If ID starts with "MAT", enable MAT features (Global Timer, Free Nav)
  const isMAT = testData.id && testData.id.startsWith("MAT");

  const SECTIONS = testData.sections ? Object.keys(testData.sections) : [];
  
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  
  // TIMER LOGIC: 
  // MAT = 120 mins (7200s) Total
  // CAT = 40 mins (2400s) Per Section
  const [timeLeft, setTimeLeft] = useState(isMAT ? 7200 : 2400); 

  useEffect(() => {
    const timer = setInterval(() => {
        setTimeLeft((prev) => {
            if (prev <= 1) {
                // Time Up Logic
                if (isMAT) {
                    // MAT: Global time up -> Submit whole test
                    alert("Time is up! Submitting exam.");
                    onExit(answers);
                    return 0;
                } else {
                    // CAT: Section time up -> Next Section
                    if (currentSectionIndex < SECTIONS.length - 1) {
                        handleSectionSwitch();
                        return 2400; // Reset for next section
                    } else {
                        onExit(answers); // Finish
                        return 0;
                    }
                }
            }
            return prev - 1;
        });
    }, 1000);
    return () => clearInterval(timer);
  }, [currentSectionIndex, isMAT]); // Dependency ensures CAT timer resets correctly

  // Safety Checks
  if (!testData || !SECTIONS.length) return <div className="p-10 text-white">Error: Empty Test Data</div>;
  
  const currentSectionName = SECTIONS[currentSectionIndex];
  const questions = testData.sections[currentSectionName];
  
  if (!questions || !questions.length) {
       return <div className="text-white p-10">Section {currentSectionName} is empty. <button onClick={onExit} className="underline">Exit</button></div>
  }
  
  const currentQuestion = questions[currentQIndex];

  // --- TEXT CLEANER ---
  const clean = (text) => {
      if(!text) return "";
      return String(text)
        .replace(/â€™/g, "'")
        .replace(/â€œ/g, '"')
        .replace(/â€/g, '"')
        .replace(/&nbsp;/g, " ")
        .replace(/<[^>]+>/g, ''); 
  };

  const RenderText = ({ text }) => {
    if (!text) return null;
    return <span className="leading-7 tracking-wide whitespace-pre-line"><SafeLatex>{clean(text)}</SafeLatex></span>;
  };

  const handleOptionSelect = (optId) => {
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: optId }));
  };

  const handleNext = () => {
    if (currentQIndex < questions.length - 1) setCurrentQIndex(currentQIndex + 1);
  };

  const handlePrev = () => {
    if (currentQIndex > 0) setCurrentQIndex(currentQIndex - 1);
  };

  // --- TAB CLICK (MAT Only) ---
  const handleTabClick = (idx) => {
      if (isMAT) {
          setCurrentSectionIndex(idx);
          setCurrentQIndex(0);
          // Do NOT reset timer for MAT
      }
  };

  const handleSectionSwitch = () => {
    if (currentSectionIndex < SECTIONS.length - 1) {
      setCurrentSectionIndex(currentSectionIndex + 1);
      setCurrentQIndex(0);
      
      // Only Reset Timer for CAT
      if (!isMAT) setTimeLeft(2400); 
      
    } else {
      if(window.confirm("Are you sure you want to submit the test?")) {
          onExit(answers);
      }
    }
  };

  const hasPassage = currentQuestion?.context_passage && String(currentQuestion.context_passage).length > 50;

  return (
    <div className="flex flex-col h-screen bg-obsidian text-gray-200 font-sans">
      {/* HEADER */}
      <div className="h-16 border-b border-subtle flex items-center justify-between px-6 bg-charcoal shrink-0 z-10 shadow-md">
        <div>
            <h2 className="font-bold text-lg text-white tracking-wide">{isMAT ? "MAT" : "CAT"} MOCK</h2>
            <span className="text-xs text-gray-500 uppercase">{testData.id}</span>
        </div>
        <div className="flex items-center gap-8">
            <div className={`px-4 py-2 rounded-lg border border-gray-800 flex items-center gap-3 ${timeLeft < 300 ? 'bg-red-900/30 border-red-500' : 'bg-black/40'}`}>
                <Timer size={20} className={timeLeft < 300 ? 'text-red-400' : 'text-accent'} />
                <span className="font-mono text-2xl text-white font-bold">
                    {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                </span>
            </div>
            {/* DYNAMIC TABS (Clickable for MAT) */}
            <div className="flex gap-1 bg-black/20 p-1 rounded-lg overflow-x-auto max-w-xl">
                {SECTIONS.map((sec, idx) => (
                    <button 
                        key={sec} 
                        onClick={() => handleTabClick(idx)}
                        disabled={!isMAT && idx !== currentSectionIndex} // Lock for CAT
                        className={`px-4 py-1.5 rounded text-sm font-medium whitespace-nowrap transition-colors
                        ${idx === currentSectionIndex ? 'bg-accent text-black shadow-lg' : 'text-gray-500 hover:text-gray-300'}
                        ${!isMAT && idx !== currentSectionIndex ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                    >
                        {sec}
                    </button>
                ))}
            </div>
        </div>
      </div>

      {/* CONTENT */}
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
      <div className="h-20 border-t border-subtle bg-charcoal flex items-center justify-between px-8 shrink-0 z-20">
        <button onClick={handlePrev} disabled={currentQIndex === 0} className="text-gray-400 hover:text-white flex items-center gap-2"><ChevronLeft size={20} /> Previous</button>
        <button onClick={handleSectionSwitch} className="text-red-400 border border-red-900/50 px-4 py-2 rounded hover:bg-red-900/20">
            {currentSectionIndex === SECTIONS.length - 1 ? "Finish Exam" : "Next Section"}
        </button>
        <button onClick={handleNext} disabled={currentQIndex === questions.length - 1} className="bg-accent text-black font-bold px-8 py-3 rounded-full flex items-center gap-2">Save & Next <ChevronRight size={20} /></button>
      </div>
    </div>
  );
}