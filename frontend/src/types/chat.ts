// src/types/chat.ts
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface WebSocketMessage {
  message: string;
  article_id: string;
  brand_identity: string;
  platform: string;
}