export interface BibleVerse {
  book: string;
  chapter: number;
  verse: number;
  text: string;
  translation: string;
}

export interface BiblePassage {
  reference: string;
  verses: BibleVerse[];
  translation: string;
}

export interface Insight {
  historical_context: string;
  theological_significance: string;
  practical_application: string;
  cached?: boolean;
}

export interface InsightHistory {
  id: string;
  reference: string;
  text: string;
  insight: Insight;
  timestamp: number;
}

export interface PassageQuery {
  book: string;
  chapter: number;
  verse_start: number;
  verse_end?: number;
  translation?: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface StandaloneChat {
  id: number;
  title: string | null;
  passage_reference: string | null;
  created_at: number;
  updated_at: number;
}

export interface StandaloneChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface UserSession {
  anonymous_id: string;
  created_at: number | null;
}

export interface UserDataExport {
  user: {
    anonymous_id: string;
    created_at: string | null;
  };
  insights: Array<{
    id: number;
    passage_reference: string;
    passage_text: string;
    historical_context: string;
    theological_significance: string;
    practical_application: string;
    created_at: string | null;
  }>;
  chat_messages: Array<{
    insight_id: number;
    role: string;
    content: string;
    created_at: string | null;
  }>;
  standalone_chats: Array<{
    title: string | null;
    passage_reference: string | null;
    passage_text: string | null;
    created_at: string | null;
    updated_at: string | null;
    messages: Array<{
      role: string;
      content: string;
      created_at: string | null;
    }>;
  }>;
}

export interface DataOperationResult {
  message: string;
  deleted?: {
    insights: number;
    chat_messages: number;
    standalone_chats: number;
  };
  imported?: {
    insights: number;
    chat_messages: number;
    standalone_chats: number;
  };
}
