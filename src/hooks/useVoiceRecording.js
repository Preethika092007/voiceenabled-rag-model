import { useState, useRef, useCallback } from 'react';

export function useVoiceRecording() {
  const [state, setState] = useState('idle'); // 'idle', 'requesting', 'recording', 'recorded', 'error'
  const [errorMessage, setErrorMessage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioURL, setAudioURL] = useState(null);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  const startRecording = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setState('error');
      setErrorMessage('Voice recording is not supported in this browser. Please use text input.');
      return;
    }

    try {
      setState('requesting');
      setErrorMessage('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        clearInterval(timerRef.current);

        if (chunksRef.current.length === 0 || blob.size === 0) {
           setState('error');
           setErrorMessage('Recording was empty. Please try again.');
           setElapsedSeconds(0);
           return;
        }

        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioURL(url);
        setState('recorded');
      };

      mediaRecorder.start(200); // chunk every 200ms
      setState('recording');
      setElapsedSeconds(0);
      
      timerRef.current = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);

    } catch (err) {
      setState('error');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Microphone access was denied. Please allow microphone access or use text input.');
      } else {
        setErrorMessage('An error occurred while trying to access the microphone.');
      }
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const discardRecording = useCallback(() => {
    if (audioURL) {
      URL.revokeObjectURL(audioURL);
    }
    setAudioBlob(null);
    setAudioURL(null);
    setState('idle');
    setElapsedSeconds(0);
    setErrorMessage('');
  }, [audioURL]);

  return {
    state,
    errorMessage,
    elapsedSeconds,
    audioBlob,
    audioURL,
    startRecording,
    stopRecording,
    discardRecording
  };
}
