import React from 'react';
import { Plus, Trash2, Power, Search, X, RefreshCw, ChevronDown } from 'lucide-react';
import { WatchlistItem } from '../types';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const CONDITION_OPTIONS: { label: string; id: number }[] = [
  { label: 'Nuovo con cartellino', id: 6 },
  { label: 'Nuovo senza cartellino', id: 1 },
  { label: 'Ottimo', id: 2 },
  { label: 'Buono', id: 3 },
  { label: 'Discreto', id: 4 },
];

const SORT_OPTIONS = [
  { value: 'newest_first', label: 'Più recenti' },
  { value: 'relevance', label: 'Rilevanza' },
  { value: 'price_low_to_high', label: 'Prezzo crescente' },
  { value: 'price_high_to_low', label: 'Prezzo decrescente' },
];

const COLOR_OPTIONS: { label: string; id: number; hex: string }[] = [
  { label: 'Nero', id: 1, hex: '#000000' },
  { label: 'Grigio', id: 3, hex: '#9B9B9B' },
  { label: 'Bianco', id: 12, hex: '#FFFFFF' },
  { label: 'Crema', id: 20, hex: '#F5F5DC' },
  { label: 'Beige', id: 4, hex: '#C8AD7F' },
  { label: 'Marrone', id: 23, hex: '#8B4513' },
  { label: 'Rosso', id: 7, hex: '#FF0000' },
  { label: 'Arancione', id: 11, hex: '#FFA500' },
  { label: 'Giallo', id: 10, hex: '#FFD700' },
  { label: 'Verde', id: 9, hex: '#228B22' },
  { label: 'Azzurro', id: 21, hex: '#87CEEB' },
  { label: 'Blu', id: 2, hex: '#0000FF' },
  { label: 'Viola', id: 8, hex: '#800080' },
  { label: 'Rosa', id: 5, hex: '#FF69B4' },
  { label: 'Multicolore', id: 13, hex: 'linear-gradient(135deg, red, orange, yellow, green, blue, purple)' },
];

interface NewItemForm {
  type: string;
  query: string;
  maxPrice: number;
  minPrice: number;
  minMargin: number;
  conditions: string[];
  size: string;
  brandIds: string;
  catalogIds: string;
  sizeIds: string;
  colorIds: number[];
  materialIds: string;
  statusIds: number[];
  sortOrder: string;
}

const emptyForm: NewItemForm = {
  type: 'product',
  query: '',
  maxPrice: 100,
  minPrice: 0,
  minMargin: 20,
  conditions: [],
  size: '',
  brandIds: '',
  catalogIds: '',
  sizeIds: '',
  colorIds: [],
  materialIds: '',
  statusIds: [],
  sortOrder: 'newest_first',
};

function parseIds(str: string): number[] {
  if (!str.trim()) return [];
  return str.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
}

export default function Watchlist() {
  const [items, setItems] = React.useState<WatchlistItem[]>([]);
  const [isAdding, setIsAdding] = React.useState(false);
  const [form, setForm] = React.useState<NewItemForm>(emptyForm);
  const [loading, setLoading] = React.useState(true);
  const [scanning, setScanning] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = React.useState(false);

  const loadWatchlist = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/watchlist');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || 'Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadWatchlist();
  }, [loadWatchlist]);

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/watchlist/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        let detail = '';
        try {
          const body = await res.json();
          detail = body?.detail;
        } catch {
          // ignore
        }
        throw new Error(detail || `HTTP ${res.status}`);
      }
      setItems(prev => prev.filter(i => i.id !== id));
      setError(null);
      // Re-sync from backend to avoid ghosts on the next refresh.
      loadWatchlist();
    } catch (err: any) {
      setError(err?.message ? `Failed to delete monitor: ${err.message}` : 'Failed to delete monitor');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.query.trim()) return;

    try {
      const payload = {
        type: form.type,
        query: form.query,
        maxPrice: form.maxPrice,
        minPrice: form.minPrice,
        minMargin: form.minMargin,
        conditions: form.conditions,
        size: form.size || undefined,
        brandIds: parseIds(form.brandIds),
        catalogIds: parseIds(form.catalogIds),
        sizeIds: parseIds(form.sizeIds),
        colorIds: form.colorIds,
        materialIds: parseIds(form.materialIds),
        statusIds: form.statusIds,
        sortOrder: form.sortOrder,
        active: true,
      };

      const res = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const newItem = await res.json();
      setItems([newItem, ...items]);
      setForm(emptyForm);
      setIsAdding(false);
      setShowAdvanced(false);

      // Trigger immediate scan for this item
      setScanning(true);
      fetch(`/api/scan/${newItem.id}`, { method: 'POST' })
        .then(() => {
          let attempts = 0;
          const poll = setInterval(async () => {
            attempts++;
            if (attempts > 10) { clearInterval(poll); setScanning(false); return; }
            try {
              const statsRes = await fetch('/api/health');
              if (statsRes.ok) {
                const health = await statsRes.json();
                if (health.listings_count > 0) {
                  clearInterval(poll);
                  setScanning(false);
                }
              }
            } catch {}
          }, 3000);
        })
        .catch(() => setScanning(false));
    } catch (err: any) {
      setError(err.message);
    }
  };

  const toggleStatusId = (id: number) => {
    setForm(prev => ({
      ...prev,
      statusIds: prev.statusIds.includes(id)
        ? prev.statusIds.filter(s => s !== id)
        : [...prev.statusIds, id],
    }));
  };

  const toggleColorId = (id: number) => {
    setForm(prev => ({
      ...prev,
      colorIds: prev.colorIds.includes(id)
        ? prev.colorIds.filter(c => c !== id)
        : [...prev.colorIds, id],
    }));
  };

  const conditionLabel = (ids: number[]): string => {
    return ids
      .map(id => CONDITION_OPTIONS.find(c => c.id === id)?.label)
      .filter(Boolean)
      .join(', ');
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Watchlist</h2>
          <p className="text-sm text-gray-500">Manage your automated price monitors.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={async () => {
              setScanning(true);
              try {
                await fetch('/api/scan', { method: 'POST' });
                setTimeout(() => setScanning(false), 5000);
              } catch { setScanning(false); }
            }}
            disabled={scanning}
            className="border border-gray-200 text-gray-600 px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-gray-50 transition-all disabled:opacity-50"
          >
            <RefreshCw size={16} className={scanning ? 'animate-spin' : ''} /> Scan Now
          </button>
          <button
            onClick={() => setIsAdding(true)}
            className="bg-primary text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-black/80 transition-all"
          >
            <Plus size={18} /> Add Monitor
          </button>
        </div>
      </div>

      {/* Add Monitor Modal */}
      {isAdding && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => { setIsAdding(false); setShowAdvanced(false); }}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 flex flex-col gap-5" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold">New Monitor</h3>
              <button onClick={() => { setIsAdding(false); setShowAdvanced(false); }} className="p-1 hover:bg-gray-100 rounded-lg">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Type */}
              <div className="flex gap-2">
                {['product', 'category'].map(t => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setForm(prev => ({ ...prev, type: t }))}
                    className={cn(
                      "px-4 py-2 rounded-lg text-xs font-bold capitalize transition-all",
                      form.type === t ? "bg-primary text-white" : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                    )}
                  >
                    {t}
                  </button>
                ))}
              </div>

              {/* Query */}
              <div>
                <label className="text-xs font-bold text-gray-600 mb-1 block">Search Query</label>
                <input
                  type="text"
                  value={form.query}
                  onChange={e => setForm(prev => ({ ...prev, query: e.target.value }))}
                  placeholder="e.g. iPhone 15 Pro, Nike Tech Fleece..."
                  className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  autoFocus
                />
              </div>

              {/* Price Range & Margin */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Min Price (€)</label>
                  <input
                    type="number"
                    value={form.minPrice}
                    onChange={e => setForm(prev => ({ ...prev, minPrice: Number(e.target.value) }))}
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                    min={0}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Max Price (€)</label>
                  <input
                    type="number"
                    value={form.maxPrice}
                    onChange={e => setForm(prev => ({ ...prev, maxPrice: Number(e.target.value) }))}
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Min Margin (%)</label>
                  <input
                    type="number"
                    value={form.minMargin}
                    onChange={e => setForm(prev => ({ ...prev, minMargin: Number(e.target.value) }))}
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              {/* Conditions (status_ids) */}
              <div>
                <label className="text-xs font-bold text-gray-600 mb-2 block">Condition</label>
                <div className="flex flex-wrap gap-2">
                  {CONDITION_OPTIONS.map(c => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => toggleStatusId(c.id)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                        form.statusIds.includes(c.id)
                          ? "bg-accent/10 text-accent border border-accent/20"
                          : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                      )}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort Order */}
              <div>
                <label className="text-xs font-bold text-gray-600 mb-1 block">Sort Order</label>
                <select
                  value={form.sortOrder}
                  onChange={e => setForm(prev => ({ ...prev, sortOrder: e.target.value }))}
                  className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                >
                  {SORT_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Advanced Filters Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-xs font-bold text-gray-500 hover:text-primary transition-colors self-start"
              >
                <ChevronDown size={14} className={cn("transition-transform", showAdvanced && "rotate-180")} />
                Advanced Filters
              </button>

              {showAdvanced && (
                <div className="flex flex-col gap-4 border-t border-gray-100 pt-4">
                  {/* Colors */}
                  <div>
                    <label className="text-xs font-bold text-gray-600 mb-2 block">Colors</label>
                    <div className="flex flex-wrap gap-2">
                      {COLOR_OPTIONS.map(c => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => toggleColorId(c.id)}
                          className={cn(
                            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                            form.colorIds.includes(c.id)
                              ? "bg-primary/10 text-primary border border-primary/20"
                              : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                          )}
                        >
                          <span
                            className="w-3 h-3 rounded-full border border-gray-300 flex-shrink-0"
                            style={{
                              background: c.hex.startsWith('linear') ? c.hex : c.hex,
                              backgroundColor: c.hex.startsWith('linear') ? undefined : c.hex,
                            }}
                          />
                          {c.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Brand IDs */}
                  <div>
                    <label className="text-xs font-bold text-gray-600 mb-1 block">Brand IDs (comma separated)</label>
                    <input
                      type="text"
                      value={form.brandIds}
                      onChange={e => setForm(prev => ({ ...prev, brandIds: e.target.value }))}
                      placeholder="e.g. 319 for Apple, 7 for Nike..."
                      className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  {/* Category IDs */}
                  <div>
                    <label className="text-xs font-bold text-gray-600 mb-1 block">Category IDs (comma separated)</label>
                    <input
                      type="text"
                      value={form.catalogIds}
                      onChange={e => setForm(prev => ({ ...prev, catalogIds: e.target.value }))}
                      placeholder="e.g. 2405 for Smartphones..."
                      className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {/* Size IDs */}
                    <div>
                      <label className="text-xs font-bold text-gray-600 mb-1 block">Size IDs (comma separated)</label>
                      <input
                        type="text"
                        value={form.sizeIds}
                        onChange={e => setForm(prev => ({ ...prev, sizeIds: e.target.value }))}
                        placeholder="e.g. 206, 207..."
                        className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                      />
                    </div>

                    {/* Material IDs */}
                    <div>
                      <label className="text-xs font-bold text-gray-600 mb-1 block">Material IDs (comma separated)</label>
                      <input
                        type="text"
                        value={form.materialIds}
                        onChange={e => setForm(prev => ({ ...prev, materialIds: e.target.value }))}
                        placeholder="e.g. 1, 2..."
                        className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  {/* Size (text, legacy) */}
                  <div>
                    <label className="text-xs font-bold text-gray-600 mb-1 block">Size (text, optional)</label>
                    <input
                      type="text"
                      value={form.size}
                      onChange={e => setForm(prev => ({ ...prev, size: e.target.value }))}
                      placeholder="e.g. M, 42, 128GB..."
                      className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                className="bg-primary text-white py-3 rounded-xl text-sm font-bold hover:bg-black/80 transition-all mt-2"
              >
                Start Monitoring
              </button>
            </form>
          </div>
        </div>
      )}

      {scanning && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 text-sm p-4 rounded-xl flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Scanning Vinted for new listings... This may take a few seconds.
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-xl">
          Error: {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Filters */}
        <div className="col-span-3 flex flex-col gap-6">
          <div className="glass-card p-6 flex flex-col gap-4">
            <h3 className="text-sm font-bold">Filters</h3>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
              <input
                type="text"
                placeholder="Search monitors..."
                className="w-full bg-gray-100 border-none rounded-lg py-2 pl-9 pr-4 text-xs focus:ring-0"
              />
            </div>

            <div className="flex flex-col gap-2 mt-2">
              <label className="flex items-center gap-2 text-xs font-medium text-gray-600 cursor-pointer">
                <input type="checkbox" className="rounded border-gray-300 text-primary focus:ring-primary" defaultChecked />
                Active Monitors
              </label>
              <label className="flex items-center gap-2 text-xs font-medium text-gray-600 cursor-pointer">
                <input type="checkbox" className="rounded border-gray-300 text-primary focus:ring-primary" />
                Paused
              </label>
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-sm font-bold mb-4">Quick Stats</h3>
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Total Active</span>
                <span className="text-xs font-bold">{items.filter(i => i.active).length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Total Monitors</span>
                <span className="text-xs font-bold">{items.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* List */}
        <div className="col-span-9 flex flex-col gap-4">
          {loading && (
            <div className="glass-card p-12 flex items-center justify-center">
              <p className="text-sm text-gray-400">Loading...</p>
            </div>
          )}

          {!loading && items.map((item) => (
            <div key={item.id} className="glass-card p-6 flex items-center justify-between group">
              <div className="flex items-center gap-4">
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center",
                  item.active ? "bg-accent/10 text-accent" : "bg-gray-100 text-gray-400"
                )}>
                  <Power size={20} />
                </div>
                <div>
                  <h4 className="font-bold">{item.query}</h4>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {item.type}
                    </span>
                    <span className="text-[10px] text-gray-500">
                      {item.minPrice > 0 ? `€${item.minPrice}` : '€0'} - €{item.maxPrice} • Min Margin: {item.minMargin}%
                    </span>
                    {item.statusIds && item.statusIds.length > 0 && (
                      <span className="text-[10px] text-gray-500">
                        • {conditionLabel(item.statusIds)}
                      </span>
                    )}
                    {item.brandIds && item.brandIds.length > 0 && (
                      <span className="text-[10px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">
                        Brand: {item.brandIds.join(', ')}
                      </span>
                    )}
                    {item.colorIds && item.colorIds.length > 0 && (
                      <span className="text-[10px] text-purple-500 bg-purple-50 px-1.5 py-0.5 rounded">
                        {item.colorIds.length} color{item.colorIds.length > 1 ? 's' : ''}
                      </span>
                    )}
                    {item.sortOrder && item.sortOrder !== 'newest_first' && (
                      <span className="text-[10px] text-gray-400">
                        • {SORT_OPTIONS.find(s => s.value === item.sortOrder)?.label}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => handleDelete(item.id)}
                  className="p-2 hover:bg-red-50 rounded-lg transition-colors text-gray-400 hover:text-red-500"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}

          {!loading && items.length === 0 && (
            <div className="glass-card p-12 flex flex-col items-center justify-center text-center gap-4">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-gray-400">
                <Search size={32} />
              </div>
              <div>
                <h4 className="font-bold">No monitors found</h4>
                <p className="text-sm text-gray-500">Start by adding a product or category to monitor.</p>
              </div>
              <button
                onClick={() => setIsAdding(true)}
                className="text-sm font-bold text-primary hover:underline"
              >
                Add your first monitor
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
