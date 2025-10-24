import { useState } from 'react';
import { Sparkles, Send } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsGenerating(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Backend integration coming soon! The app is loading correctly.'
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen nebula-background overflow-hidden relative">
      {/* Starfield overlay */}
      <div className="stars"></div>
      <div className="stars2"></div>
      <div className="stars3"></div>

      {/* Main container */}
      <div className="relative z-10 min-h-screen flex flex-col items-center px-4 py-8">

        {/* Title Section */}
        <div className="text-center mt-8 mb-6">
          <h1 className="text-5xl md:text-6xl font-bold text-[#F2F2F7] mb-3 glow-text">
            🌙 Starlit Stories
          </h1>
          <p className="text-[#B9AFFF] text-lg md:text-xl font-light tracking-wide">
            Dreams begin with stories.
          </p>
        </div>

        {/* Chat Display Area */}
        <div className="flex-1 w-full max-w-3xl overflow-y-auto px-4 space-y-6 pb-32">
          {messages.length === 0 && (
            <div className="text-center py-12 fade-in">
              <p className="text-[#B9AFFF] text-xl md:text-2xl font-light italic">
                Good evening... what story shall I tell you tonight?
              </p>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-bubble ${
                message.role === 'user' ? 'user-message' : 'assistant-message'
              } fade-in`}
            >
              {message.role === 'user' && (
                <div className="flex items-center gap-2 mb-2 text-[#FFD369]">
                  <Sparkles size={16} />
                  <span className="text-sm font-medium">You asked</span>
                </div>
              )}
              <p className="text-[#F2F2F7] leading-relaxed whitespace-pre-wrap">
                {message.content}
              </p>
            </div>
          ))}

          {/* Generating indicator */}
          {isGenerating && (
            <div className="text-center py-6 fade-in">
              <div className="inline-flex items-center gap-3 text-[#B9AFFF]">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="text-sm">Testing...</span>
              </div>
            </div>
          )}
        </div>

        {/* Chat Input Area - Fixed at bottom */}
        <div className="fixed bottom-0 left-0 right-0 w-full bg-gradient-to-t from-[#0E0E2C] via-[#0E0E2C]/95 to-transparent pt-6 pb-8 px-4">
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="relative">
              <div className="input-glow rounded-full bg-[#1A103D]/60 backdrop-blur-lg border border-[#B9AFFF]/30 shadow-2xl p-2 flex items-center gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Tell me a story about..."
                  disabled={isGenerating}
                  className="flex-1 bg-transparent text-[#F2F2F7] placeholder-[#B9AFFF]/50 px-4 py-3 outline-none text-base md:text-lg"
                />
                <button
                  type="submit"
                  disabled={isGenerating || !input.trim()}
                  className="send-button bg-gradient-to-r from-[#B9AFFF] to-[#FFD369] text-[#0E0E2C] rounded-full p-3 md:p-4 hover:scale-110 transition-all duration-300 disabled:opacity-50 disabled:hover:scale-100 shadow-lg"
                >
                  <Send size={20} className="md:w-6 md:h-6" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
