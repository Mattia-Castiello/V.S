import React from 'react';
import { Plus, Trash2, Check, X, Edit3, ShoppingBag, Package, ExternalLink } from 'lucide-react';
import { Purchase } from '../types';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NewPurchaseForm {
  title: string;
  imageUrl: string;
  url: string;
  brand: string;
  condition: string;
  vintedPrice: number;
  purchasePrice: number;
  notes: string;
}

const emptyForm: NewPurchaseForm = {
  title: '',
  imageUrl: '',
  url: '',
  brand: '',
  condition: '',
  vintedPrice: 0,
  purchasePrice: 0,
  notes: '',
};

export default function Purchases() {
  const [purchases, setPurchases] = React.useState<Purchase[]>([]);
  const [isAdding, setIsAdding] = React.useState(false);
  const [form, setForm] = React.useState<NewPurchaseForm>(emptyForm);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editResale, setEditResale] = React.useState<number>(0);
  const [editPurchasePrice, setEditPurchasePrice] = React.useState<number>(0);
  const [editNotes, setEditNotes] = React.useState<string>('');
  const [filter, setFilter] = React.useState<'all' | 'active' | 'sold'>('all');

  React.useEffect(() => {
    fetch('/api/purchases')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setPurchases)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    try {
      const res = await fetch('/api/purchases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const newPurchase = await res.json();
      setPurchases([newPurchase, ...purchases]);
      setForm(emptyForm);
      setIsAdding(false);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    await fetch(`/api/purchases/${id}`, { method: 'DELETE' });
    setPurchases(purchases.filter(p => p.id !== id));
  };

  const handleMarkSold = async (id: string) => {
    const res = await fetch(`/api/purchases/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sold: true }),
    });
    if (res.ok) {
      const updated = await res.json();
      setPurchases(purchases.map(p => p.id === id ? updated : p));
    }
  };

  const handleMarkUnsold = async (id: string) => {
    const res = await fetch(`/api/purchases/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sold: false }),
    });
    if (res.ok) {
      const updated = await res.json();
      setPurchases(purchases.map(p => p.id === id ? updated : p));
    }
  };

  const startEditing = (p: Purchase) => {
    setEditingId(p.id);
    setEditPurchasePrice(p.purchasePrice);
    setEditResale(p.resalePrice || 0);
    setEditNotes(p.notes || '');
  };

  const saveEdit = async () => {
    if (!editingId) return;
    const res = await fetch(`/api/purchases/${editingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        purchasePrice: editPurchasePrice,
        resalePrice: editResale || null,
        notes: editNotes,
      }),
    });
    if (res.ok) {
      const updated = await res.json();
      setPurchases(purchases.map(p => p.id === editingId ? updated : p));
    }
    setEditingId(null);
  };

  const filtered = purchases.filter(p => {
    if (filter === 'active') return !p.sold;
    if (filter === 'sold') return p.sold;
    return true;
  });

  const totalSpent = purchases.reduce((s, p) => s + p.purchasePrice, 0);
  const totalResale = purchases.filter(p => p.resalePrice).reduce((s, p) => s + (p.resalePrice || 0), 0);
  const soldPurchases = purchases.filter(p => p.sold && p.resalePrice);
  const realizedProfit = soldPurchases.reduce((s, p) => s + ((p.resalePrice || 0) - p.purchasePrice), 0);
  const activePurchases = purchases.filter(p => !p.sold);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Purchases</h2>
          <p className="text-sm text-gray-500">Track your buys, resale prices and profits.</p>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="bg-primary text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-black/80 transition-all"
        >
          <Plus size={18} /> Add Purchase
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card p-5 flex flex-col gap-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Spent</p>
          <h3 className="text-2xl font-bold">{totalSpent.toFixed(0)}€</h3>
          <span className="text-[10px] text-gray-400">{purchases.length} items</span>
        </div>
        <div className="glass-card p-5 flex flex-col gap-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Expected Resale</p>
          <h3 className="text-2xl font-bold">{totalResale.toFixed(0)}€</h3>
          <span className="text-[10px] text-gray-400">{purchases.filter(p => p.resalePrice).length} priced</span>
        </div>
        <div className="glass-card p-5 flex flex-col gap-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Realized Profit</p>
          <h3 className={cn("text-2xl font-bold", realizedProfit >= 0 ? "text-accent" : "text-red-500")}>
            {realizedProfit >= 0 ? '+' : ''}{realizedProfit.toFixed(0)}€
          </h3>
          <span className="text-[10px] text-gray-400">{soldPurchases.length} sold</span>
        </div>
        <div className="glass-card p-5 flex flex-col gap-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">In Stock</p>
          <h3 className="text-2xl font-bold">{activePurchases.length}</h3>
          <span className="text-[10px] text-gray-400">{activePurchases.reduce((s, p) => s + p.purchasePrice, 0).toFixed(0)}€ invested</span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {(['all', 'active', 'sold'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "text-xs font-bold px-4 py-2 rounded-lg capitalize transition-all",
              filter === f ? "bg-primary text-white" : "bg-gray-100 text-gray-500 hover:bg-gray-200"
            )}
          >
            {f === 'all' ? `All (${purchases.length})` : f === 'active' ? `In Stock (${activePurchases.length})` : `Sold (${soldPurchases.length})`}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-xl">
          Error: {error}
        </div>
      )}

      {/* Add Purchase Modal */}
      {isAdding && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setIsAdding(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 flex flex-col gap-5" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold">New Purchase</h3>
              <button onClick={() => setIsAdding(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="text-xs font-bold text-gray-600 mb-1 block">Title</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={e => setForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="e.g. Nike Tech Fleece Grey M"
                  className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  autoFocus
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Vinted Price (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={form.vintedPrice}
                    onChange={e => setForm(prev => ({ ...prev, vintedPrice: Number(e.target.value) }))}
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Purchase Price (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={form.purchasePrice}
                    onChange={e => setForm(prev => ({ ...prev, purchasePrice: Number(e.target.value) }))}
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Brand (optional)</label>
                  <input
                    type="text"
                    value={form.brand}
                    onChange={e => setForm(prev => ({ ...prev, brand: e.target.value }))}
                    placeholder="e.g. Nike"
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-600 mb-1 block">Condition</label>
                  <input
                    type="text"
                    value={form.condition}
                    onChange={e => setForm(prev => ({ ...prev, condition: e.target.value }))}
                    placeholder="e.g. Nuovo con cartellino"
                    className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-gray-600 mb-1 block">Vinted URL (optional)</label>
                <input
                  type="text"
                  value={form.url}
                  onChange={e => setForm(prev => ({ ...prev, url: e.target.value }))}
                  placeholder="https://vinted.it/items/..."
                  className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-600 mb-1 block">Notes (optional)</label>
                <textarea
                  value={form.notes}
                  onChange={e => setForm(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Any notes about the purchase..."
                  className="w-full bg-gray-100 border-none rounded-lg py-2.5 px-4 text-sm focus:ring-2 focus:ring-primary/20 resize-none h-20"
                />
              </div>
              <button
                type="submit"
                className="bg-primary text-white py-3 rounded-xl text-sm font-bold hover:bg-black/80 transition-all mt-2"
              >
                Save Purchase
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Purchases List */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-gray-400 border-b border-black/5">
                <th className="px-6 py-4 font-bold">Item</th>
                <th className="px-4 py-4 font-bold">Vinted Price</th>
                <th className="px-4 py-4 font-bold">Purchase Price</th>
                <th className="px-4 py-4 font-bold">Resale Price</th>
                <th className="px-4 py-4 font-bold">Profit</th>
                <th className="px-4 py-4 font-bold">Status</th>
                <th className="px-4 py-4 font-bold">Notes</th>
                <th className="px-4 py-4 font-bold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {loading && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-400 text-sm">Loading...</td>
                </tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-400 text-sm">
                    <div className="flex flex-col items-center gap-3">
                      <ShoppingBag size={32} className="text-gray-300" />
                      <p>No purchases yet. Track your first buy!</p>
                    </div>
                  </td>
                </tr>
              )}
              {filtered.map(p => {
                const profit = p.resalePrice ? p.resalePrice - p.purchasePrice : null;
                const isEditing = editingId === p.id;

                return (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {p.imageUrl ? (
                          <img src={p.imageUrl} className="w-10 h-10 rounded-lg object-cover" alt="" />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                            <Package size={18} className="text-gray-400" />
                          </div>
                        )}
                        <div>
                          <p className="text-sm font-bold">{p.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {p.brand && (
                              <span className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">{p.brand}</span>
                            )}
                            {p.condition && (
                              <span className="text-[10px] text-gray-500">{p.condition}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-sm text-gray-400">{p.vintedPrice.toFixed(2)}€</p>
                    </td>
                    <td className="px-4 py-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editPurchasePrice}
                          onChange={e => setEditPurchasePrice(Number(e.target.value))}
                          className="w-20 bg-gray-100 border-none rounded py-1 px-2 text-sm"
                        />
                      ) : (
                        <p className="text-sm font-bold">{p.purchasePrice.toFixed(2)}€</p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="0.01"
                          value={editResale}
                          onChange={e => setEditResale(Number(e.target.value))}
                          placeholder="0.00"
                          className="w-20 bg-gray-100 border-none rounded py-1 px-2 text-sm"
                        />
                      ) : (
                        <p className={cn("text-sm font-bold", p.resalePrice ? "text-blue-500" : "text-gray-300")}>
                          {p.resalePrice ? `${p.resalePrice.toFixed(2)}€` : '—'}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      {profit !== null ? (
                        <span className={cn("text-sm font-bold", profit >= 0 ? "text-accent" : "text-red-500")}>
                          {profit >= 0 ? '+' : ''}{profit.toFixed(0)}€
                        </span>
                      ) : (
                        <span className="text-sm text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <span className={cn(
                        "px-2 py-1 rounded-full text-[10px] font-bold uppercase",
                        p.sold ? "bg-accent/10 text-accent" : "bg-yellow-100 text-yellow-700"
                      )}>
                        {p.sold ? 'Sold' : 'In Stock'}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      {isEditing ? (
                        <textarea
                          value={editNotes}
                          onChange={e => setEditNotes(e.target.value)}
                          className="w-32 bg-gray-100 border-none rounded py-1 px-2 text-xs resize-none h-12"
                        />
                      ) : (
                        <p className="text-xs text-gray-500 max-w-[120px] truncate">{p.notes || '—'}</p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1">
                        {isEditing ? (
                          <>
                            <button onClick={saveEdit} className="p-1.5 hover:bg-accent/10 rounded-lg text-accent" title="Save">
                              <Check size={14} />
                            </button>
                            <button onClick={() => setEditingId(null)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400" title="Cancel">
                              <X size={14} />
                            </button>
                          </>
                        ) : (
                          <>
                            <button onClick={() => startEditing(p)} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400" title="Edit">
                              <Edit3 size={14} />
                            </button>
                            {!p.sold ? (
                              <button onClick={() => handleMarkSold(p.id)} className="p-1.5 hover:bg-accent/10 rounded-lg text-gray-400 hover:text-accent" title="Mark as sold">
                                <Check size={14} />
                              </button>
                            ) : (
                              <button onClick={() => handleMarkUnsold(p.id)} className="p-1.5 hover:bg-yellow-50 rounded-lg text-gray-400 hover:text-yellow-600" title="Mark as unsold">
                                <Package size={14} />
                              </button>
                            )}
                            {p.url && (
                              <a href={p.url} target="_blank" rel="noopener noreferrer" className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400" title="Open on Vinted">
                                <ExternalLink size={14} />
                              </a>
                            )}
                            <button onClick={() => handleDelete(p.id)} className="p-1.5 hover:bg-red-50 rounded-lg text-gray-400 hover:text-red-500" title="Delete">
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
