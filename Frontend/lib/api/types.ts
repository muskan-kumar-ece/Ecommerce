export type JwtPair = {
  access: string;
  refresh: string;
};

export type Product = {
  id: number;
  category: number;
  category_name: string;
  name: string;
  slug: string;
  description: string;
  price: string;
  sku: string;
  stock_quantity: number;
  is_refurbished: boolean;
  condition_grade: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CartItem = {
  id: number;
  cart: number;
  product: number;
  quantity: number;
  created_at: string;
  updated_at: string;
};

export type Cart = {
  id: number;
  user: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Order = {
  id: number;
  user: string;
  total_amount: string;
  status: string;
  payment_status: string;
  tracking_id: string;
  created_at: string;
  updated_at: string;
};
