import { Check, MessageCircle, FileText, Camera, ShieldCheck, BarChart3, Award } from 'lucide-react';

const STEPS = [
  { id: 1, name: 'เริ่มต้น', icon: MessageCircle, description: 'ยินดีต้อนรับ' },
  { id: 2, name: 'ข้อมูลพื้นฐาน', icon: FileText, description: 'รวบรวมข้อมูล' },
  { id: 3, name: 'ถ่ายบัตร', icon: Camera, description: 'บัตรประชาชน' },
  { id: 4, name: 'ยืนยันตัวตน', icon: ShieldCheck, description: 'Selfie' },
  { id: 5, name: 'วิเคราะห์', icon: BarChart3, description: 'ประเมินความเสี่ยง' },
  { id: 6, name: 'เสร็จสิ้น', icon: Award, description: 'รับ Trust Badge' },
];

interface StepIndicatorProps {
  currentStep: number;
}

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
      <div className="flex justify-between items-center relative">
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 -z-10">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-500"
            style={{ width: `${((currentStep - 1) / (STEPS.length - 1)) * 100}%` }}
          />
        </div>

        {STEPS.map((step) => {
          const Icon = step.icon;
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          const isPending = currentStep < step.id;

          return (
            <div key={step.id} className="flex flex-col items-center relative">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isCompleted
                    ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg scale-110'
                    : isCurrent
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg scale-110 animate-pulse'
                    : 'bg-gray-200'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5 text-white" />
                ) : (
                  <Icon
                    className={`w-5 h-5 ${
                      isCurrent ? 'text-white' : 'text-gray-400'
                    }`}
                  />
                )}
              </div>

              <div className="mt-2 text-center">
                <p
                  className={`text-xs font-medium ${
                    isCurrent ? 'text-blue-600' : isPending ? 'text-gray-400' : 'text-green-600'
                  }`}
                >
                  {step.name}
                </p>
                <p className="text-[10px] text-gray-500 mt-0.5">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
