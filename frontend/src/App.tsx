import { useEffect, useRef, useState } from 'react';
import { MessageCircle, Shield, Sparkles, CheckCircle2 } from 'lucide-react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { StepIndicator } from './components/StepIndicator';
import { TrustBadge } from './components/TrustBadge';
import { useEKYC } from './hooks/useEKYC';

function App() {
  const {
    messages,
    currentStep,
    loading,
    trustBadge,
    isCompleted,
    initializeSession,
    sendMessage,
    uploadImage,
  } = useEKYC();

  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const init = async () => {
      try {
        await initializeSession();
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };

    init();
  }, [initializeSession]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const showImageUpload = currentStep === 3 || currentStep === 4;
  const imageUploadType = currentStep === 3 ? 'id_card' : 'selfie';

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">กำลังเริ่มต้นระบบ...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <header className="mb-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Shield className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    QuickChat ID
                  </h1>
                  <p className="text-gray-600 text-sm">
                    Verify Identity in Seconds, Directly on Chat
                  </p>
                </div>
              </div>

              {isCompleted && (
                <div className="flex items-center gap-2 bg-green-50 border-2 border-green-200 rounded-xl px-4 py-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-green-700">
                    Verified
                  </span>
                </div>
              )}
            </div>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold text-blue-900">AI-Driven Chat</h3>
                </div>
                <p className="text-sm text-blue-700">
                  Adaptive conversational KYC with scam detection
                </p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-purple-900">Vision Security</h3>
                </div>
                <p className="text-sm text-purple-700">
                  Thai ID OCR with face matching & deepfake detection
                </p>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <MessageCircle className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold text-green-900">5-7 Seconds</h3>
                </div>
                <p className="text-sm text-green-700">
                  Complete verification in just a few seconds
                </p>
              </div>
            </div>
          </div>
        </header>

        {!isCompleted && <StepIndicator currentStep={currentStep} />}

        {isCompleted && trustBadge ? (
          <div className="mb-6">
            <TrustBadge
              level={trustBadge.level}
              score={trustBadge.score}
              benefits={trustBadge.benefits}
              transactionLimit={trustBadge.transactionLimit}
              expires={trustBadge.expires}
            />
          </div>
        ) : null}

        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div
            className="h-[500px] overflow-y-auto p-6 space-y-4"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }}
          >
            {messages.map((msg, index) => (
              <ChatMessage
                key={index}
                role={msg.role}
                content={msg.content}
                scamScore={msg.scamScore}
                timestamp={msg.timestamp}
              />
            ))}
            {loading && (
              <div className="flex justify-start mb-4">
                <div className="bg-white rounded-2xl px-6 py-4 shadow-md border border-gray-200">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.4s' }}
                    />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <ChatInput
              onSend={sendMessage}
              onImageUpload={uploadImage}
              disabled={loading || isCompleted}
              placeholder={
                isCompleted
                  ? 'การยืนยันตัวตนเสร็จสมบูรณ์'
                  : currentStep === 3
                  ? 'กดปุ่มถ่ายรูปเพื่ออัปโหลดบัตรประชาชน...'
                  : currentStep === 4
                  ? 'กดปุ่มถ่ายรูปเพื่อถ่าย Selfie...'
                  : 'พิมพ์ข้อความ...'
              }
              showImageUpload={showImageUpload}
              imageUploadType={imageUploadType}
            />
          </div>
        </div>

        <footer className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            QuickChat ID - The Fastest, Simplest, and Safest way to build digital trust
          </p>
          <p className="text-xs text-gray-400 mt-1">
            PDPA Compliant | Secured with End-to-End Encryption
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
