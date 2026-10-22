import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, User, Bot, Trash2, Copy, Check, Lock } from 'lucide-react';
import { useAIChatStore } from '@/state';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
export const AIChatPage: React.FC = () => {
  const { messages, isStreaming, currentStreamMessage, sendMessage, sendMessageStream, clearChatHistory, fetchChatHistory } = useAIChatStore();
  const [input, setInput] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isGuest } = useAuth();

  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const message = input.trim();
    setInput('');

    try {
      if (useStreaming) {
        await sendMessageStream(message);
      } else {
        await sendMessage(message);
      }
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear chat history?')) {
      try {
        await clearChatHistory();
        toast.success('Chat history cleared');
      } catch (error) {
        toast.error('Failed to clear chat history');
      }
    }
  };

  const copyToClipboard = async (text: string, messageId: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(messageId);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (isGuest) {
    return (
      <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col items-center justify-center">
        <Lock className="text-gray-400 mb-4" size={48} />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          AI Chat Locked
        </h1>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Sign up or sign in to access AI-powered chat features
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            AI Chat
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Ask questions and get AI-powered answers
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Streaming</span>
          </label>
          <button
            onClick={handleClearHistory}
            className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <Trash2 size={18} />
            Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="mx-auto text-gray-400 mb-4" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Ask me anything! I'm here to help.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="text-blue-600 dark:text-blue-400" size={20} />
                    </div>
                  )}
                  
                  <div
                    className={`max-w-[80%] rounded-xl p-4 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <>
                        <div className="prose dark:prose-invert max-w-none">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                        <button
                          onClick={() => copyToClipboard(message.content, index)}
                          className="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                        >
                          {copiedId === index ? <Check size={14} /> : <Copy size={14} />}
                          {copiedId === index ? 'Copied' : 'Copy'}
                        </button>
                      </>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>

                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="text-gray-600 dark:text-gray-300" size={20} />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Streaming message */}
            {isStreaming && currentStreamMessage && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 justify-start"
              >
                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="text-blue-600 dark:text-blue-400" size={20} />
                </div>
                <div className="max-w-[80%] rounded-xl p-4 bg-gray-100 dark:bg-gray-700">
                  <div className="prose dark:prose-invert max-w-none">
                    <ReactMarkdown>{currentStreamMessage}</ReactMarkdown>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isStreaming}
          className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isStreaming ? (
            <Loader2 className="animate-spin" size={20} />
          ) : (
            <Send size={20} />
          )}
        </button>
      </form>
    </div>
  );
};