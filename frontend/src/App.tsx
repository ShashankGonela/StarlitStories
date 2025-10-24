import { useState, useRef, useEffect } from 'react';
import { Sparkles, Send } from 'lucide-react';
import { generateStory } from './api/generateStory';
import { FlipCard } from './components/FlipCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  story?: {
    title: string;
    text: string;
    moral: string;
  };
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [threadId, setThreadId] = useState<string | null>(null); // Maintain conversation thread
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowWelcome(false);
    }, 4000);
    return () => clearTimeout(timer);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateStoryFromBackend = async (prompt: string): Promise<{
    title?: string;
    text: string;
    moral?: string;
    isConversational?: boolean;
  }> => {
    setIsGenerating(true);

    try {
      const response = await generateStory({
        user_input: prompt,
        length_tier: 'medium',
        thread_id: threadId || undefined // Send thread_id to maintain conversation
      });

      // Update thread_id from response
      if (response.thread_id) {
        setThreadId(response.thread_id);
      }

      if (response.success && response.story) {
        // Check if this is a story (has title) or conversational response (no title)
        if (response.title) {
          // It's a story with title and moral
          return {
            title: response.title,
            text: response.story,
            moral: response.moral,
            isConversational: false
          };
        } else {
          // It's a conversational response (farewell, greeting, etc.)
          return {
            text: response.story,
            isConversational: true
          };
        }
      } else {
        throw new Error(response.error || 'Failed to generate story');
      }
    } catch (error) {
      console.error('Story generation error:', error);
      throw error;
    }
  };

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

    try {
      const storyData = await generateStoryFromBackend(input.trim());

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: storyData.isConversational ? storyData.text : (storyData.title || 'Story Generated'),
        // Only include story property if it's an actual story (not conversational)
        story: storyData.isConversational ? undefined : {
          title: storyData.title || '',
          text: storyData.text || '',
          moral: storyData.moral || ''
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error generating your story. Please try again with a different request.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
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
        <div className="flex-1 w-full max-w-5xl overflow-y-auto px-4 space-y-6 pb-40">
          {/* Welcome Message */}
          {showWelcome && messages.length === 0 && (
            <div className="text-center py-12 fade-in">
              <p className="text-[#B9AFFF] text-xl md:text-2xl font-light italic">
                Good evening... what story shall I tell you tonight?
              </p>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <div key={message.id}>
              {message.role === 'user' ? (
                <div className="message-bubble user-message fade-in">
                  <div className="flex items-center gap-2 mb-2 text-[#FFD369]">
                    <Sparkles size={16} />
                    <span className="text-sm font-medium">You asked</span>
                  </div>
                  <p className="text-[#F2F2F7] leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              ) : (
                <>
                  {message.story ? (
                    <FlipCard
                      title={message.story.title}
                      story={message.story.text}
                      moral={message.story.moral}
                    />
                  ) : (
                    <div className="message-bubble assistant-message fade-in">
                      <p className="text-[#F2F2F7] leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>
                  )}
                </>
              )}
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
                <span className="text-sm">Weaving your story...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
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
