import axios from 'axios';
import { BiblePassage, Insight, PassageQuery } from '../types';

const API_BASE_URL = '/api';

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
      `${API_BASE_URL}/passage?${params}`
    );
    return response.data;
  },

  async getChapter(
    book: string,
    chapter: number,
    translation: string = 'WEB'
  ): Promise<BiblePassage> {
    const params = new URLSearchParams({
      book,
      chapter: chapter.toString(),
      translation,
    });

    const response = await axios.get<BiblePassage>(
      `${API_BASE_URL}/chapter?${params}`
    );
    return response.data;
  },

  async getInsights(
    passageText: string,
    passageReference: string
  ): Promise<Insight> {
    const response = await axios.post<Insight>(`${API_BASE_URL}/insights`, {
      passage_text: passageText,
      passage_reference: passageReference,
      save: true,
    });
    return response.data;
  },

  async getInsightsHistory(limit: number = 50): Promise<any[]> {
    const response = await axios.get(`${API_BASE_URL}/insights/history?limit=${limit}`);
    return response.data;
  },

  async clearInsightsHistory(): Promise<void> {
    await axios.delete(`${API_BASE_URL}/insights/history`);
  },
};
