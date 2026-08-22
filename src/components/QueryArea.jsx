import React, { useState, useEffect } from 'react';
import { Mic, Send, Square, Trash2, AlertCircle, Loader2, UploadCloud } from 'lucide-react';
import { useVoiceRecording } from '../hooks/useVoiceRecording';
import { api } from '../api/endpoints';

export default function QueryArea({ pipelineStates, setPipelineStates, onTranscriptChange, onRetrievalResults, onAnswerData }) {
  const [query, setQuery] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  // Propagate transcript changes
  useEffect(() => {
    if (onTranscriptChange) {
      onTranscriptChange(transcript);
    }
  }, [transcript, onTranscriptChange]);
  
  const {
    state: voiceState,
    errorMessage: voiceError,
    elapsedSeconds,
    audioURL,
    audioBlob,
    startRecording,
    stopRecording,
    discardRecording
  } = useVoiceRecording();

  // Sync state to App for Pipeline Overview
  useEffect(() => {
    if (setPipelineStates) {
      setPipelineStates(prev => {
        let vState = 'waiting';
        let sttState = prev.stt;
        
        if (voiceState === 'recording') vState = 'recording';
        else if (voiceState === 'recorded' && !isUploading && !transcript) vState = 'complete';
        else if (isUploading) {
          vState = 'complete';
          sttState = 'processing';
        }
        else if (transcript) {
          vState = 'complete';
          sttState = 'complete';
        }
        
        return { ...prev, voice: vState, stt: sttState };
      });
    }
  }, [voiceState, isUploading, transcript, setPipelineStates]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSubmitting(true);
    setStatusMessage('Running LangGraph Pipeline...');
    
    setPipelineStates(prev => ({
      ...prev,
      validation: 'processing',
      retrieval: 'waiting',
      reranking: 'waiting',
      generation: 'waiting',
      grounding: 'waiting'
    }));
    
    if (onAnswerData) {
      onAnswerData({ answer: null, sources: [], timings: {}, status: null, reason: null });
    }
    
    try {
      const response = await api.submitQuery(query);
      setStatusMessage(response.message || 'Pipeline Complete');
      
      if (onRetrievalResults && response.results) {
        onRetrievalResults(response.results);
      }
      if (onAnswerData) {
        onAnswerData({
          answer: response.answer,
          sources: response.sources || [],
          timings: response.timings || {},
          status: response.status,
          reason: response.reason
        });
      }
      
      // Update pipeline states from backend
      if (response.pipeline) {
        setPipelineStates(prev => ({
          ...prev,
          validation: response.pipeline.validation || 'complete',
          retrieval: response.pipeline.retrieval || 'skipped',
          reranking: response.pipeline.reranking || 'skipped',
          generation: response.pipeline.generation || 'skipped',
          grounding: response.pipeline.grounding || 'skipped'
        }));
      }
      
    } catch (error) {
      setStatusMessage(error.message || 'Failed to submit query.');
      setPipelineStates(prev => ({ ...prev, validation: 'error' }));
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setStatusMessage(''), 5000);
    }
  };
  
  const handleVoiceSubmit = async () => {
    if (!audioBlob) return;
    
    setIsUploading(true);
    setStatusMessage('Transcribing audio...');
    setPipelineStates(prev => ({ ...prev, stt: 'processing' }));
    
    try {
      const response = await api.submitVoiceQuery(audioBlob);
      setStatusMessage('Audio transcribed successfully');
      if (response.transcript) {
        setTranscript(response.transcript);
        setQuery(response.transcript);
      }
      setPipelineStates(prev => ({ ...prev, stt: 'complete' }));
    } catch (error) {
      setStatusMessage(error.message || 'Failed to transcribe recording.');
      setPipelineStates(prev => ({ ...prev, stt: 'error' }));
    } finally {
      setIsUploading(false);
      setTimeout(() => setStatusMessage(''), 5000);
    }
  };

  const handleClearTranscript = () => {
    setTranscript('');
    discardRecording();
    setPipelineStates(prev => ({ ...prev, stt: 'waiting', voice: 'waiting' }));
  };

  return (
    <section className="flex flex-col items-center justify-center py-12 px-4 max-w-2xl mx-auto w-full">
      <h2 className="text-3xl font-semibold text-textMain mb-3 text-center">Ask your knowledge base</h2>
      <p className="text-textMuted text-center mb-10 text-sm leading-relaxed max-w-lg">
        Ask a question using your voice or type it below. EchoRAG retrieves relevant context and generates answers grounded in the available knowledge base.
      </p>

      <div className="flex flex-col items-center justify-center min-h-[140px] w-full">
        {voiceState === 'idle' && (
          <button 
            onClick={startRecording}
            className="group relative flex flex-col items-center justify-center gap-3 transition-all"
          >
            <div className="w-20 h-20 rounded-full bg-surface border border-borderMain flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors duration-300 shadow-sm">
              <Mic size={32} />
            </div>
            <span className="text-sm font-medium text-textMuted group-hover:text-textMain transition-colors">Start speaking</span>
          </button>
        )}

        {voiceState === 'requesting' && (
          <div className="flex flex-col items-center gap-3">
            <div className="w-20 h-20 rounded-full bg-surface border border-borderMain flex items-center justify-center text-textMuted animate-pulse">
              <Mic size={32} opacity={0.5} />
            </div>
            <span className="text-sm font-medium text-textMuted">Requesting microphone access...</span>
          </div>
        )}

        {voiceState === 'recording' && (
          <div className="flex flex-col items-center gap-4">
            <button 
              onClick={stopRecording}
              className="w-20 h-20 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500 hover:bg-red-500 hover:text-white transition-all duration-300 shadow-[0_0_15px_rgba(239,68,68,0.2)]"
            >
              <Square size={24} fill="currentColor" />
            </button>
            <div className="flex flex-col items-center gap-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                <span className="text-base font-semibold text-textMain tracking-widest">{formatTime(elapsedSeconds)}</span>
              </div>
              <span className="text-xs font-medium text-textMuted">Recording... Click to stop</span>
            </div>
          </div>
        )}

        {voiceState === 'recorded' && (
          <div className="w-full max-w-md bg-surface border border-borderMain rounded-xl p-4 flex flex-col items-center gap-4">
            <span className="text-sm font-medium text-textMain">Recording ready ({formatTime(elapsedSeconds)})</span>
            <div className="flex items-center gap-4 w-full">
              <audio src={audioURL} controls className="h-10 flex-1 custom-audio" />
              <button 
                onClick={discardRecording}
                disabled={isUploading}
                className="p-2.5 rounded-lg text-textMuted hover:text-red-400 hover:bg-red-400/10 transition-colors border border-transparent hover:border-red-400/20 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Discard recording"
              >
                <Trash2 size={18} />
              </button>
            </div>
            <button
              onClick={handleVoiceSubmit}
              disabled={isUploading}
              className="w-full mt-2 flex items-center justify-center gap-2 bg-primary hover:bg-primaryHover text-white py-2 px-4 rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed text-sm"
            >
              {isUploading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <UploadCloud size={16} />
                  Process Recording
                </>
              )}
            </button>
          </div>
        )}

        {voiceState === 'error' && (
          <div className="flex flex-col items-center gap-3 max-w-sm text-center">
            <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-500 mb-1">
              <AlertCircle size={24} />
            </div>
            <p className="text-sm text-textMuted leading-relaxed">{errorMessage}</p>
            <button 
              onClick={discardRecording}
              className="mt-2 text-xs font-medium text-primary hover:text-primaryHover transition-colors"
            >
              Reset and try again
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 w-full my-8">
        <div className="flex-1 h-px bg-borderMain"></div>
        <span className="text-xs font-medium text-textMuted uppercase tracking-wider">or</span>
        <div className="flex-1 h-px bg-borderMain"></div>
      </div>

      <form onSubmit={handleTextSubmit} className="w-full relative flex flex-col gap-3">
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isSubmitting || isUploading}
            placeholder="Type your question here..."
            className="w-full bg-surface border border-borderMain rounded-lg pl-4 pr-12 py-3 text-textMain placeholder-textMuted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-sm disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isSubmitting || isUploading}
            className="absolute right-2 p-1.5 rounded-md text-textMuted hover:text-primary hover:bg-primary/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Send query"
          >
            {isSubmitting ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        {statusMessage && (
          <div className="text-sm text-amber-500/90 bg-amber-500/10 px-3 py-2 rounded border border-amber-500/20 text-center animate-in fade-in slide-in-from-top-1">
            {statusMessage}
          </div>
        )}
      </form>
    </section>
  );
}
