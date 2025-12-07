import React from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Trophy, RefreshCcw, Download } from 'lucide-react';

export default function ResultScreen({ testData, userAnswers, onRestart }) {
  
  // --- 1. DETECT EXAM TYPE & MARKING SCHEME (FIXED) ---
  // We check if "MAT" appears anywhere in the ID (e.g., "MAT_MOCK..." or "PRAC_MAT...")
  const isMAT = testData.id && testData.id.includes("MAT");
  
  const markingScheme = isMAT 
    ? { correct: 1, wrong: 0.25 }  // MAT: +1 / -0.25
    : { correct: 3, wrong: 1 };    // CAT: +3 / -1

  // --- 2. DYNAMIC DATA FLATTENING ---
  const allQuestions = testData.sections 
    ? Object.values(testData.sections).flat() 
    : testData.questions || [];

  let totalScore = 0;
  let correctCount = 0;
  let wrongCount = 0;

  allQuestions.forEach(q => {
    const userAns = userAnswers[q.id];
    if (!userAns) return; // Unattempted

    // Normalize comparison
    if (String(userAns).trim() === String(q.correct_option).trim()) {
        totalScore += markingScheme.correct;
        correctCount++;
    } else {
        wrongCount++;
        // Negative marking logic
        if (isMAT) {
            // MAT always has negative marking
            totalScore -= markingScheme.wrong;
        } else {
            // CAT only has negative marking for MCQs (if options exist)
            if (q.options) {
                totalScore -= markingScheme.wrong;
            }
        }
    }
  });

  const accuracy = correctCount + wrongCount > 0 
    ? Math.round((correctCount / (correctCount + wrongCount)) * 100) 
    : 0;

  // --- CLEAN TEXT HELPER ---
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

        // HEADER
        doc.setFontSize(22);
        doc.setTextColor(16, 185, 129);
        doc.text(`${isMAT ? "MAT" : "CAT"} Analysis Report`, 14, 20);
        
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Exam ID: ${testData.id}`, 14, 28);
        doc.text(`Date: ${new Date().toLocaleDateString()}`, 14, 33);

        // SCORE BOX
        doc.setFillColor(240, 240, 240);
        doc.roundedRect(14, 40, 180, 25, 3, 3, 'F');
        doc.setFontSize(14);
        doc.setTextColor(0);
        doc.text(`Score: ${totalScore}`, 25, 55);
        doc.text(`Accuracy: ${accuracy}%`, 85, 55);
        doc.text(`Attempts: ${correctCount + wrongCount}/${allQuestions.length}`, 145, 55);

        // TABLE
        const summaryRows = allQuestions.map((q, index) => {
            const userAns = userAnswers[q.id] ? String(userAnswers[q.id]) : "-";
            const correctAns = q.correct_option ? String(q.correct_option) : "(TITA)";
            
            let status = "Unattempted";
            if (userAns !== "-") status = String(userAns).trim() === String(correctAns).trim() ? "Correct" : "Wrong";

            return [index + 1, q.section || "Gen", clean(q.question_text).substring(0, 50) + "...", userAns, correctAns, status];
        });

        autoTable(doc, {
            startY: 75,
            head: [['#', 'Sec', 'Question Preview', 'Your', 'Key', 'Result']],
            body: summaryRows,
            theme: 'grid',
            headStyles: { fillColor: [50, 50, 50] },
            styles: { fontSize: 8 },
            columnStyles: { 2: { cellWidth: 80 } },
            didParseCell: (data) => {
                if (data.column.index === 5) {
                    if (data.cell.raw === 'Correct') data.cell.styles.textColor = [0, 150, 0];
                    if (data.cell.raw === 'Wrong') data.cell.styles.textColor = [200, 0, 0];
                }
            }
        });

        // DETAILED SOLUTIONS (Page 2)
        doc.addPage();
        doc.setFontSize(16);
        doc.setTextColor(0);
        doc.text("Detailed Solutions", 14, 20);

        const detailRows = allQuestions.map((q, index) => {
            let content = "";
            if (q.context_passage && q.context_passage.length > 50) {
                content += `[PASSAGE]:\n${clean(q.context_passage)}\n\n`;
            }
            content += `[QUESTION]:\n${clean(q.question_text)}\n\n`;
            
            // Image handling in PDF
            if (q.images && q.images.length > 0) content += `(See Images)\n\n`;
            else if (q.image_url) content += `(See Image)\n\n`;

            if (q.options && q.options.length > 0) {
                content += `[OPTIONS]:\n`;
                q.options.forEach((opt, i) => {
                    const optText = typeof opt === 'string' ? opt : opt.text;
                    content += `(${String.fromCharCode(65+i)}) ${clean(optText)}\n`;
                });
                content += "\n";
            }

            const userAns = userAnswers[q.id] || "Unattempted";
            const correctAns = q.correct_option || "TITA";
            const isCorrect = String(userAns).trim() === String(correctAns).trim();
            
            const resultString = `YOUR ANSWER: ${userAns}   |   CORRECT ANSWER: ${correctAns}`;
            
            return [
                { content: `Q.${index+1}`, styles: { fontStyle: 'bold', halign: 'center', fillColor: [240, 240, 240] } },
                content,
                { content: resultString, styles: { textColor: isCorrect ? [0,150,0] : [200,0,0], fontStyle: 'bold' } }
            ];
        });

        autoTable(doc, {
            startY: 30,
            head: [['ID', 'Full Question & Context', 'Performance']],
            body: detailRows,
            theme: 'grid',
            headStyles: { fillColor: [16, 185, 129] },
            columnStyles: { 0: { cellWidth: 15 }, 1: { cellWidth: 120 }, 2: { cellWidth: 55 } },
            styles: { fontSize: 9, cellPadding: 4, overflow: 'linebreak' }, 
        });

        doc.save(`Analysis_${testData.id}.pdf`);
    } catch (error) {
        console.error("PDF Gen Error:", error);
        alert("PDF Generation Failed. Check console.");
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
            <p className="text-gray-500 mt-2">ID: {testData.id}</p>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
            <div className="bg-black/40 p-4 rounded-xl border border-gray-800 text-center">
                <span className="text-gray-500 text-xs font-bold uppercase">Total Score</span>
                <div className="text-3xl font-bold text-white mt-1">{totalScore}</div>
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

        <div className="flex gap-4">
            <button onClick={onRestart} className="flex-1 bg-gray-700 text-white font-bold py-4 rounded-xl hover:bg-gray-600 flex items-center justify-center gap-2">
                <RefreshCcw size={20} /> Dashboard
            </button>
            <button onClick={downloadPDF} className="flex-1 bg-accent text-black font-bold py-4 rounded-xl hover:bg-emerald-400 flex items-center justify-center gap-2">
                <Download size={20} /> Download PDF
            </button>
        </div>
      </div>
    </div>
  );
}