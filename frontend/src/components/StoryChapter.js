import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';

const DEFAULT_CHAPTERS = {
  1: {
    title: "O sonho nasce",
    lines: [
      "O sonho de conhecer a China",
      "começa aqui..."
    ]
  },
  2: {
    title: "O sonho ganha forma",
    lines: [
      "Cada contribuição aproxima",
      "esta viagem da realidade."
    ]
  },
  3: {
    title: "O sonho está a caminho",
    lines: [
      "A rota desenha-se entre cidades",
      "e paisagens milenares."
    ]
  },
  4: {
    title: "O sonho quase acontece",
    lines: [
      "A viagem está cada vez mais próxima.",
      "Em breve será realidade."
    ]
  },
  5: {
    title: "O sonho torna-se realidade",
    lines: [
      "A comunidade tornou este sonho possível.",
      "Agora começa a verdadeira aventura."
    ]
  }
};

export const getChapterNumber = (percentage) => {
  if (percentage >= 100) return 5;
  if (percentage >= 75) return 4;
  if (percentage >= 50) return 3;
  if (percentage >= 25) return 2;
  return 1;
};

const StoryChapter = ({ percentage = 0, customChapters, variant = "light" }) => {
  const chapterNum = getChapterNumber(percentage);
  const chapters = customChapters || DEFAULT_CHAPTERS;
  const chapter = chapters[chapterNum] || DEFAULT_CHAPTERS[chapterNum];

  if (!chapter) return null;

  const isDark = variant === "dark";

  return (
    <motion.div
      key={chapterNum}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className={`rounded-2xl px-3 py-2 inline-block ${isDark ? 'bg-black/20' : 'bg-[#FFBE98]/8 border border-[#FFBE98]/20'}`}
      data-testid="story-chapter"
    >
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        <BookOpen className={`w-4 h-4 ${isDark ? 'text-[#FFBE98]' : 'text-[#FFBE98]'}`} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-white/60' : 'text-[#6B6661]/60'}`}>
          Capítulo {chapterNum}
        </span>
        <span className={`${isDark ? 'text-white/30' : 'text-[#6B6661]/30'}`}>—</span>
        <span className={`font-handwritten text-lg md:text-xl ${isDark ? 'text-[#FFBE98]' : 'text-[#FFBE98]'}`} data-testid="story-chapter-title">
          {chapter.title}
        </span>
      </div>
      <div className={`text-xs leading-snug ${isDark ? 'text-white/80' : 'text-[#6B6661]'}`} data-testid="story-chapter-text">
        {chapter.lines.map((line, i) => (
          <React.Fragment key={i}>{line}{i < chapter.lines.length - 1 && <br />}</React.Fragment>
        ))}
      </div>
    </motion.div>
  );
};

export default StoryChapter;
