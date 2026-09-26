export type ChoiceType = 'A' | 'B' | 'tie' | 'skip';

export interface Pair {
  id: number;
  prompt: string;
  response_a: string;
  response_b: string;
  category: string;
}

export interface LabelSubmission {
  pair_id: number;
  annotator_id: string;
  chosen: ChoiceType;
}

export interface LabelDistribution {
  A: number;
  B: number;
  tie: number;
  skip: number;
  [key: string]: number;
}

export interface AnalyticsData {
  total_labels: number;
  label_distribution: LabelDistribution;
  agreement_rate: number;
  total_pairs?: number;
  labeled_pairs?: number;
  active_annotators?: number;
  category_breakdown?: Record<string, number>;
}

export interface ApiError {
  detail: string | { status: string; database: string };
}
