import axios from "axios";
import { BiblePassage, Insight, PassageQuery, InsightHistory, Definition, DefinitionHistory, ChatMessage, StandaloneChat, StandaloneChatMessage, UserSession, UserDataExport, DataOperationResult } from "../types";

const API_BASE_URL = "/api";

// Configure axios to send credentials (cookies) with every request
axios.defaults.withCredentials = true;

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
  ): Promise<string> {
    const response = await axios.post<{ response: string }>(
      `${API_BASE_URL}/chat/message`,
      {
        insight_id: insightId,
        message,
        passage_text: passageText,
        passage_reference: passageReference,
        insight_context: {
          historical_context: insightContext.historical_context,
          theological_significance: insightContext.theological_significance,
          practical_application: insightContext.practical_application,
        },
      },
    );
    return response.data.response;
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
    passageText?: string,
    passageReference?: string,
  ): Promise<{ chat_id: number; messages: StandaloneChatMessage[] }> {
    const response = await axios.post<{ chat_id: number; messages: StandaloneChatMessage[] }>(
      `${API_BASE_URL}/standalone-chat`,
      {
        message,
        passage_text: passageText,
        passage_reference: passageReference,
      },
    );
    return response.data;
  },

  async sendStandaloneChatMessage(
    chatId: number,
    message: string,
  ): Promise<string> {
    const response = await axios.post<{ response: string }>(
      `${API_BASE_URL}/standalone-chat/message`,
      {
        chat_id: chatId,
        message,
      },
    );
    return response.data.response;
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
