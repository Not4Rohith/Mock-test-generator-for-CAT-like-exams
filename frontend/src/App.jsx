import { useState, useEffect } from 'react'
import axios from 'axios'
import { Layers, Zap, BookOpen, GraduationCap, Lightbulb } from 'lucide-react' // Added Lightbulb icon
import TestInterface from './TestInterface'
import PracticeInterface from './PracticeInterface'
import PracticeConfig from './PracticeConfig'
import ResultScreen from './ResultScreen'

function App() {
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  const [activeData, setActiveData] = useState(() => {
    const saved = localStorage.getItem('cat_app_activeData');
    return saved ? JSON.parse(saved) : null;
  });

  const [mode, setMode] = useState(() => localStorage.getItem('cat_app_mode') || 'landing');
  const [examType, setExamType] = useState(() => localStorage.getItem('cat_app_examType') || 'CAT');
  const [userAnswers, setUserAnswers] = useState(() => {
    const saved = localStorage.getItem('cat_app_userAnswers');
    return saved ? JSON.parse(saved) : {};
  });
  
  const [practiceSettings, setPracticeSettings] = useState(() => {
    const saved = localStorage.getItem('cat_app_practiceSettings');
    return saved ? JSON.parse(saved) : null;
  });

  const [loading, setLoading] = useState(false);
  const [mockConfig, setMockConfig] = useState({ startYear: 2017, endYear: 2025 });

  useEffect(() => { localStorage.setItem('cat_app_activeData', JSON.stringify(activeData)); }, [activeData]);
  useEffect(() => { localStorage.setItem('cat_app_mode', mode); }, [mode]);
  useEffect(() => { localStorage.setItem('cat_app_examType', examType); }, [examType]);
  useEffect(() => { localStorage.setItem('cat_app_userAnswers', JSON.stringify(userAnswers)); }, [userAnswers]);
  useEffect(() => { localStorage.setItem('cat_app_practiceSettings', JSON.stringify(practiceSettings)); }, [practiceSettings]);

  const resetSession = () => {
    localStorage.removeItem('cat_app_activeData');
    localStorage.removeItem('cat_app_mode');
    localStorage.removeItem('cat_app_userAnswers');
    localStorage.removeItem('cat_app_practiceSettings');
    setActiveData(null);
    setMode('home');
    setUserAnswers({});
  };

  const startMock = async () => {
    setLoading(true);
    try {
      const isRandom = examType === 'MAT' || examType === 'CMAT';
      const res = await axios.get(`${API_URL}/generate-mock`, {
        params: { 
            exam_type: examType, 
            year_start: isRandom ? 0 : mockConfig.startYear, 
            year_end: isRandom ? 9999 : mockConfig.endYear 
        }
      });
      if (res.data && res.data.sections) {
          setActiveData(res.data);
          setMode('mock-test');
          setUserAnswers({});
      } else {
          alert("Error: Empty mock data.");
      }
    } catch (e) { alert("Start failed: " + e.message); }
    setLoading(false);
  };

  const startPractice = async (settings) => {
    setPracticeSettings(settings);
    setLoading(true);
    try {
      const isRandom = examType === 'MAT' || examType === 'CMAT';
      const res = await axios.get(`${API_URL}/generate-practice`, {
        params: { 
            exam_type: examType, 
            section: settings.section, 
            count: settings.count, 
            topic: settings.topic,
            year_start: isRandom ? 0 : settings.yearStart,
            year_end: isRandom ? 9999 : settings.yearEnd
        }
      });
      
      const fakeStructure = { id: res.data.id, sections: {} };
      res.data.questions.forEach(q => {
          if(!fakeStructure.sections[q.section]) fakeStructure.sections[q.section] = [];
          fakeStructure.sections[q.section].push(q);
      });
      
      setActiveData(fakeStructure);
      setMode('practice-test');
      setUserAnswers({});
    } catch (e) { alert("Error: " + e.message); }
    setLoading(false);
  };

  if (mode === 'landing') {
      return (
        
        <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-obsidian text-white font-sans relative">
            <h1 className="text-6xl font-bold mb-4 tracking-tighter">Exam Engine</h1>
            <p className="text-gray-400 mb-12 text-xl">Select your target exam</p>
            
            <div className="flex gap-6 flex-wrap justify-center max-w-5xl">
                <button onClick={() => { setExamType('CAT'); setMode('home'); }} className="group bg-charcoal p-8 rounded-3xl border border-subtle hover:border-blue-500 hover:scale-105 transition-all text-center w-60">
                    <div className="bg-blue-900/30 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-blue-600 transition-colors">
                        <GraduationCap className="text-blue-400 group-hover:text-white" size={32} />
                    </div>
                    <h2 className="text-2xl font-bold">CAT</h2>
                    <p className="text-gray-500 mt-2 text-sm">IIM Entrance</p>
                </button>

                <button onClick={() => { setExamType('CMAT'); setMode('home'); }} className="group bg-charcoal p-8 rounded-3xl border border-subtle hover:border-purple-500 hover:scale-105 transition-all text-center w-60">
                    <div className="bg-purple-900/30 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-purple-600 transition-colors">
                        <Lightbulb className="text-purple-400 group-hover:text-white" size={32} />
                    </div>
                    <h2 className="text-2xl font-bold">CMAT</h2>
                    <p className="text-gray-500 mt-2 text-sm">NTA Management</p>
                </button>

                <button onClick={() => { setExamType('MAT'); setMode('home'); }} className="group bg-charcoal p-8 rounded-3xl border border-subtle hover:border-emerald-500 hover:scale-105 transition-all text-center w-60">
                    <div className="bg-emerald-900/30 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:bg-emerald-600 transition-colors">
                        <BookOpen className="text-emerald-400 group-hover:text-white" size={32} />
                    </div>
                    <h2 className="text-2xl font-bold">MAT</h2>
                    <p className="text-gray-500 mt-2 text-sm">AIMA Management</p>
                </button>
            </div>

            <div className="absolute bottom-8 text-center opacity-50 hover:opacity-100 transition-opacity duration-300">
                <p className="text-sm font-medium text-gray-400">Made with <span className="text-red-600 animate-pulse">❤️</span></p>
                <p className="text-gray-600 text-xs mt-1 uppercase tracking-widest font-bold">-rohith</p>
            </div>
        </div>
      )
  }

  // --- Rendering logic for mock/practice/result remains similar ---
  if (mode === 'mock-test' && activeData) {
      return <TestInterface key={activeData.id} testData={activeData} onExit={(ans) => { setUserAnswers(ans); setMode('result'); }} />
  }

  if (mode === 'practice-test' && activeData) {
      const allQs = Object.values(activeData.sections).flat();
      return <PracticeInterface key={activeData.id} testData={{questions: allQs, id: activeData.id}} settings={practiceSettings} onExit={(ans) => { setUserAnswers(ans); setMode('result'); }} />
  }

  if (mode === 'result' && activeData) {
      return <ResultScreen testData={activeData} userAnswers={userAnswers} onRestart={resetSession} />
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-obsidian text-white relative">
      <div className="absolute top-8 left-8">
          <button onClick={() => setMode('landing')} className="text-gray-500 hover:text-white flex items-center gap-2">&larr; Switch Exam</button>
      </div>
      <div className="mb-12 text-center">
        <h1 className="text-5xl font-bold tracking-tighter text-white mb-2">{examType} Engine <span className="text-accent text-lg">Giggle</span></h1>
        <p className="text-gray-400">{examType} Preparation Dashboard</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
          <button onClick={() => setMode('mock-config')} className="group bg-charcoal p-8 rounded-3xl border border-subtle hover:border-accent transition-all text-left">
              <div className="bg-blue-900/30 w-16 h-16 rounded-2xl flex items-center justify-center mb-6"><Layers className="text-blue-400" size={32} /></div>
              <h2 className="text-2xl font-bold text-white mb-2">Full Mock Test</h2>
              <p className="text-gray-400">
                {examType === 'CAT' ? '3 Sections, 120 Minutes' : 
                 examType === 'CMAT' ? '5 Sections, 180 Minutes' : 
                 '5 Sections, 200 Questions'}
              </p>
          </button>
          <button onClick={() => setMode('practice-config')} className="group bg-charcoal p-8 rounded-3xl border border-subtle hover:border-accent transition-all text-left">
              <div className="bg-emerald-900/30 w-16 h-16 rounded-2xl flex items-center justify-center mb-6"><Zap className="text-emerald-400" size={32} /></div>
              <h2 className="text-2xl font-bold text-white mb-2">Practice Zone</h2>
              <p className="text-gray-400">Custom sessions. Filter by Section & Topic.</p>
          </button>
      </div>

      {mode === 'mock-config' && (
          <div className="w-full max-w-md bg-charcoal p-8 rounded-2xl border border-subtle mt-8">
             <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2"><Layers size={24}/> Mock Settings</h2>
             {examType === 'CAT' ? (
                 <div className="space-y-4 mb-4">
                     <label className="text-gray-400 text-sm font-bold">Year Range</label>
                     <div className="flex gap-4">
                        <input type="number" value={mockConfig.startYear} onChange={e=>setMockConfig({...mockConfig, startYear: parseInt(e.target.value)})} className="w-full bg-obsidian p-3 rounded border border-gray-700" />
                        <input type="number" value={mockConfig.endYear} onChange={e=>setMockConfig({...mockConfig, endYear: parseInt(e.target.value)})} className="w-full bg-obsidian p-3 rounded border border-gray-700" />
                     </div>
                 </div>
             ) : (
                <div className="bg-blue-900/20 p-4 rounded-lg mb-4 border border-blue-800 text-blue-200 text-sm">
                    {examType} Mock will generate a balanced paper from all available slots (100-200 Questions).
                </div>
             )}
             <button onClick={startMock} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl mt-4">
                 {loading ? "Generating..." : "Start Mock Exam"}
             </button>
             <button onClick={() => setMode('home')} className="w-full text-gray-500 py-2">Back</button>
          </div>
      )}
      {mode === 'practice-config' && (
          <div className="mt-8">
             <PracticeConfig onStart={startPractice} examType={examType} />
             <button onClick={() => setMode('home')} className="w-full text-gray-500 py-4 mt-2">Back</button>
          </div>
      )}
    </div>
  )
}
export default App