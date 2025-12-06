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

/**
 * Format a passage reference with translation in parentheses.
 * Example: "John 3:16" with "KJV" becomes "John 3:16 (KJV)"
 */
export function formatReferenceWithTranslation(
  reference: string,
  translation: string,
): string {
  // Don't add translation if already present
  if (reference.includes("(") && reference.includes(")")) {
    return reference;
  }
  return `${reference} (${translation})`;
}

/**
 * Extract reference and translation from a formatted reference.
 * Example: "John 3:16 (KJV)" returns { reference: "John 3:16", translation: "KJV" }
 */
export function parseReferenceWithTranslation(formattedReference: string): {
  reference: string;
  translation: string | null;
} {
  const match = formattedReference.match(/^(.+?)\s*\(([^)]+)\)\s*$/);
  if (match) {
    return { reference: match[1].trim(), translation: match[2].trim() };
  }
  return { reference: formattedReference, translation: null };
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

export interface Definition {
  definition: string;
  biblical_usage: string;
  original_language: string;
  cached?: boolean;
}

export interface DefinitionHistory {
  id: string;
  word: string;
  passage_reference: string;
  verse_text: string;
  definition: Definition;
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
  passage_text: string | null;
  created_at: number;
  updated_at: number;
}

export interface StandaloneChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface UsageInfo {
  is_pro: boolean;
  daily_limit: number;
  calls_today: number;
  remaining: number;
}

export interface UserSession {
  anonymous_id: string;
  created_at: number | null;
  usage?: UsageInfo;
}

export interface UsageLimitError {
  message: string;
  current_usage: number;
  limit: number;
  is_pro: boolean;
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

export interface UserDevice {
  id: number;
  device_name: string | null;
  device_type: string | null;
  user_agent: string | null;
  created_at: string;
  last_active: string;
  is_current?: boolean;
}

export interface LinkCodeResponse {
  display_code: string;
  expires_at: string;
  qr_data: string;
}

export interface LinkDeviceResponse {
  success: boolean;
  new_anonymous_id: string;
  message: string;
}

export interface UnlinkDeviceResponse {
  device_count: number;
  data_deleted: boolean;
  should_clear_cookie: boolean;
  message: string;
}
