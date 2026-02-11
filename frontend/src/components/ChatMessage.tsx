import { User, Bot, Shield, AlertTriangle } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  scamScore?: number;
  timestamp?: string;
}

export function ChatMessage({ role, content, scamScore, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';
  const isSystem = role === 'system';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fadeIn`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-blue-600'
              : isSystem
              ? 'bg-gradient-to-br from-gray-500 to-gray-600'
              : 'bg-gradient-to-br from-green-500 to-emerald-600'
          } shadow-lg`}
        >
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : isSystem ? (
            <Shield className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        <div
          className={`flex-1 px-4 py-3 rounded-2xl shadow-md ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
              : isSystem
              ? 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800 border border-gray-300'
              : 'bg-white text-gray-800 border border-gray-200'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{content}</p>

          {scamScore !== undefined && scamScore > 0 && (
            <div
              className={`mt-2 pt-2 border-t ${
                isUser ? 'border-blue-400' : 'border-gray-300'
              } flex items-center gap-2 text-xs`}
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Scam risk: {scamScore}/100</span>
            </div>
          )}

          {timestamp && (
            <p
              className={`text-xs mt-1 ${
                isUser ? 'text-blue-100' : 'text-gray-500'
              }`}
            >
              {new Date(timestamp).toLocaleTimeString('th-TH', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
