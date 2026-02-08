import { useState, useRef, useCallback } from 'react';
import { transcribeApi } from '../api/client';

interface UseSpeechRecognitionOptions {
  onTranscript: (transcript: string) => void;
  onError?: (message: string) => void;
  lang?: string;
}

export function useSpeechRecognition({ onTranscript, onError }: UseSpeechRecognitionOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const hasSpeechApi =
    typeof window !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia;

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  const toggleRecording = useCallback(() => {
    if (isTranscribing) return;

    if (isRecording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      return;
    }

    chunksRef.current = [];

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        streamRef.current = stream;

        // Prefer webm/opus, fallback to browser default
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : undefined;

        const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunksRef.current.push(event.data);
          }
        };

        recorder.onstop = () => {
          setIsRecording(false);
          stopStream();

          const chunks = chunksRef.current;
          if (chunks.length === 0) {
            onError?.('No audio recorded. Please try again.');
            return;
          }

          const blob = new Blob(chunks, { type: recorder.mimeType });
          if (blob.size === 0) {
            onError?.('No audio recorded. Please try again.');
            return;
          }

          setIsTranscribing(true);

          const formData = new FormData();
          const ext = recorder.mimeType.includes('webm') ? 'webm'
            : recorder.mimeType.includes('mp4') ? 'mp4'
            : recorder.mimeType.includes('ogg') ? 'ogg'
            : 'webm';
          formData.append('file', blob, `recording.${ext}`);

          transcribeApi.transcribe(formData)
            .then(response => {
              const text = response.data.transcript;
              if (text) {
                onTranscript(text);
              } else {
                onError?.('No speech detected. Please try again.');
              }
            })
            .catch(err => {
              const status = err?.response?.status;
              if (status === 503) {
                onError?.('Voice transcription is not available right now.');
              } else if (status === 504) {
                onError?.('Transcription timed out. Please try a shorter recording.');
              } else {
                onError?.('Transcription failed. Please try again.');
              }
            })
            .finally(() => {
              setIsTranscribing(false);
            });
        };

        recorder.onerror = () => {
          setIsRecording(false);
          stopStream();
          onError?.('Recording failed. Please try again.');
        };

        recorder.start();
        setIsRecording(true);
      })
      .catch(err => {
        if (err.name === 'NotAllowedError') {
          onError?.('Microphone access denied. Please allow microphone in your browser settings.');
        } else {
          onError?.('Could not access microphone. Please check your device settings.');
        }
      });
  }, [isRecording, isTranscribing, onTranscript, onError, stopStream]);

  return { isRecording, isTranscribing, hasSpeechApi, toggleRecording };
}
