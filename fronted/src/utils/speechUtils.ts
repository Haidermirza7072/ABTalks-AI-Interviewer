/**
 * Speech utility functions for natural, human-sounding TTS.
 *
 * Primary: synthesizes audio via the backend `/tts` endpoint (Microsoft Edge
 * neural voices via edge-tts) which sound genuinely human.
 * Fallback: browser Web Speech API when the backend is unreachable.
 */

let currentAudio: HTMLAudioElement | null = null;

const getTtsEndpoint = (): string => {
  const configured = (import.meta.env?.VITE_TTS_API_URL as string | undefined)?.trim();
  if (configured) return `${configured.replace(/\/+$/, '')}/tts`;
  return '/tts';
};

/** Stop any in-flight audio (backend TTS or browser voices). */
export const cancelSpeech = () => {
  if (currentAudio) {
    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      const src = currentAudio.src;
      if (src.startsWith('blob:')) URL.revokeObjectURL(src);
    } catch {
      // ignore
    }
    currentAudio = null;
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

const synthWithBackend = async (text: string, voice: string): Promise<HTMLAudioElement | null> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    const res = await fetch(getTtsEndpoint(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!res.ok) return null;
    const blob = await res.blob();
    if (!blob || blob.size === 0) return null;
    return new Audio(URL.createObjectURL(blob));
  } catch {
    return null;
  }
};

export const getNaturalVoice = (): SpeechSynthesisVoice | null => {
  if (!('speechSynthesis' in window)) return null;

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const englishVoices = voices.filter((v) => v.lang.startsWith('en'));

  // Priority 1: Natural / Neural / Online voices (Edge, Windows 11, Chrome)
  const neuralVoice = englishVoices.find(
    (v) =>
      v.name.includes('Natural') ||
      v.name.includes('Neural') ||
      v.name.includes('Online') ||
      v.name.includes('Jenny') ||
      v.name.includes('Aria') ||
      v.name.includes('Guy')
  );
  if (neuralVoice) return neuralVoice;

  // Priority 2: Google US / UK English voices (Chrome)
  const googleVoice = englishVoices.find(
    (v) => v.name.includes('Google') && (v.lang.includes('US') || v.lang.includes('GB'))
  );
  if (googleVoice) return googleVoice;

  // Priority 3: Premium / Enhanced voices (macOS / Safari / iOS)
  const premiumVoice = englishVoices.find(
    (v) =>
      v.name.includes('Enhanced') ||
      v.name.includes('Premium') ||
      v.name.includes('Samantha') ||
      v.name.includes('Alex')
  );
  if (premiumVoice) return premiumVoice;

  // Fallback: any en-US voice or first available english voice
  const usVoice = englishVoices.find((v) => v.lang === 'en-US');
  return usVoice || englishVoices[0] || voices[0];
};

const speakWithBrowserVoice = (
  text: string,
  onStart?: () => void,
  onEnd?: () => void,
  onError?: () => void
) => {
  if (!('speechSynthesis' in window)) {
    onError?.();
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);

  const voice = getNaturalVoice();
  if (voice) {
    utterance.voice = voice;
  }

  // Slightly slower rate and natural pitch produce a warmer, more human voice
  utterance.rate = 0.95;
  utterance.pitch = 1.0;

  if (onStart) utterance.onstart = onStart;
  if (onEnd) utterance.onend = onEnd;
  if (onError) utterance.onerror = onError;

  // Ensure voices are loaded if empty (some browsers load voices asynchronously)
  if (window.speechSynthesis.getVoices().length === 0) {
    window.speechSynthesis.onvoiceschanged = () => {
      const reloadedVoice = getNaturalVoice();
      if (reloadedVoice) utterance.voice = reloadedVoice;
      window.speechSynthesis.speak(utterance);
    };
  } else {
    window.speechSynthesis.speak(utterance);
  }
};

export const speakWithNaturalVoice = (
  text: string,
  onStart?: () => void,
  onEnd?: () => void,
  onError?: () => void,
  voice: string = 'en-US-GuyNeural'
): SpeechSynthesisUtterance | null => {
  if (!text.trim()) return null;

  cancelSpeech();

  // Primary path: natural neural voice from the backend
  synthWithBackend(text, voice).then((audio) => {
    if (!audio) {
      // Fallback path: browser Web Speech API
      speakWithBrowserVoice(text, onStart, onEnd, onError);
      return;
    }

    currentAudio = audio;
    onStart?.();
    audio.onended = () => {
      currentAudio = null;
      onEnd?.();
    };
    audio.onerror = () => {
      currentAudio = null;
      onError?.();
      onEnd?.();
    };
    audio.play().catch(() => {
      currentAudio = null;
      speakWithBrowserVoice(text, onStart, onEnd, onError);
    });
  });

  return null;
};
