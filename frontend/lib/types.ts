export interface User {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Client {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Asset {
  id: number;
  ticker: string;
  name: string;
  exchange: string;
  currency: string;
}

export interface Allocation {
  id: number;
  client_id: number;
  asset_id: number;
  quantity: string;
  buy_price: string;
  buy_date: string;
}

export interface Movement {
  id: number;
  client_id: number;
  type: "deposit" | "withdrawal";
  amount: string;
  date: string;
  note?: string | null;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}
