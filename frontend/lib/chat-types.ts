export interface ChatProduct {
  id: number;
  slug: string;
  name: string;
  brand: string;
  model: string;
  price_vnd: number;
  image_url: string | null;
  ram_gb: number;
  storage_gb: number;
  chipset: string;
  battery_mah: number;
  gaming_score: number;
  camera_score: number;
  battery_score: number;
  performance_score: number;
  display_score: number;
  stock_quantity: number;
  ranking_score: number | null;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  model: string;
  products: ChatProduct[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  products?: ChatProduct[];
  model?: string;
}
