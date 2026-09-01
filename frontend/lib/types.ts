export type ProductSort = "newest" | "price_asc" | "price_desc" | "name_asc";

export interface ProductListItem {
  id: number;
  slug: string;
  name: string;
  brand: string;
  model: string;
  price_vnd: number;
  image_url: string | null;
  release_year: number | null;
  ram_gb: number;
  storage_gb: number;
  stock_quantity: number;
}

export interface ProductListResponse {
  items: ProductListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductSpec {
  chipset: string;
  ram_gb: number;
  storage_gb: number;
  screen_size_inches: number;
  screen_type: string;
  refresh_rate_hz: number;
  battery_mah: number;
  charging_watt: number;
  rear_camera: string;
  front_camera: string;
  os: string;
  gaming_score: number;
  camera_score: number;
  battery_score: number;
  performance_score: number;
  display_score: number;
}

export interface Inventory {
  quantity: number;
}

export interface ProductDetail {
  id: number;
  slug: string;
  name: string;
  brand: string;
  model: string;
  price_vnd: number;
  description: string | null;
  image_url: string | null;
  release_year: number | null;
  is_active: boolean;
  spec: ProductSpec;
  inventory: Inventory;
}

export interface ProductQuery {
  q?: string;
  brand?: string[];
  min_price?: number;
  max_price?: number;
  min_ram?: number;
  min_storage?: number;
  limit?: number;
  offset?: number;
  sort?: ProductSort;
}
