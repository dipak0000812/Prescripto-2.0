import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Send,
  Mic,
  MicOff,
  Volume2,
  Square,
  AlertTriangle,
  PhoneCall,
  Sparkles,
  HelpCircle,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { Button } from './ui/Button';
import { useLanguage } from '../context/LanguageContext';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

interface AssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuestion?: string | null;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({
  isOpen,
  onClose,
  initialQuestion,
}) => {
  const { t, language, speak, stopSpeaking, isSpeaking } = useLanguage();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: t(
        'assistant.welcome',
        'Hello! I am your Prescripto helper. I can explain medicine timings, food instructions, and dosage symbols from your prescription. How can I help you today?'
      ),
      timestamp: new Date(),
    },
  ]);

  const [inputText, setInputText] = useState<string>('');
  const [isListeningVoice, setIsListeningVoice] = useState<boolean>(false);
  const [activeSpeechMsgId, setActiveSpeechMsgId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Quick suggestions
  const suggestions = [
    { label: 'What does 1-0-1 mean?', query: 'What does 1-0-1 mean?' },
    { label: 'What does "after food" mean?', query: 'What does after food mean?' },
    { label: 'What does SOS mean?', query: 'What does SOS or PRN mean?' },
    { label: 'How to take a clear photo?', query: 'How do I take a clear photo of my prescription?' },
  ];

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle initialQuestion if provided
  useEffect(() => {
    if (isOpen && initialQuestion) {
      handleUserSubmit(initialQuestion);
    }
  }, [isOpen, initialQuestion]);

  if (!isOpen) return null;

  const getAssistantAnswer = (q: string): string => {
    const lower = q.toLowerCase();
    if (lower.includes('1-0-1') || lower.includes('one zero one') || lower.includes('morning and night')) {
      return '1-0-1 means taking the medicine 2 times a day: 1 dose in the Morning, 0 in the Afternoon, and 1 at Night before sleeping.';
    }
    if (lower.includes('1-1-1') || lower.includes('three times') || lower.includes('tds') || lower.includes('tid')) {
      return '1-1-1 means taking the medicine 3 times a day: 1 dose in the Morning, 1 in the Afternoon around lunchtime, and 1 at Night with dinner.';
    }
    if (lower.includes('after food') || lower.includes('pc') || lower.includes('post cibum')) {
      return '"After food" (or pc) means taking the medicine 15 to 30 minutes after having your meal or a snack. This protects your stomach from irritation.';
    }
    if (lower.includes('before food') || lower.includes('ac') || lower.includes('empty stomach')) {
      return '"Before food" (or ac) means taking the medicine 30 to 60 minutes before eating, so the medicine can be absorbed properly into your system.';
    }
    if (lower.includes('sos') || lower.includes('prn') || lower.includes('as needed') || lower.includes('if needed')) {
      return '"SOS" or "PRN" means "only if needed". You only take this medicine when you have symptoms (like sudden pain or high fever). Do not take it on a fixed daily schedule unless your doctor advised it.';
    }
    if (lower.includes('q6h') || lower.includes('every 6 hours') || lower.includes('q8h')) {
      return 'Interval timings like q6h mean taking one dose every 6 hours (4 times across the 24-hour day). Be sure to space the doses evenly.';
    }
    if (lower.includes('photo') || lower.includes('picture') || lower.includes('camera') || lower.includes('scan')) {
      return 'To get the best scan: place the prescription slip flat on a table under good daylight. Avoid dark shadows or strong camera flash glare, and ensure all corners are visible.';
    }
    return 'I can explain prescription symbols, dosage schedules (like 1-0-1 or BD), and food instructions. For personal medical advice or changes to your prescription, please consult your prescribing doctor or local chemist.';
  };

  const handleUserSubmit = (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date(),
    };

    const replyText = getAssistantAnswer(text);
    const assistantMsg: Message = {
      id: `asst-${Date.now() + 1}`,
      sender: 'assistant',
      text: replyText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInputText('');
  };

  // Toggle voice readout
  const handleToggleSpeak = (msgId: string, text: string) => {
    if (isSpeaking && activeSpeechMsgId === msgId) {
      stopSpeaking();
      setActiveSpeechMsgId(null);
    } else {
      setActiveSpeechMsgId(msgId);
      speak(text);
    }
  };

  // Speech Recognition (Microphone)
  const handleToggleVoiceInput = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Voice dictation is not supported in this browser. Please type your question.');
      return;
    }

    if (isListeningVoice) {
      recognitionRef.current?.stop();
      setIsListeningVoice(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = language === 'hi' ? 'hi-IN' : language === 'gu' ? 'gu-IN' : language === 'mr' ? 'mr-IN' : 'en-IN';
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListeningVoice(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputText(transcript);
        handleUserSubmit(transcript);
      };
      recognition.onerror = () => setIsListeningVoice(false);
      recognition.onend = () => setIsListeningVoice(false);

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setIsListeningVoice(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="assistant-title"
      className="fixed inset-0 z-50 overflow-hidden bg-stone-900/40 backdrop-blur-xs flex justify-end animate-in fade-in"
    >
      <div
        className="relative w-full sm:max-w-md bg-white h-full max-sm:rounded-t-3xl shadow-2xl flex flex-col justify-between overflow-hidden text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="px-5 py-4 bg-paper border-b border-stone-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-brand text-white flex items-center justify-center shadow-2xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 id="assistant-title" className="text-base font-bold text-ink">
                Prescripto Assistant
              </h2>
              <p className="text-[11px] text-ink-muted">AI helper for prescription questions</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded-xl transition min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
            aria-label="Close assistant"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Emergency Helpline Strip */}
        <div className="px-5 py-2.5 bg-red-50 border-b border-red-200 text-xs text-red-900 flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2">
            <PhoneCall className="w-4 h-4 text-red-600 shrink-0" />
            <span className="font-semibold">Medical emergency?</span>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="tel:112"
              className="font-bold text-red-700 bg-white px-2 py-0.5 rounded-md border border-red-200 hover:bg-red-100 transition"
            >
              Call 112
            </a>
            <a
              href="tel:108"
              className="font-bold text-red-700 bg-white px-2 py-0.5 rounded-md border border-red-200 hover:bg-red-100 transition"
            >
              Ambulance 108
            </a>
          </div>
        </div>

        {/* Quiet AI Disclaimer */}
        <div className="px-5 py-2 bg-stone-50 border-b border-stone-200 text-[11px] text-ink-muted flex items-center gap-1.5 shrink-0">
          <ShieldCheck className="w-3.5 h-3.5 text-brand shrink-0" />
          <span>AI helper, not a doctor. Always check medicines with your doctor or chemist.</span>
        </div>

        {/* Message Thread */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {messages.map((m) => {
            const isAsst = m.sender === 'assistant';
            const isSpeakingThis = isSpeaking && activeSpeechMsgId === m.id;

            return (
              <div
                key={m.id}
                className={`flex flex-col ${isAsst ? 'items-start' : 'items-end'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    isAsst
                      ? 'bg-paper text-ink border border-stone-200 shadow-2xs'
                      : 'bg-brand text-white shadow-2xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.text}</p>
                </div>

                {/* Voice listen button for assistant messages */}
                {isAsst && (
                  <div className="mt-1 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleToggleSpeak(m.id, m.text)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand hover:underline p-1 cursor-pointer"
                    >
                      {isSpeakingThis ? (
                        <>
                          <Square className="w-3 h-3 text-red-600 animate-pulse" />
                          <span>Stop</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3 h-3 text-brand" />
                          <span>Listen</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div className="px-4 py-2 bg-stone-50 border-t border-stone-200 shrink-0">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
            {suggestions.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleUserSubmit(s.query)}
                className="whitespace-nowrap px-3 py-1.5 bg-white border border-stone-200 rounded-full text-ink hover:border-brand/40 hover:bg-brand-soft text-[11px] font-medium transition cursor-pointer shrink-0"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-stone-200 shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleUserSubmit();
            }}
            className="flex items-center gap-2"
          >
            <button
              type="button"
              onClick={handleToggleVoiceInput}
              aria-label={isListeningVoice ? 'Stop listening' : 'Start voice input'}
              className={`p-2.5 rounded-xl border transition min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer ${
                isListeningVoice
                  ? 'bg-red-500 text-white border-red-500 animate-pulse'
                  : 'bg-paper text-ink border-stone-200 hover:bg-stone-50'
              }`}
            >
              {isListeningVoice ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-brand" />}
            </button>

            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask about a medicine, schedule, or symbol…"
              className="flex-1 px-3.5 py-2.5 text-xs bg-paper border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand focus:bg-white transition min-h-[44px]"
            />

            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!inputText.trim()}
              className="min-h-[44px] px-3.5"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AssistantDrawer;

