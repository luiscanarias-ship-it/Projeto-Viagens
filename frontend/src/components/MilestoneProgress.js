import { Flame, PartyPopper } from 'lucide-react';

export default function MilestoneProgress({ progressPercentage, contributorCount, variant = 'light' }) {
  const progress = Math.min(Math.round(progressPercentage || 0), 100);
  const count = contributorCount || 0;
  
  if (progress >= 100) {
    return (
      <div data-testid="milestone-progress-complete" className={`flex items-center justify-center gap-2 mt-2 text-sm font-semibold ${variant === 'dark' ? 'text-[#F2C94C]' : 'text-[#F2C94C]'}`}>
        <PartyPopper className="w-4 h-4" />
        <span>Sonho realizado! Obrigado a todos os que contribuíram.</span>
      </div>
    );
  }

  if (count > 0) {
    return (
      <div data-testid="milestone-progress" className={`flex items-center justify-center gap-2 mt-2 text-sm font-semibold ${variant === 'dark' ? 'text-white/80' : 'text-[#2D2A26]'}`}>
        <Flame className="w-4 h-4 text-orange-500" />
        <span>Já há {count} pessoas a acreditar neste sonho</span>
      </div>
    );
  }

  return null;
}
