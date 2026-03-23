import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import { fileURLToPath } from "url";
import { WatchlistItem, Opportunity, Purchase } from "./src/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Mock Data Store
  let watchlist: WatchlistItem[] = [
    {
      id: "1",
      type: "product",
      query: "Nike Tech Fleece",
      maxPrice: 80,
      minPrice: 0,
      minMargin: 30,
      conditions: ["Nuovo con cartellino", "Ottimo"],
      brandIds: [],
      catalogIds: [],
      sizeIds: [],
      colorIds: [],
      materialIds: [],
      statusIds: [6, 2],
      sortOrder: "newest_first",
      active: true
    },
    {
      id: "2",
      type: "product",
      query: "Sony WH-1000XM5",
      maxPrice: 250,
      minPrice: 0,
      minMargin: 20,
      conditions: ["Ottimo"],
      brandIds: [],
      catalogIds: [],
      sizeIds: [],
      colorIds: [],
      materialIds: [],
      statusIds: [2],
      sortOrder: "newest_first",
      active: true
    }
  ];

  let opportunities: Opportunity[] = [
    {
      id: "v1",
      title: "Nike Tech Fleece Full Zip - Grey",
      description: "Originale, mai usato. Taglia M.",
      price: 45,
      condition: "Nuovo con cartellino",
      imageUrl: "https://picsum.photos/seed/nike/400/400",
      url: "https://vinted.it/items/123",
      publishedAt: new Date().toISOString(),
      brand: "Nike",
      size: "M",
      photos: [],
      favouriteCount: 12,
      viewCount: 45,
      city: "Milano",
      country: "Italia",
      sellerUsername: "user123",
      sellerRating: 4.8,
      avgPriceSameCondition: 72,
      avgPriceAll: 58,
      marginAbsolute: 27,
      priceVsAvg: -37.5,
      numSimilar: 18,
      canonicalName: "Nike Tech Fleece Full Zip Hoodie",
      conditionBreakdown: [
        { condition: "Nuovo con cartellino", avg: 72, min: 45, max: 90, count: 6 },
        { condition: "Ottimo", avg: 55, min: 35, max: 70, count: 8 },
        { condition: "Buono", avg: 40, min: 25, max: 55, count: 4 }
      ],
      score: 'high'
    },
    {
      id: "v2",
      title: "Sony WH-1000XM5 Black",
      description: "Perfette condizioni, scatola inclusa.",
      price: 180,
      condition: "Ottimo",
      imageUrl: "https://picsum.photos/seed/sony/400/400",
      url: "https://vinted.it/items/456",
      publishedAt: new Date().toISOString(),
      brand: "Sony",
      photos: [],
      favouriteCount: 8,
      viewCount: 30,
      city: "Roma",
      country: "Italia",
      sellerUsername: "seller456",
      sellerRating: 4.5,
      avgPriceSameCondition: 220,
      avgPriceAll: 200,
      marginAbsolute: 40,
      priceVsAvg: -18.2,
      numSimilar: 12,
      canonicalName: "Sony WH-1000XM5",
      conditionBreakdown: [
        { condition: "Nuovo con cartellino", avg: 280, min: 250, max: 310, count: 3 },
        { condition: "Ottimo", avg: 220, min: 180, max: 260, count: 7 },
        { condition: "Buono", avg: 170, min: 140, max: 200, count: 2 }
      ],
      score: 'medium'
    },
    {
      id: "v3",
      title: "Nike Tech Fleece Joggers Grey M",
      description: "Usati poche volte, come nuovi.",
      price: 38,
      condition: "Ottimo",
      imageUrl: "https://picsum.photos/seed/nike2/400/400",
      url: "https://vinted.it/items/789",
      publishedAt: new Date().toISOString(),
      brand: "Nike",
      size: "M",
      photos: [],
      favouriteCount: 5,
      viewCount: 22,
      city: "Torino",
      country: "Italia",
      sellerUsername: "seller789",
      sellerRating: 4.2,
      avgPriceSameCondition: 42,
      avgPriceAll: 48,
      marginAbsolute: 4,
      priceVsAvg: -9.5,
      numSimilar: 15,
      canonicalName: "Nike Tech Fleece Joggers",
      conditionBreakdown: [
        { condition: "Nuovo con cartellino", avg: 65, min: 50, max: 80, count: 4 },
        { condition: "Ottimo", avg: 42, min: 30, max: 55, count: 8 },
        { condition: "Buono", avg: 30, min: 20, max: 40, count: 3 }
      ],
      score: 'low'
    }
  ];

  // API Routes
  app.get("/api/watchlist", (req, res) => {
    res.json(watchlist);
  });

  app.post("/api/watchlist", (req, res) => {
    const newItem = { ...req.body, id: Math.random().toString(36).substr(2, 9) };
    watchlist.push(newItem);
    res.json(newItem);
  });

  app.delete("/api/watchlist/:id", (req, res) => {
    watchlist = watchlist.filter(item => item.id !== req.params.id);
    res.sendStatus(204);
  });

  app.get("/api/opportunities", (req, res) => {
    res.json(opportunities);
  });

  app.get("/api/stats", (req, res) => {
    const activeCount = watchlist.filter(w => w.active).length;
    const vsAvgs = opportunities.map(o => o.priceVsAvg).filter(v => v !== 0);
    const avgMargin = vsAvgs.length > 0 ? Math.round((vsAvgs.reduce((a, b) => a + b, 0) / vsAvgs.length) * 10) / 10 : 0;
    const potentialProfit = Math.round(
      opportunities.reduce((acc, op) => acc + Math.max(op.marginAbsolute, 0), 0) * 100
    ) / 100;
    res.json({
      totalMonitored: activeCount,
      opportunitiesFound: opportunities.length,
      avgMargin,
      potentialProfit,
    });
  });

  // Purchases
  let purchasesList: Purchase[] = [];

  app.get("/api/purchases", (req, res) => {
    res.json(purchasesList);
  });

  app.post("/api/purchases", (req, res) => {
    const newPurchase = { ...req.body, id: Math.random().toString(36).substr(2, 9), sold: false, purchasedAt: new Date().toISOString() };
    purchasesList.unshift(newPurchase);
    res.json(newPurchase);
  });

  app.patch("/api/purchases/:id", (req, res) => {
    const idx = purchasesList.findIndex(p => p.id === req.params.id);
    if (idx === -1) return res.sendStatus(404);
    purchasesList[idx] = { ...purchasesList[idx], ...req.body };
    if (req.body.sold) purchasesList[idx].soldAt = new Date().toISOString();
    if (req.body.sold === false) purchasesList[idx].soldAt = undefined;
    res.json(purchasesList[idx]);
  });

  app.delete("/api/purchases/:id", (req, res) => {
    purchasesList = purchasesList.filter(p => p.id !== req.params.id);
    res.sendStatus(204);
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
