import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, RotateCcw, Sparkles } from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const PlainEnglishChat: React.FC = () => {
  const { currentFile, selectedRange } = useProjectStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleClearChat = () => {
    setMessages([]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !currentFile) return;

    const userMsg = input.trim();
    setInput('');
    const newMessages: Message[] = [...messages, { role: 'user', content: userMsg }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages,
          file_id: currentFile.id,
          code_context: selectedRange?.code || currentFile.content.slice(0, 1500),
        }),
      });

      if (!response.ok || !response.body) throw new Error(`Chat error (${response.status})`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantReply = '';

      setMessages([...newMessages, { role: 'assistant', content: '' }]);

      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;
          const raw = trimmed.slice(6).trim();
          if (raw === '[DONE]') continue;
          try {
            const data = JSON.parse(raw);
            if (data.event === 'chunk' && data.content) {
              assistantReply += data.content;
              setMessages([...newMessages, { role: 'assistant', content: assistantReply }]);
            }
          } catch {}
        }
      }
    } catch (err: any) {
      setMessages([
        ...newMessages,
        { role: 'assistant', content: `Error: ${err.message || 'Could not connect to model service'}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1117] rounded-lg border border-[#30363d] overflow-hidden">
      {/* Header with Clear Button */}
      <div className="h-8 bg-[#161b22] px-3 border-b border-[#30363d] flex items-center justify-between text-[11px] text-gray-400 font-medium">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-purple-400" />
          <span>Non-Technical Q&A Assistant</span>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-gray-200 transition-colors"
              title="Reset conversation"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear</span>
            </button>
          )}
          <span className="text-[10px] text-purple-400">Conversational</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-xs text-gray-500">
            <Bot className="w-8 h-8 text-gray-600 mb-2" />
            <p>Ask any business, logic, or edge-case question about the code.</p>
            {selectedRange && (
              <p className="mt-1 text-[11px] text-purple-400">
                Focused on Lines {selectedRange.startLine}–{selectedRange.endLine}
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-1.5 justify-center">
              <button
                type="button"
                onClick={() => setInput('What happens if the database is unreachable during this operation?')}
                className="px-2 py-1 rounded bg-[#161b22] border border-[#30363d] text-[11px] text-gray-300 hover:text-white transition-colors"
              >
                What happens if DB fails?
              </button>
              <button
                type="button"
                onClick={() => setInput('Who is allowed to trigger this logic?')}
                className="px-2 py-1 rounded bg-[#161b22] border border-[#30363d] text-[11px] text-gray-300 hover:text-white transition-colors"
              >
                Who can trigger this?
              </button>
              <button
                type="button"
                onClick={() => setInput('Can you give a concrete real-world example of this in action?')}
                className="px-2 py-1 rounded bg-[#161b22] border border-[#30363d] text-[11px] text-gray-300 hover:text-white transition-colors"
              >
                Give a real-world example
              </button>
            </div>
          </div>
        ) : (
          messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex gap-2 text-xs leading-relaxed ${
                m.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {m.role === 'assistant' && (
                <div className="w-5 h-5 rounded-full bg-purple-600 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3 h-3 text-white" />
                </div>
              )}
              <div
                className={`p-2.5 rounded-lg max-w-[85%] whitespace-pre-wrap ${
                  m.role === 'user'
                    ? 'bg-purple-600 text-white rounded-tr-none'
                    : 'bg-[#161b22] border border-[#30363d] text-gray-200 rounded-tl-none'
                }`}
              >
                {m.content || (isLoading ? 'Thinking...' : '')}
              </div>
              {m.role === 'user' && (
                <div className="w-5 h-5 rounded-full bg-[#30363d] flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3 h-3 text-gray-300" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-2 border-t border-[#30363d] bg-[#161b22] flex gap-1.5">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask in plain English (e.g., 'What happens if card fails?')..."
          disabled={isLoading || !currentFile}
          className="flex-1 bg-[#0d1117] border border-[#30363d] text-gray-200 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:border-purple-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim() || !currentFile}
          className="p-1.5 rounded-md bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 transition-colors"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
};
