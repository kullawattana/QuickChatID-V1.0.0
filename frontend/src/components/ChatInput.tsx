import { useState } from 'react';
import { Send, Image as ImageIcon, Camera } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onImageUpload?: (file: File, type: 'id_card' | 'selfie') => void;
  disabled?: boolean;
  placeholder?: string;
  showImageUpload?: boolean;
  imageUploadType?: 'id_card' | 'selfie';
}

export function ChatInput({
  onSend,
  onImageUpload,
  disabled = false,
  placeholder = 'พิมพ์ข้อความ...',
  showImageUpload = false,
  imageUploadType = 'id_card',
}: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage('');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onImageUpload) {
      onImageUpload(file, imageUploadType);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      {showImageUpload && onImageUpload && (
        <div className="relative">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="image-upload"
            disabled={disabled}
          />
          <label
            htmlFor="image-upload"
            className={`flex items-center justify-center w-12 h-12 rounded-xl ${
              disabled
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-gradient-to-br from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 cursor-pointer'
            } text-white transition-all duration-200 shadow-md hover:shadow-lg`}
          >
            {imageUploadType === 'selfie' ? (
              <Camera className="w-5 h-5" />
            ) : (
              <ImageIcon className="w-5 h-5" />
            )}
          </label>
        </div>
      )}

      <div className="flex-1 flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-800"
        />

        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white flex items-center justify-center transition-all duration-200 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </form>
  );
}
