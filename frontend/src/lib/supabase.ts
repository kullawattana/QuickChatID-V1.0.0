import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface User {
  id: string;
  external_id: string;
  platform: 'line' | 'messenger' | 'web';
  email?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface VerificationSession {
  session_id: string;
  user_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'blocked';
  current_step: number;
  risk_score: number;
  trust_score: number;
  badge_level?: 'bronze' | 'silver' | 'gold' | 'platinum';
  started_at: string;
  completed_at?: string;
  metadata: Record<string, any>;
}

export interface Message {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  scam_score: number;
  scam_indicators: string[];
  created_at: string;
}

export interface TrustBadge {
  badge_id: string;
  user_id: string;
  session_id: string;
  badge_level: 'bronze' | 'silver' | 'gold' | 'platinum';
  trust_score: number;
  jwt_certificate: string;
  transaction_limit: number;
  benefits: string[];
  issued_at: string;
  expires_at: string;
  is_active: boolean;
}
