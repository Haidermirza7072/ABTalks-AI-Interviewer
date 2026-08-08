const FILLER_PATTERNS: Array<[RegExp, string]> = [
  [/\bum\b/gi, 'um'],
  [/\buh\b/gi, 'uh'],
  [/\buhh\b/gi, 'uh'],
  [/\buhm\b/gi, 'um'],
  [/\ber\b/gi, 'er'],
  [/\bhmm\b/gi, 'hmm'],
  [/\byou know\b/gi, 'you know'],
  [/\bi mean\b/gi, 'I mean'],
  [/\blike\b/gi, 'like'],
  [/\bkind of\b/gi, 'kind of'],
  [/\bsort of\b/gi, 'sort of'],
  [/\bbasically\b/gi, 'basically'],
  [/\bactually\b/gi, 'actually'],
  [/\bliterally\b/gi, 'literally'],
];

export interface FillerAnalysis {
  count: number;
  words: string[];
}

export function analyzeFillers(text: string): FillerAnalysis {
  if (!text || text.trim().length === 0) {
    return { count: 0, words: [] };
  }

  const words = new Set<string>();
  let count = 0;
  let remaining = text.replace(/[^\w\s]/g, ' ');

  for (const [pattern, label] of FILLER_PATTERNS) {
    const matches = remaining.match(pattern);
    if (matches) {
      count += matches.length;
      words.add(label);
      remaining = remaining.replace(pattern, ' ');
    }
  }

  return { count, words: Array.from(words) };
}

export function fillerTip(fillers: number): string | null {
  if (fillers <= 0) return null;
  if (fillers === 1) return 'You used 1 filler word — try a short pause instead.';
  if (fillers <= 3) return `You used ${fillers} filler words — try pausing briefly instead.`;
  return `You used ${fillers} filler words — that can make you sound less confident. Practice pausing instead of saying them.`;
}
