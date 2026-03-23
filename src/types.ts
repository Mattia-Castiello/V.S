export interface WatchlistItem {
  id: string;
  type: 'category' | 'product';
  query: string;
  maxPrice: number;
  minPrice: number;
  minMargin: number;
  conditions: string[];
  size?: string;
  brandIds: number[];
  catalogIds: number[];
  sizeIds: number[];
  colorIds: number[];
  materialIds: number[];
  statusIds: number[];
  sortOrder: string;
  active: boolean;
}

export interface VintedListing {
  id: string;
  title: string;
  description: string;
  price: number;
  condition: string;
  imageUrl: string;
  url: string;
  publishedAt: string;
  brand?: string;
  model?: string;
  size?: string;
  sellerUsername?: string;
  sellerRating?: number;
  photos: { id?: number; url: string; thumbnails?: string[] }[];
  favouriteCount: number;
  viewCount: number;
  city?: string;
  country?: string;
}

export interface ConditionBreakdown {
  condition: string;
  avg: number;
  min: number;
  max: number;
  count: number;
}

export interface Opportunity extends VintedListing {
  avgPriceSameCondition: number;
  avgPriceAll: number;
  marginAbsolute: number;
  priceVsAvg: number;
  numSimilar: number;
  canonicalName?: string;
  conditionBreakdown: ConditionBreakdown[];
  score: 'high' | 'medium' | 'low';
}

export interface Purchase {
  id: string;
  listingId?: string;
  title: string;
  imageUrl: string;
  url: string;
  brand?: string;
  condition: string;
  vintedPrice: number;
  purchasePrice: number;
  resalePrice?: number;
  sold: boolean;
  notes: string;
  purchasedAt?: string;
  soldAt?: string;
}

export interface DashboardStats {
  totalMonitored: number;
  opportunitiesFound: number;
  avgMargin: number;
  potentialProfit: number;
}
