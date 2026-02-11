import { Award, CheckCircle, Clock, TrendingUp } from 'lucide-react';

interface TrustBadgeProps {
  level: 'bronze' | 'silver' | 'gold' | 'platinum';
  score: number;
  benefits: string[];
  transactionLimit: number;
  expires: string;
}

const BADGE_CONFIG = {
  bronze: {
    gradient: 'from-orange-400 to-orange-600',
    icon: '🥉',
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
  },
  silver: {
    gradient: 'from-gray-400 to-gray-600',
    icon: '🥈',
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
  },
  gold: {
    gradient: 'from-yellow-400 to-yellow-600',
    icon: '🥇',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
  },
  platinum: {
    gradient: 'from-blue-400 via-purple-500 to-pink-500',
    icon: '💎',
    color: 'text-purple-600',
    bgColor: 'bg-gradient-to-br from-blue-50 to-purple-50',
    borderColor: 'border-purple-200',
  },
};

export function TrustBadge({ level, score, benefits, transactionLimit, expires }: TrustBadgeProps) {
  const config = BADGE_CONFIG[level];
  const expiresDate = new Date(expires);
  const daysUntilExpiry = Math.ceil(
    (expiresDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="max-w-2xl mx-auto">
      <div
        className={`bg-white rounded-3xl shadow-2xl overflow-hidden border-4 ${config.borderColor} animate-fadeIn`}
      >
        <div
          className={`bg-gradient-to-br ${config.gradient} p-8 text-white relative overflow-hidden`}
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full -mr-16 -mt-16" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-10 rounded-full -ml-12 -mb-12" />

          <div className="relative flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-5xl">{config.icon}</span>
                <div>
                  <h2 className="text-3xl font-bold capitalize">{level}</h2>
                  <p className="text-sm opacity-90">Trust Badge</p>
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="text-5xl font-bold">{score}</div>
              <p className="text-sm opacity-90">Trust Score</p>
            </div>
          </div>

          <div className="mt-6 flex items-center gap-2 bg-white bg-opacity-20 rounded-xl px-4 py-2 backdrop-blur-sm">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-medium">
              {score >= 96
                ? 'Maximum Trust Level'
                : score >= 81
                ? 'High Trust Level'
                : score >= 61
                ? 'Medium Trust Level'
                : 'Basic Trust Level'}
            </span>
          </div>
        </div>

        <div className={`${config.bgColor} p-8`}>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className={`text-lg font-bold ${config.color} mb-3 flex items-center gap-2`}>
                <Award className="w-5 h-5" />
                ประโยชน์ที่ได้รับ
              </h3>
              <ul className="space-y-2">
                {benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className={`text-lg font-bold ${config.color} mb-3`}>ข้อมูลเพิ่มเติม</h3>
              <div className="space-y-3">
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">วงเงินธุรกรรม/วัน</p>
                  <p className="text-lg font-bold text-gray-800">
                    {transactionLimit === -1
                      ? 'ไม่จำกัด'
                      : `${transactionLimit.toLocaleString()} บาท`}
                  </p>
                </div>

                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <p className="text-xs text-gray-500">อายุการใช้งาน</p>
                  </div>
                  <p className="text-sm font-medium text-gray-800">
                    อีก {daysUntilExpiry} วัน
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    หมดอายุ: {expiresDate.toLocaleDateString('th-TH')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Digital Trust Certificate - Verified by QuickChat ID
            </p>
            <p className="text-xs text-gray-400 text-center mt-1">
              This badge is cryptographically signed and verifiable
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
