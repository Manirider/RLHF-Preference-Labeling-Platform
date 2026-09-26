import { Pair, LabelSubmission, AnalyticsData } from '../types';

const rawApiUrl = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || '';
const cleanApiUrl = rawApiUrl.replace(/\/+$/, '');
const API_BASE = cleanApiUrl ? (cleanApiUrl.endsWith('/api') ? cleanApiUrl : `${cleanApiUrl}/api`) : '/api';

export class ApiService {
  private static async handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body.detail) {
          errorMsg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
        const text = await res.text();
        if (text) errorMsg = text;
      }
      throw new Error(errorMsg);
    }
    return res.json() as Promise<T>;
  }

  static async getNextPair(annotatorId: string): Promise<Pair> {
    const res = await fetch(`${API_BASE}/pairs/next?annotator_id=${encodeURIComponent(annotatorId.trim())}`);
    return this.handleResponse<Pair>(res);
  }

  static async submitLabel(payload: LabelSubmission): Promise<{ id: number; status: string }> {
    const res = await fetch(`${API_BASE}/labels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return this.handleResponse<{ id: number; status: string }>(res);
  }

  static async getAnalytics(): Promise<AnalyticsData> {
    const res = await fetch(`${API_BASE}/analytics`);
    return this.handleResponse<AnalyticsData>(res);
  }

  static async getCategories(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/categories`);
    return this.handleResponse<string[]>(res);
  }

  static getExportUrl(params?: { category?: string; annotator_id?: string }): string {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.annotator_id) query.append('annotator_id', params.annotator_id);
    const qs = query.toString();
    return `${API_BASE}/export${qs ? `?${qs}` : ''}`;
  }

  static async checkHealth(): Promise<{ status: string; database: string }> {
    const res = await fetch(`${API_BASE}/health`);
    return this.handleResponse<{ status: string; database: string }>(res);
  }
}

export default ApiService;
