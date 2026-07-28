/**
 * Curato AI — TypeScript Types: API
 */

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  message: string | null;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
