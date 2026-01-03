import React from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Trophy, RefreshCcw, Download } from 'lucide-react';

export default function ResultScreen({ testData, userAnswers, onRestart }) {
  
  // --- 1. DETECT EXAM TYPE ---
  const isMAT = testData.id && testData.id.includes("MAT");
  const isXAT = testData.id && testData.id.includes("XAT");
  const isCMAT = testData.id && testData.id.includes("CMAT");

  // --- 2. MARKING SCHEME LOGIC ---
  const markingScheme = isCMAT
    ? { correct: 4, wrong: 1 } // CMAT: +4, -1
    : isXAT 
    ? { correct: 1, wrong: 0.25, unattemptedPenalty: 0.10, freeUnattempted: 8 }
    : isMAT 
    ? { correct: 1, wrong: 0.25 }
    : { correct: 3, wrong: 1 }; // CAT: +3, -1

  // --- 3. DYNAMIC DATA FLATTENING ---
  const allQuestions = testData.sections 
    ? Object.values(testData.sections).flat() 
    : testData.questions || [];

  let totalScore = 0;
  let correctCount = 0;
  let wrongCount = 0;
  let unattemptedCount = 0;

  allQuestions.forEach(q => {
    const userAns = userAnswers[q.id];
    
    if (!userAns) {
        unattemptedCount++;
        return; 
    }

    if (String(userAns).trim() === String(q.correct_option).trim()) {
        totalScore += markingScheme.correct;
        correctCount++;
    } else {
        wrongCount++;
        // Scoring logic for wrong answers
        if (isCMAT || isXAT || isMAT) {
            totalScore -= markingScheme.wrong;
        } else if (q.options && q.options.length > 0) { 
            // CAT: Only MCQs have negative marking
            totalScore -= markingScheme.wrong;
        }
    }
  });

  // --- XAT SPECIFIC PENALTY ---
  let penaltyApplied = 0;
  if (isXAT && unattemptedCount > markingScheme.freeUnattempted) {
      penaltyApplied = (unattemptedCount - markingScheme.freeUnattempted) * markingScheme.unattemptedPenalty;
      totalScore -= penaltyApplied;
  }

  const accuracy = correctCount + wrongCount > 0 
    ? Math.round((correctCount / (correctCount + wrongCount)) * 100) 
    : 0;

  const clean = (text) => {
      if (!text) return "";
      return String(text)
        .replace(/<[^>]*>/g, '') 
        .replace(/&nbsp;/g, ' ') 
        .replace(/[$]/g, '')     
        .replace(/\\/g, '')      
        .replace(/â€™/g, "'")    
        .replace(/\s+/g, ' ')    
        .trim();
  };

  const downloadPDF = () => {
    try {
        const doc = new jsPDF();
        const examName = isCMAT ? "CMAT" : isXAT ? "XAT" : (isMAT ? "MAT" : "CAT");

        // HEADER
        doc.setFontSize(22);
        doc.setTextColor(16, 185, 129);
        doc.text(`${examName} Analysis Report`, 14, 20);
        
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Exam ID: ${testData.id}`, 14, 28);
        doc.text(`Date: ${new Date().toLocaleDateString()}`, 14, 33);

        // SCORE BOX
        doc.setFillColor(240, 240, 240);
        doc.roundedRect(14, 40, 180, 30, 3, 3, 'F');
        doc.setFontSize(14);
        doc.setTextColor(0);
        doc.text(`Score: ${totalScore.toFixed(2)}`, 20, 55);
        doc.text(`Accuracy: ${accuracy}%`, 75, 55);
        doc.text(`Attempts: ${correctCount + wrongCount}/${allQuestions.length}`, 130, 55);
        
        // SUMMARY TABLE
        const summaryRows = allQuestions.map((q, index) => {
            const userAns = userAnswers[q.id] ? String(userAnswers[q.id]) : "-";
            const correctAns = q.correct_option ? String(q.correct_option) : "TITA";
            let status = "Unattempted";
            if (userAns !== "-") status = String(userAns).trim() === String(correctAns).trim() ? "Correct" : "Wrong";

            return [index + 1, q.section ? q.section.substring(0, 10) : "Gen", clean(q.question_text).substring(0, 50) + "...", userAns, correctAns, status];
        });

        autoTable(doc, {
            startY: 80,
            head: [['#', 'Sec', 'Question Preview', 'Your', 'Key', 'Result']],
            body: summaryRows,
            theme: 'grid',
            headStyles: { fillColor: [50, 50, 50] },
            styles: { fontSize: 8 },
        });

        doc.save(`Result_${examName}_${testData.id}.pdf`);
    } catch (error) {
        console.error("PDF Gen Error:", error);
        alert("PDF Generation Failed.");
    }
  };

  return (
    <div className="min-h-screen bg-obsidian text-gray-200 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-charcoal rounded-2xl border border-subtle p-8 shadow-2xl">
        <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-accent/20 rounded-full mb-4">
                <Trophy size={40} className="text-accent" />
            </div>
            <h1 className="text-3xl font-bold text-white">Analysis Report</h1>
            <p className="text-gray-500 mt-2">
                {isCMAT ? 'CMAT' : isXAT ? 'XAT' : isMAT ? 'MAT' : 'CAT'} Mock ID: {testData.id}
            </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-black/40 p-4 rounded-xl border border-gray-800 text-center">
                <span className="text-gray-500 text-xs font-bold uppercase">Net Score</span>
                <div className="text-3xl font-bold text-white mt-1">{totalScore.toFixed(2)}</div>
            </div>
            <div className="bg-black/40 p-4 rounded-xl border border-gray-800 text-center">
                <span className="text-gray-500 text-xs font-bold uppercase">Accuracy</span>
                <div className="text-3xl font-bold text-yellow-400 mt-1">{accuracy}%</div>
            </div>
            <div className="bg-black/40 p-4 rounded-xl border border-gray-800 text-center">
                <span className="text-gray-500 text-xs font-bold uppercase">Correct</span>
                <div className="text-3xl font-bold text-emerald-400 mt-1">{correctCount}</div>
            </div>
            <div className="bg-black/40 p-4 rounded-xl border border-gray-800 text-center">
                <span className="text-gray-500 text-xs font-bold uppercase">Wrong</span>
                <div className="text-3xl font-bold text-red-400 mt-1">{wrongCount}</div>
            </div>
        </div>

        {/* XAT Warning */}
        {isXAT && unattemptedCount > 8 && (
            <div className="bg-red-900/20 border border-red-900/50 p-3 rounded-lg mb-8 text-center text-red-400 text-sm">
                ⚠️ Penalty of <b>-{penaltyApplied.toFixed(2)}</b> applied for <b>{unattemptedCount}</b> unattempted questions.
            </div>
        )}

        <div className="flex flex-col md:flex-row gap-4">
            <button onClick={onRestart} className="flex-1 bg-gray-700 text-white font-bold py-4 rounded-xl hover:bg-gray-600 flex items-center justify-center gap-2 transition-colors">
                <RefreshCcw size={20} /> Dashboard
            </button>
            <button onClick={downloadPDF} className="flex-1 bg-accent text-black font-bold py-4 rounded-xl hover:bg-emerald-400 flex items-center justify-center gap-2 transition-colors">
                <Download size={20} /> Download PDF
            </button>
        </div>
      </div>
    </div>
  );
}