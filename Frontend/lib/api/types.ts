export type ApiListResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type JwtPair = {
  access: string;
  refresh: string;
};

export type User = {
  id: string;
  name: string;
  email: string;
  role: "admin" | "student";
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string;
  sku: string;
  is_active: boolean;
};

export type CartItem = {
  id: number;
  quantity: number;
  product: Product;
};

export type Cart = {
  id: number;
  items: CartItem[];
};
