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

export type ProductReview = {
  id: number;
  product: number;
  user_name: string;
  rating: number;
  comment: string;
  created_at: string;
  updated_at?: string;
};

export type WishlistItem = {
  id: number;
  product: number;
  product_details?: Product;
  product_name?: string;
  product_price?: string;
  image_url?: string;
  created_at?: string;
  updated_at?: string;
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
  gross_amount?: string | null;
  coupon_discount?: string;
  applied_coupon?: number | null;
  status: string;
  payment_status: string;
  tracking_id: string | null;
  items?: OrderItem[];
  created_at: string;
  updated_at: string;
};

export type OrderItem = {
  id: number;
  order: number;
  product: number;
  quantity: number;
  price: string;
  created_at: string;
  updated_at: string;
};

export type AnalyticsSummary = {
  total_revenue: string;
  total_orders: number;
  total_paid_orders: number;
  total_refunded_orders: number;
  refund_rate_percent: number;
  today_revenue: string;
  today_orders: number;
  last_7_days_revenue: string;
};

export type ReferralSummary = {
  referral_code: string;
  total_referrals: number;
  successful_referrals: number;
  pending_rewards: number;
  earned_rewards: string;
  referral_link: string;
  reward_coupon_codes: string[];
};
