import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, Clock, Hash, BookOpen, Play, Filter } from 'lucide-react';

export default function PracticeConfig({ onStart, examType }) {
  // --- 1. DEFINE API URL ---
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  const SECTIONS = examType === 'MAT' 
    ? [
        { label: "Math", value: "Mathematical Skills" },
        { label: "Language", value: "Language Comprehension" },
        { label: "Data", value: "Data Analysis & Sufficiency" },
        { label: "Reasoning", value: "Intelligence & Critical Reasoning" },
        { label: "GK", value: "Indian & Global Environment" },
        { label: "ALL", value: "ALL" }
      ]
    : [
        { label: "QA", value: "QA" },
        { label: "VARC", value: "VARC" },
        { label: "DILR", value: "DILR" },
        { label: "ALL", value: "ALL" }
      ];

  const [settings, setSettings] = useState({
    section: SECTIONS[0].value,
    count: 10,
    timeLimit: 15,
    yearStart: 2017,
    yearEnd: 2024,
    topic: "ALL"
  });

  const [availableTopics, setAvailableTopics] = useState([]);

  useEffect(() => {
    setSettings(prev => ({ ...prev, section: SECTIONS[0].value, topic: "ALL" }));
  }, [examType]);

  useEffect(() => {
    const fetchTopics = async () => {
        try {
            // USE BACKTICKS HERE
            const res = await axios.get(`${API_URL}/get-topics`, {
                params: { section: settings.section, exam_type: examType }
            });
            setAvailableTopics(["ALL", ...res.data.topics]);
            setSettings(prev => ({ ...prev, topic: "ALL" })); 
        } catch (e) {
            console.error("Topic fetch failed", e);
            setAvailableTopics(["ALL"]);
        }
    };
    fetchTopics();
  }, [settings.section, examType]);

  return (
    <div className="w-full max-w-lg bg-charcoal p-8 rounded-2xl border border-subtle shadow-2xl">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white">Custom Practice ({examType})</h1>
        <p className="text-gray-400">Tailor your training session</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="flex items-center gap-2 text-sm text-gray-400 font-bold uppercase mb-2">
            <BookOpen size={16} /> Section
          </label>
          <div className="grid grid-cols-3 gap-2">
            {SECTIONS.map(sec => (
              <button
                key={sec.value}
                onClick={() => setSettings({...settings, section: sec.value})}
                className={`p-2 rounded-lg border text-xs font-bold transition-all truncate
                  ${settings.section === sec.value 
                    ? 'bg-accent text-black border-accent' 
                    : 'bg-obsidian text-gray-400 border-gray-700 hover:border-gray-500'}`}
              >
                {sec.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-gray-400 font-bold uppercase mb-2">
            <Filter size={16} /> Topic
          </label>
          <select 
            value={settings.topic}
            onChange={(e) => setSettings({...settings, topic: e.target.value})}
            className="w-full bg-obsidian border border-gray-700 text-white p-3 rounded-lg focus:border-accent outline-none appearance-none"
          >
            {availableTopics.map(t => (
                <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-2 text-sm text-gray-400 font-bold uppercase mb-2">
                <Hash size={16} /> Count
              </label>
              <input 
                type="number" min="5" max="50" step="5"
                value={settings.count}
                onChange={(e) => setSettings({...settings, count: parseInt(e.target.value)})}
                className="w-full bg-obsidian border border-gray-700 text-white p-3 rounded-lg outline-none"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm text-gray-400 font-bold uppercase mb-2">
                <Clock size={16} /> Mins
              </label>
              <input 
                type="number" min="0" max="180"
                value={settings.timeLimit}
                onChange={(e) => setSettings({...settings, timeLimit: parseInt(e.target.value)})}
                className="w-full bg-obsidian border border-gray-700 text-white p-3 rounded-lg outline-none"
              />
            </div>
        </div>

        <button 
          onClick={() => onStart(settings)}
          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 mt-4 shadow-lg shadow-emerald-900/20"
        >
          <Play size={20} /> Start Practice
        </button>
      </div>
    </div>
  );
}