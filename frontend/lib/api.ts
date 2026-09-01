import type {
  ProductDetail,
  ProductListResponse,
  ProductQuery,
} from "@/lib/types";

export class CatalogApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "CatalogApiError";
    this.status = status;
  }
}

function getBackendUrl(): string {
  const backendUrl = process.env.BACKEND_API_URL;
  if (!backendUrl) {
    throw new Error("BACKEND_API_URL is not configured");
  }
  return backendUrl;
}

function addQueryParam(
  params: URLSearchParams,
  key: string,
  value: string | number | undefined,
): void {
  if (value !== undefined && value !== "") {
    params.append(key, String(value));
  }
}

function productsUrl(query: ProductQuery): URL {
  const url = new URL("/api/products", getBackendUrl());
  const params = url.searchParams;

  addQueryParam(params, "q", query.q);
  query.brand?.forEach((brand) => addQueryParam(params, "brand", brand));
  addQueryParam(params, "min_price", query.min_price);
  addQueryParam(params, "max_price", query.max_price);
  addQueryParam(params, "min_ram", query.min_ram);
  addQueryParam(params, "min_storage", query.min_storage);
  addQueryParam(params, "limit", query.limit);
  addQueryParam(params, "offset", query.offset);
  addQueryParam(params, "sort", query.sort);

  return url;
}

async function responseError(response: Response): Promise<CatalogApiError> {
  const body = await response.text();
  let detail = body;

  try {
    const parsed: unknown = JSON.parse(body);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      "detail" in parsed &&
      typeof parsed.detail === "string"
    ) {
      detail = parsed.detail;
    }
  } catch {
    // Keep the raw response text for non-JSON errors.
  }

  return new CatalogApiError(
    detail || `Catalog API request failed with status ${response.status}`,
    response.status,
  );
}

export async function getProducts(
  query: ProductQuery = {},
): Promise<ProductListResponse> {
  const response = await fetch(productsUrl(query), { cache: "no-store" });
  if (!response.ok) {
    throw await responseError(response);
  }

  return (await response.json()) as ProductListResponse;
}

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  const url = new URL(
    `/api/products/${encodeURIComponent(slug)}`,
    getBackendUrl(),
  );
  const response = await fetch(url, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw await responseError(response);
  }

  return (await response.json()) as ProductDetail;
}
