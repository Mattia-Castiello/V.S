import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import {
  Clock,
  ExternalLink,
  Tag,
  Heart,
  Eye,
  MapPin,
  Star,
  ChevronLeft,
  ChevronRight,
  Search,
  Users
} from 'lucide-react';
import { WatchlistItem, Opportunity, DashboardStats, ConditionBreakdown } from '../types';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const StatCard = ({ label, value, subValue }: { label: string; value: string | number; subValue?: string }) => (
  <div className="glass-card p-6 flex flex-col gap-1">
    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
    <div className="flex items-baseline gap-2">
      <h3 className="text-2xl font-bold">{value}</h3>
      {subValue && <span className="text-xs text-gray-400">{subValue}</span>}
    </div>
  </div>
);

function PhotoCarousel({ photos, fallbackUrl }: { photos: { url: string }[]; fallbackUrl: string }) {
  const [idx, setIdx] = React.useState(0);
  const urls = photos.length > 0 ? photos.map(p => p.url) : [fallbackUrl];

  if (urls.length <= 1) {
    return <img src={urls[0] || ''} className="w-12 h-12 rounded-lg object-cover" alt="" />;
  }

  return (
    <div className="relative w-12 h-12 group/photo">
      <img src={urls[idx] || ''} className="w-12 h-12 rounded-lg object-cover" alt="" />
      <div className="absolute inset-0 flex items-center justify-between opacity-0 group-hover/photo:opacity-100 transition-opacity">
        <button
          onClick={e => { e.stopPropagation(); setIdx(i => (i - 1 + urls.length) % urls.length); }}
          className="w-4 h-4 bg-black/50 text-white rounded-full flex items-center justify-center"
        >
          <ChevronLeft size={10} />
        </button>
        <button
          onClick={e => { e.stopPropagation(); setIdx(i => (i + 1) % urls.length); }}
          className="w-4 h-4 bg-black/50 text-white rounded-full flex items-center justify-center"
        >
          <ChevronRight size={10} />
        </button>
      </div>
      <span className="absolute bottom-0 right-0 bg-black/60 text-white text-[8px] px-1 rounded-tl rounded-br-lg">
        {idx + 1}/{urls.length}
      </span>
    </div>
  );
}

function ConditionPills({ breakdown }: { breakdown: ConditionBreakdown[] }) {
  if (!breakdown || breakdown.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1">
      {breakdown.map((b) => (
        <span
          key={b.condition}
          className="text-[9px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded"
          title={`${b.condition}: avg ${b.avg.toFixed(0)}€ (${b.min.toFixed(0)}-${b.max.toFixed(0)}€, ${b.count} items)`}
        >
          {b.condition.replace('Nuovo con cartellino', 'NCC').replace('Nuovo senza cartellino', 'NSC')}: {b.avg.toFixed(0)}€
        </span>
      ))}
    </div>
  );
}

function PriceVsAvgBadge({ value }: { value: number }) {
  const isGood = value < 0;
  return (
    <span className={cn(
      "px-2 py-0.5 rounded-full text-xs font-bold",
      isGood ? "bg-green-100 text-green-700" : value > 0 ? "bg-red-100 text-red-600" : "bg-gray-100 text-gray-500"
    )}>
      {value > 0 ? '+' : ''}{value.toFixed(1)}%
    </span>
  );
}

// Build chart data: savings vs average by score
function buildChartData(opportunities: Opportunity[]) {
  const high = opportunities.filter(o => o.score === 'high');
  const medium = opportunities.filter(o => o.score === 'medium');
  const low = opportunities.filter(o => o.score === 'low');
  return [
    { name: 'High', value: high.reduce((s, o) => s + Math.max(o.marginAbsolute, 0), 0), count: high.length, highlight: true },
    { name: 'Medium', value: medium.reduce((s, o) => s + Math.max(o.marginAbsolute, 0), 0), count: medium.length, highlight: false },
    { name: 'Low', value: low.reduce((s, o) => s + Math.max(o.marginAbsolute, 0), 0), count: low.length, highlight: false },
  ];
}

export default function Dashboard() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [opportunities, setOpportunities] = React.useState<Opportunity[]>([]);
  const [watchlist, setWatchlist] = React.useState<WatchlistItem[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);

  const appendError = React.useCallback((msg: string) => {
    setError(prev => (prev ? `${prev} | ${msg}` : msg));
  }, []);

  const fetchStats = React.useCallback(async () => {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) throw new Error(`stats: HTTP ${res.status}`);
      const data = await res.json();
      setStats(data);
    } catch (err: any) {
      appendError(err?.message || 'Failed to load stats');
    }
  }, [appendError]);

  const fetchOpportunities = React.useCallback(async () => {
    try {
      const res = await fetch('/api/opportunities');
      if (!res.ok) throw new Error(`opportunities: HTTP ${res.status}`);
      const data = await res.json();
      setOpportunities(data);
    } catch (err: any) {
      appendError(err?.message || 'Failed to load opportunities');
    }
  }, [appendError]);

  const fetchWatchlist = React.useCallback(async () => {
    try {
      const res = await fetch('/api/watchlist');
      if (!res.ok) throw new Error(`watchlist: HTTP ${res.status}`);
      const data = await res.json();
      setWatchlist(data);
    } catch (err: any) {
      appendError(err?.message || 'Failed to load watchlist');
    }
  }, [appendError]);

  const refreshData = React.useCallback(async () => {
    setRefreshing(true);
    setError(null);
    await Promise.allSettled([fetchStats(), fetchOpportunities(), fetchWatchlist()]);
    setRefreshing(false);
  }, [fetchStats, fetchOpportunities, fetchWatchlist]);

  React.useEffect(() => {
    refreshData();
  }, [refreshData]);

  const chartData = buildChartData(opportunities);
  const totalSavings = stats?.potentialProfit || 0;
  const activeWatchlist = watchlist.filter(w => w.active);

  return (
    <div className="flex flex-col gap-8">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-xl">
          API Error: {error}
        </div>
      )}
      {/* Top Section */}
      <div className="grid grid-cols-12 gap-6">
        {/* Main Chart Card */}
        <div className="col-span-8 glass-card p-8">
          <div className="flex justify-between items-start mb-8">
            <div>
              <h2 className="text-3xl font-bold">{totalSavings.toFixed(0)}€</h2>
              <p className="text-sm text-gray-400">Risparmio Potenziale da {opportunities.length} opportunità</p>
            </div>
            <button
              onClick={refreshData}
              disabled={refreshing}
              className="text-xs font-bold px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition disabled:opacity-50"
            >
              {refreshing ? 'Refreshing…' : 'Refresh data'}
            </button>
          </div>

          <div className="h-[280px] w-full">
            {chartData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#9ca3af' }}
                    dy={10}
                  />
                  <YAxis hide />
                  <Tooltip
                    cursor={{ fill: 'transparent' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const d = payload[0].payload;
                        return (
                          <div className="bg-primary text-white p-3 rounded-xl shadow-xl text-xs">
                            <p className="font-bold mb-1">{d.name} Score</p>
                            <div className="flex justify-between gap-4">
                              <span className="opacity-70">Risparmio</span>
                              <span className="font-bold">{Number(payload[0].value).toFixed(0)}€</span>
                            </div>
                            <div className="flex justify-between gap-4">
                              <span className="opacity-70">Count</span>
                              <span className="font-bold">{d.count}</span>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 6, 6]} barSize={60}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.highlight ? '#84cc16' : '#e5e7eb'}
                        className={entry.highlight ? "opacity-100" : "opacity-50"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                Nessun dato disponibile. Scansiona la watchlist per vedere il risparmio.
              </div>
            )}
          </div>
        </div>

        {/* Side Stats */}
        <div className="col-span-4 flex flex-col gap-6">
          <StatCard
            label="Risparmio Potenziale"
            value={`${totalSavings.toFixed(0)}€`}
          />
          <StatCard
            label="Opportunità"
            value={stats?.opportunitiesFound || 0}
          />
          <StatCard
            label="Avg vs Media"
            value={`${stats?.avgMargin || 0}%`}
          />
          <StatCard
            label="Monitor Attivi"
            value={stats?.totalMonitored || 0}
          />
        </div>
      </div>

      {/* Middle Section - Active Watchlist */}
      <div className="glass-card p-6 flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <h3 className="font-bold">Watchlist Attiva ({activeWatchlist.length})</h3>
        </div>
        {activeWatchlist.length === 0 ? (
          <div className="flex items-center justify-center p-8 text-gray-400 text-sm gap-2">
            <Search size={16} />
            Nessun monitor attivo. Aggiungine uno dalla pagina Watchlist.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {activeWatchlist.map((item, i) => {
              return (
                <div key={item.id} className="flex items-center justify-between p-3 bg-bg-subtle rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      i % 2 === 0 ? "bg-accent/10 text-accent" : "bg-accent-orange/10 text-accent-orange"
                    )}>
                      <Tag size={18} />
                    </div>
                    <div>
                      <p className="text-sm font-bold">{item.query}</p>
                      <p className="text-[10px] text-gray-500">
                        {item.minPrice > 0 ? `€${item.minPrice} - ` : ''}€{item.maxPrice} max • {item.minMargin}% min margin
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Section - Opportunities Table */}
      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-black/5 flex justify-between items-center">
          <h3 className="font-bold">Opportunità Recenti ({opportunities.length})</h3>
          <div className="flex gap-2">
            <button className="text-xs font-bold px-3 py-1.5 rounded-lg bg-gray-100">Tutte</button>
            <button className="text-xs font-bold px-3 py-1.5 rounded-lg text-gray-400 hover:bg-gray-50">Best Deals</button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-gray-400 border-b border-black/5">
                <th className="px-6 py-4 font-bold">Prodotto</th>
                <th className="px-4 py-4 font-bold">Dettagli</th>
                <th className="px-4 py-4 font-bold">Prezzo</th>
                <th className="px-4 py-4 font-bold">Media Cond.</th>
                <th className="px-4 py-4 font-bold">vs Media</th>
                <th className="px-4 py-4 font-bold">Simili</th>
                <th className="px-4 py-4 font-bold">Condizioni</th>
                <th className="px-4 py-4 font-bold">Score</th>
                <th className="px-4 py-4 font-bold">Azione</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {opportunities.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center text-gray-400 text-sm">
                    Nessuna opportunità trovata. Scansiona la watchlist per scoprire affari.
                  </td>
                </tr>
              )}
              {opportunities.map((op) => (
                <tr key={op.id} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <PhotoCarousel photos={op.photos || []} fallbackUrl={op.imageUrl} />
                      <div className="max-w-[200px]">
                        <p className="text-sm font-bold truncate">{op.canonicalName || op.title}</p>
                        {op.canonicalName && op.canonicalName !== op.title && (
                          <p className="text-[9px] text-gray-400 truncate">{op.title}</p>
                        )}
                        <p className="text-[10px] text-gray-500 flex items-center gap-1">
                          <Clock size={10} /> {op.condition}
                        </p>
                        {op.brand && (
                          <span className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded mt-0.5 inline-block">
                            {op.brand}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-col gap-1 text-[10px] text-gray-500">
                      {op.size && <span>Size: {op.size}</span>}
                      <div className="flex items-center gap-2">
                        {op.favouriteCount > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Heart size={10} className="text-red-400" /> {op.favouriteCount}
                          </span>
                        )}
                        {op.viewCount > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Eye size={10} className="text-gray-400" /> {op.viewCount}
                          </span>
                        )}
                      </div>
                      {(op.city || op.country) && (
                        <span className="flex items-center gap-0.5">
                          <MapPin size={10} className="text-gray-400" />
                          {[op.city, op.country].filter(Boolean).join(', ')}
                        </span>
                      )}
                      {op.sellerRating != null && op.sellerRating > 0 && (
                        <span className="flex items-center gap-0.5">
                          <Star size={10} className="text-yellow-500" />
                          {op.sellerRating.toFixed(1)}
                          {op.sellerUsername && (
                            <span className="text-gray-400 ml-0.5">@{op.sellerUsername}</span>
                          )}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <p className="text-sm font-bold">{op.price.toFixed(2)}€</p>
                  </td>
                  <td className="px-4 py-4">
                    <p className="text-sm font-bold text-blue-500">
                      {op.avgPriceSameCondition > 0 ? `${op.avgPriceSameCondition.toFixed(0)}€` : '—'}
                    </p>
                    {op.avgPriceAll > 0 && op.avgPriceAll !== op.avgPriceSameCondition && (
                      <p className="text-[10px] text-gray-400">
                        Tutte: {op.avgPriceAll.toFixed(0)}€
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <PriceVsAvgBadge value={op.priceVsAvg} />
                    {op.marginAbsolute > 0 && (
                      <p className="text-[10px] text-green-600 mt-0.5">
                        -{op.marginAbsolute.toFixed(0)}€
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <Users size={12} className="text-gray-400" />
                      {op.numSimilar}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <ConditionPills breakdown={op.conditionBreakdown} />
                  </td>
                  <td className="px-4 py-4">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-[10px] font-bold uppercase",
                      op.score === 'high' ? "bg-accent/10 text-accent" :
                      op.score === 'medium' ? "bg-yellow-100 text-yellow-700" :
                      "bg-gray-100 text-gray-500"
                    )}>
                      {op.score}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <a
                      href={op.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 bg-white border border-black/5 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center w-8 h-8"
                    >
                      <ExternalLink size={14} className="text-gray-400" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
