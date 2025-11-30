import axios from "axios";
import { BiblePassage, Insight, PassageQuery, InsightHistory, Definition, DefinitionHistory, ChatMessage, StandaloneChat, StandaloneChatMessage, UserSession, UserDataExport, DataOperationResult } from "../types";

const API_BASE_URL = "/api";

// Configure axios to send credentials (cookies) with every request
axios.defaults.withCredentials = true;

// Helper function to handle SSE streaming
interface SSEEventHandlers {
  onToken?: (token: string) => void;
  onChatId?: (chatId: number) => void;
  onDone?: (stopReason?: string) => void;
  onError?: (error: Error) => void;
}

async function handleSSEStream(
  response: Response,
  handlers: SSEEventHandlers
): Promise<void> {
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('ReadableStream not supported');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let stopReason: string | undefined;

  try {
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.token && handlers.onToken) {
              handlers.onToken(data.token);
            } else if (data.chat_id && handlers.onChatId) {
              handlers.onChatId(data.chat_id);
            } else if (data.stop_reason !== undefined) {
              stopReason = data.stop_reason;
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
        if (line.startsWith('event: done')) {
          if (handlers.onDone) {
            handlers.onDone(stopReason);
          }
          return;
        }
        if (line.startsWith('event: error')) {
          const errorLine = lines.find(l => l.startsWith('data: '));
          if (errorLine) {
            try {
              const errorData = JSON.parse(errorLine.slice(6));
              const error = new Error(errorData.error || 'Unknown error');
              if (handlers.onError) {
                handlers.onError(error);
              }
              throw error;
            } catch (e) {
              const error = e instanceof Error ? e : new Error('Unknown error');
              if (handlers.onError) {
                handlers.onError(error);
              }
              throw error;
            }
          } else {
            const error = new Error('Unknown error');
            if (handlers.onError) {
              handlers.onError(error);
            }
            throw error;
          }
        }
      }
    }
  } catch (error) {
    if (handlers.onError && error instanceof Error) {
      handlers.onError(error);
    }
    throw error;
  }
}

export const bibleService = {
  async getPassage(query: PassageQuery): Promise<BiblePassage> {
    const params = new URLSearchParams({
      book: query.book,
      chapter: query.chapter.toString(),
      verse_start: query.verse_start.toString(),
      ...(query.verse_end && { verse_end: query.verse_end.toString() }),
      ...(query.translation && { translation: query.translation }),
    });

    const response = await axios.get<BiblePassage>(
      `${API_BASE_URL}/passage?${params}`,
    );
    return response.data;
  },

  async getChapter(
    book: string,
    chapter: number,
    translation: string = "WEB",
  ): Promise<BiblePassage> {
    const params = new URLSearchParams({
      book,
      chapter: chapter.toString(),
      translation,
    });

    const response = await axios.get<BiblePassage>(
      `${API_BASE_URL}/chapter?${params}`,
    );
    return response.data;
  },

  async getInsights(
    passageText: string,
    passageReference: string,
  ): Promise<Insight> {
    const response = await axios.post<Insight>(`${API_BASE_URL}/insights`, {
      passage_text: passageText,
      passage_reference: passageReference,
      save: true,
    });
    return response.data;
  },

  async getInsightsHistory(limit: number = 50): Promise<InsightHistory[]> {
    const response = await axios.get<InsightHistory[]>(
      `${API_BASE_URL}/insights/history?limit=${limit}`,
    );
    return response.data;
  },

  async clearInsightsHistory(): Promise<void> {
    await axios.delete(`${API_BASE_URL}/insights/history`);
  },

  async getDefinition(
    word: string,
    verseText: string,
    passageReference: string,
  ): Promise<Definition> {
    const response = await axios.post<Definition>(`${API_BASE_URL}/definitions`, {
      word: word,
      verse_text: verseText,
      passage_reference: passageReference,
      save: true,
    });
    return response.data;
  },

  async getDefinitionsHistory(limit: number = 50): Promise<DefinitionHistory[]> {
    const response = await axios.get<DefinitionHistory[]>(
      `${API_BASE_URL}/definitions/history?limit=${limit}`,
    );
    return response.data;
  },

  async clearDefinitionsHistory(): Promise<void> {
    await axios.delete(`${API_BASE_URL}/definitions/history`);
  },

  async sendChatMessage(
    insightId: number,
    message: string,
    passageText: string,
    passageReference: string,
    insightContext: Insight,
    onToken: (token: string) => void,
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        insight_id: insightId,
        message,
        passage_text: passageText,
        passage_reference: passageReference,
        insight_context: {
          historical_context: insightContext.historical_context,
          theological_significance: insightContext.theological_significance,
          practical_application: insightContext.practical_application,
        },
      }),
    });

    await handleSSEStream(response, { onToken });
  },

  async getChatMessages(insightId: number): Promise<ChatMessage[]> {
    const response = await axios.get<ChatMessage[]>(
      `${API_BASE_URL}/chat/messages/${insightId}`,
    );
    return response.data;
  },

  async clearChatMessages(insightId: number): Promise<void> {
    await axios.delete(`${API_BASE_URL}/chat/messages/${insightId}`);
  },

  async createStandaloneChat(
    message: string,
    onToken: (token: string) => void,
    passageText?: string,
    passageReference?: string,
  ): Promise<number> {
    let chatId: number | null = null;

    const response = await fetch(`${API_BASE_URL}/standalone-chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        message,
        passage_text: passageText,
        passage_reference: passageReference,
      }),
    });

    await handleSSEStream(response, {
      onToken,
      onChatId: (id) => {
        chatId = id;
      },
      onDone: () => {
        if (chatId === null) {
          throw new Error('No chat ID received');
        }
      }
    });

    if (chatId === null) {
      throw new Error('No chat ID received');
    }

    return chatId;
  },

  async sendStandaloneChatMessage(
    chatId: number,
    message: string,
    onToken: (token: string) => void,
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/standalone-chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        chat_id: chatId,
        message,
      }),
    });

    await handleSSEStream(response, { onToken });
  },

  async getStandaloneChats(limit: number = 50): Promise<StandaloneChat[]> {
    const response = await axios.get<StandaloneChat[]>(
      `${API_BASE_URL}/standalone-chat?limit=${limit}`,
    );
    return response.data;
  },

  async getStandaloneChatMessages(chatId: number): Promise<StandaloneChatMessage[]> {
    const response = await axios.get<StandaloneChatMessage[]>(
      `${API_BASE_URL}/standalone-chat/${chatId}/messages`,
    );
    return response.data;
  },

  async deleteStandaloneChat(chatId: number): Promise<void> {
    await axios.delete(`${API_BASE_URL}/standalone-chat/${chatId}`);
  },

  async getUserSession(): Promise<UserSession> {
    const response = await axios.get<UserSession>(`${API_BASE_URL}/user/session`);
    return response.data;
  },

  async clearUserData(): Promise<DataOperationResult> {
    const response = await axios.delete<DataOperationResult>(`${API_BASE_URL}/user/data`);
    return response.data;
  },

  async exportUserData(): Promise<UserDataExport> {
    const response = await axios.get<UserDataExport>(`${API_BASE_URL}/user/export`);
    return response.data;
  },

  async importUserData(data: UserDataExport): Promise<DataOperationResult> {
    const response = await axios.post<DataOperationResult>(`${API_BASE_URL}/user/import`, { data });
    return response.data;
  },
};
