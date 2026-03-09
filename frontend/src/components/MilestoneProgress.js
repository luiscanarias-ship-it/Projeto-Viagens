import { Flame, PartyPopper, TrendingUp } from 'lucide-react';

const MILESTONES = [25, 50, 75, 100];

export default function MilestoneProgress({ progressPercentage, variant = 'light' }) {
  const progress = Math.min(Math.round(progressPercentage || 0), 100);
  
  const nextMilestone = MILESTONES.find(m => m > progress);
  
  if (!nextMilestone && progress >= 100) {
    return (
      <div data-testid="milestone-progress-complete" className={`flex items-center justify-center gap-2 mt-2 text-sm font-semibold ${variant === 'dark' ? 'text-[#F2C94C]' : 'text-[#F2C94C]'}`}>
        <PartyPopper className="w-4 h-4" />
        <span>Sonho realizado! Obrigado a todos os que contribuiram.</span>
      </div>
    );
  }

  if (!nextMilestone) return null;

  const remaining = nextMilestone - progress;
  const isClose = remaining <= 5;

  const milestoneLabels = {
    25: 'O Primeiro Passo',
    50: 'Meio Caminho',
    75: 'Quase La',
    100: 'Sonho Realizado',
  };

  const label = milestoneLabels[nextMilestone];

  if (isClose) {
    return (
      <div data-testid="milestone-progress-close" className={`flex items-center justify-center gap-2 mt-2 text-sm font-semibold ${variant === 'dark' ? 'text-[#F2C94C]' : 'text-[#E6A07C]'}`}>
        <Flame className="w-4 h-4 animate-bounce" style={{ animationDuration: '1.5s' }} />
        <span>Faltam apenas {remaining}% para &ldquo;{label}&rdquo;! Estamos quase!</span>
      </div>
    );
  }

  return (
    <div data-testid="milestone-progress" className={`flex items-center justify-center gap-2 mt-2 text-sm ${variant === 'dark' ? 'text-white/70' : 'text-[#6B6661]'}`}>
      <TrendingUp className="w-4 h-4" />
      <span>Faltam {remaining}% para o proximo capitulo: &ldquo;{label}&rdquo;</span>
    </div>
  );
}
