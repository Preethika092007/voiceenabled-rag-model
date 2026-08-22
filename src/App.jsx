import React, { useState, useEffect } from 'react';
import Navigation from './components/Navigation';
import QueryArea from './components/QueryArea';
import PipelineOverview from './components/PipelineOverview';
import Transcript from './components/Transcript';
import Answer from './components/Answer';
import RetrievedContext from './components/RetrievedContext';
import Performance from './components/Performance';
import { api } from './api/endpoints';

function App() {
  const [pipelineStates, setPipelineStates] = useState({
    voice: 'waiting',
    stt: 'waiting',
    validation: 'waiting',
    retrieval: 'waiting',
    reranking: 'waiting',
    generation: 'waiting',
    grounding: 'waiting',
  });
  const [systemStatus, setSystemStatus] = useState('Offline');
  const [datasetStatus, setDatasetStatus] = useState('not_prepared');
  const [transcript, setTranscript] = useState('');
  const [retrievalResults, setRetrievalResults] = useState([]);
  const [answerData, setAnswerData] = useState({ answer: null, sources: [], timings: {}, status: null, reason: null });

  const [benchmarkResults, setBenchmarkResults] = useState(null);

  // Health check polling
  useEffect(() => {
    let isMounted = true;
    
    const checkStatus = async () => {
      try {
        await api.checkHealth();
        if (isMounted) setSystemStatus('Ready');
        
        try {
          const ds = await api.getDatasetStatus();
          if (isMounted) setDatasetStatus(ds.status);
        } catch (e) {
          if (isMounted) setDatasetStatus('not_prepared');
        }
        
        try {
          const bench = await api.getBenchmarkResults();
          if (isMounted && bench.status !== 'not_found') {
            setBenchmarkResults(bench);
          }
        } catch (e) {
          // ignore
        }
      } catch (error) {
        if (isMounted) {
          setSystemStatus('Offline');
          setDatasetStatus('not_prepared');
        }
      }
    };

    checkStatus();
    // Poll every 30 seconds
    const intervalId = setInterval(checkStatus, 30000);
    
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background text-textMain flex flex-col font-sans">
      <Navigation systemStatus={systemStatus} datasetStatus={datasetStatus} />
      
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        <QueryArea 
          pipelineStates={pipelineStates}
          setPipelineStates={setPipelineStates}
          onTranscriptChange={setTranscript}
          onRetrievalResults={setRetrievalResults}
          onAnswerData={setAnswerData}
        />
        
        <div className="w-full h-px bg-borderMain/50 my-4"></div>
        
        <PipelineOverview states={pipelineStates} />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="flex flex-col">
            <Transcript text={transcript} />
            <Answer 
              answer={answerData.answer} 
              sources={answerData.sources}
              status={answerData.status}
              reason={answerData.reason}
              isLoading={pipelineStates.validation === 'processing' && !answerData.status} 
            />
          </div>
          <div className="flex flex-col">
            <RetrievedContext results={retrievalResults} isLoading={pipelineStates.validation === 'processing' && !answerData.status} />
          </div>
        </div>
        
        <Performance 
          timings={answerData.timings}
          benchmark={benchmarkResults}
        />
      </main>
    </div>
  );
}

export default App;
