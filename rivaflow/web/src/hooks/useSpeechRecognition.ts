import { useState, useEffect, useRef, useCallback } from 'react';

interface UseSpeechRecognitionOptions {
  onTranscript: (transcript: string) => void;
  onError?: (message: string) => void;
  lang?: string;
}

export function useSpeechRecognition({ onTranscript, onError, lang = 'en-US' }: UseSpeechRecognitionOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);

  const hasSpeechApi =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = lang;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };
    recognition.onend = () => setIsRecording(false);
    recognition.onerror = (event: any) => {
      setIsRecording(false);
      const error = event.error;
      if (error === 'not-allowed') {
        onError?.('Microphone access denied. Please allow microphone in your browser settings.');
      } else if (error === 'no-speech') {
        onError?.('No speech detected. Please try again.');
      } else if (error === 'network') {
        onError?.('Network error. Speech recognition requires an internet connection.');
      } else {
        onError?.(`Speech recognition failed: ${error || 'unknown error'}`);
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
      setIsRecording(true);
    } catch (e) {
      onError?.('Could not start speech recognition. Your browser may not fully support this feature.');
    }
  }, [isRecording, lang, onTranscript, onError]);

  return { isRecording, hasSpeechApi, toggleRecording };
}
