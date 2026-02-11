import { useState, useCallback } from 'react';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  scamScore?: number;
  timestamp: string;
}

interface TrustBadge {
  level: 'bronze' | 'silver' | 'gold' | 'platinum';
  score: number;
  benefits: string[];
  transactionLimit: number;
  expires: string;
}

export function useEKYC() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [trustBadge, setTrustBadge] = useState<TrustBadge | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const initializeSession = useCallback(async () => {
    try {
      console.log('🚀 Initializing session with backend...');
      
      const response = await fetch(`${API_BASE_URL}/session/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize session: ${response.status}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to initialize session');
      }

      console.log('✅ Session initialized:', data.session_id);

      setSessionId(data.session_id);
      setUserId(data.user_id);

      const welcomeMessage: Message = {
        role: 'assistant',
        content: data.message.content,
        timestamp: data.message.timestamp,
      };

      setMessages([welcomeMessage]);
      return data.session_id;
    } catch (error) {
      console.error('❌ Error initializing session:', error);

      // Fallback to demo mode
      const demoSessionId = `demo_${Date.now()}`;
      setSessionId(demoSessionId);
      setUserId(`demo_user_${Date.now()}`);

      const welcomeMessage: Message = {
        role: 'assistant',
        content:
          '🎭 **โหมดทดลอง (Demo Mode)**\n\n' +
          'ไม่สามารถเชื่อมต่อ Backend ได้\n' +
          'กำลังใช้งานในโหมดทดลอง\n\n' +
          'สวัสดีค่ะ! ยินดีต้อนรับสู่ QuickChat ID\n\n' +
          'พร้อมเริ่มต้นแล้วใช่ไหมคะ? กรุณาพิมพ์ "พร้อม"',
        timestamp: new Date().toISOString(),
      };

      setMessages([welcomeMessage]);
      return demoSessionId;
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!sessionId) return;

      const userMessage: Message = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      const isDemo = sessionId.startsWith('demo_');

      try {
        if (isDemo) {
          // Demo mode - simple responses
          await new Promise((resolve) => setTimeout(resolve, 1000));

          let response = '';
          let nextStep = currentStep;

          if (currentStep === 1) {
            response =
              'ยอดเยี่ยม! เริ่มต้นกันเลยค่ะ\n\n' +
              'ก่อนอื่นขอทราบข้อมูลพื้นฐานของคุณนะคะ:\n\n' +
              '1. ชื่อ-นามสกุล\n' +
              '2. เบอร์โทรศัพท์\n' +
              '3. อีเมล\n\n' +
              'กรุณาแชร์ข้อมูลเหล่านี้ค่ะ';
            nextStep = 2;
          } else if (currentStep === 2) {
            response =
              'ขอบคุณสำหรับข้อมูลค่ะ ✅\n\n' +
              'ถัดไปเราจะต้องตรวจสอบบัตรประชาชนของคุณ\n\n' +
              '📸 กรุณาถ่ายรูปหรืออัปโหลดรูปบัตรประชาชนของคุณค่ะ\n\n' +
              'คำแนะนำ:\n' +
              '✓ ถ่ายรูปให้ชัดเจน\n' +
              '✓ แสงสว่างเพียงพอ\n' +
              '✓ มองเห็นข้อความทั้งหมด';
            nextStep = 3;
          }

          const assistantMessage: Message = {
            role: 'assistant',
            content: response,
            timestamp: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
          setCurrentStep(nextStep);
        } else {
          // Real backend mode
          console.log('📤 Sending message to backend...');

          const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              session_id: sessionId,
              message: content,
            }),
          });

          if (!response.ok) {
            throw new Error(`Failed to send message: ${response.status}`);
          }

          const data = await response.json();

          if (!data.success) {
            throw new Error(data.error || 'Failed to send message');
          }

          console.log('✅ Received response from backend');

          const assistantMessage: Message = {
            role: 'assistant',
            content: data.response,
            scamScore: data.scam_score,
            timestamp: data.timestamp,
          };

          setMessages((prev) => [...prev, assistantMessage]);

          // Map step names to numbers
          const stepMap: Record<string, number> = {
            welcome: 1,
            personal_info: 2,
            document: 3,
            biometric: 4,
            complete: 6,
          };

          const nextStepNumber = stepMap[data.next_step] || currentStep;
          if (nextStepNumber !== currentStep) {
            setCurrentStep(nextStepNumber);
          }
        }
      } catch (error) {
        console.error('❌ Error sending message:', error);
        const errorMessage: Message = {
          role: 'system',
          content: 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, currentStep]
  );

  const uploadImage = useCallback(
    async (file: File, type: 'id_card' | 'selfie') => {
      if (!sessionId) return;

      setLoading(true);
      const isDemo = sessionId.startsWith('demo_');

      try {
        const statusMessage: Message = {
          role: 'system',
          content: `✅ ${type === 'id_card' ? 'บัตรประชาชน' : 'รูปใบหน้า'}อัปโหลดสำเร็จ\n\nกำลังประมวลผล...`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, statusMessage]);

        if (isDemo) {
          // Demo mode
          await new Promise((resolve) => setTimeout(resolve, 2000));

          if (type === 'selfie') {
            // Generate demo trust badge
            const randomScore = Math.floor(Math.random() * 20) + 80;
            const level =
              randomScore >= 96
                ? 'platinum'
                : randomScore >= 85
                ? 'gold'
                : randomScore >= 70
                ? 'silver'
                : 'bronze';

            const benefitsMap = {
              bronze: ['การยืนยันตัวตนพื้นฐาน', 'การทำธุรกรรมทั่วไป'],
              silver: ['การยืนยันเต็มรูปแบบ', 'ฟีเจอร์พิเศษ', 'Support แบบ priority'],
              gold: [
                'การยืนยันระดับสูง',
                'ฟีเจอร์พิเศษทั้งหมด',
                'Support ลำดับสำคัญ',
                'ส่วนลดค่าธรรมเนียม',
              ],
              platinum: [
                'การยืนยันระดับสูงสุด',
                'VIP Features',
                'ไม่จำกัดวงเงินธุรกรรม',
                'Support 24/7',
                'บริการเฉพาะบุคคล',
              ],
            };

            const limitMap = {
              bronze: 10000,
              silver: 50000,
              gold: 100000,
              platinum: -1,
            };

            const trustBadgeData: TrustBadge = {
              level,
              score: randomScore,
              benefits: benefitsMap[level],
              transactionLimit: limitMap[level],
              expires: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
            };

            setTrustBadge(trustBadgeData);
            setIsCompleted(true);
            setCurrentStep(6);

            const completionMessage: Message = {
              role: 'assistant',
              content: `🎉 ยืนยันตัวตนเสร็จสมบูรณ์!\n\n${level.toUpperCase()} Badge\nคะแนน: ${randomScore}/100`,
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, completionMessage]);
          } else {
            // ID card uploaded
            setCurrentStep(4);
            const nextMessage: Message = {
              role: 'assistant',
              content:
                'บัตรของคุณผ่านการตรวจสอบเรียบร้อยแล้ว! ✅\n\n' +
                '📊 ผลการตรวจสอบ:\n' +
                '✓ OCR: 95% ความแม่นยำ\n' +
                '✓ Document Authenticity: ผ่าน\n\n' +
                'ขั้นตอนสุดท้าย:\n' +
                '🤳 กรุณาถ่าย Selfie',
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, nextMessage]);
          }
        } else {
          // Real backend mode
          console.log('📤 Uploading image to backend...');

          const formData = new FormData();
          formData.append('file', file);
          formData.append('session_id', sessionId);
          formData.append('image_type', type);

          const response = await fetch(`${API_BASE_URL}/chat/image`, {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Failed to upload image: ${response.status}`);
          }

          const data = await response.json();

          if (!data.success) {
            throw new Error(data.error || 'Failed to upload image');
          }

          console.log('✅ Image processed successfully');

          const assistantMessage: Message = {
            role: 'assistant',
            content: data.response,
            timestamp: data.timestamp,
          };

          setMessages((prev) => [...prev, assistantMessage]);

          // Map step to number
          const stepMap: Record<string, number> = {
            welcome: 1,
            personal_info: 2,
            document: 3,
            biometric: 4,
            complete: 6,
          };

          const nextStepNumber = stepMap[data.next_step] || currentStep;
          setCurrentStep(nextStepNumber);

          // Handle trust badge
          if (data.trust_badge) {
            setTrustBadge(data.trust_badge);
            setIsCompleted(true);
          }
        }
      } catch (error) {
        console.error('❌ Error uploading image:', error);
        const errorMessage: Message = {
          role: 'system',
          content: 'เกิดข้อผิดพลาดในการอัปโหลดรูปภาพ กรุณาลองใหม่',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, currentStep]
  );

  return {
    messages,
    currentStep,
    loading,
    trustBadge,
    isCompleted,
    initializeSession,
    sendMessage,
    uploadImage,
  };
}
