import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, Package, Menu, X, Search, ArrowRight, ShieldCheck, Zap, Trash2, Plus, CheckCircle, LogIn, LogOut, User, Sparkle, Star, Heart } from 'lucide-react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import API from './services/api';
import LoginPage from './auth/LoginPage';
import RegisterPage from './auth/RegisterPage';

const DEMO_USER = 'demo-user';

/* ------------------------------------------------------------------ */
/* Header - Glassmorphism Luxury                                        */
/* ------------------------------------------------------------------ */
function Header({ cartCount }) {
  const [open, setOpen] = useState(false);
  const { user, logout, loading } = useAuth();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/[0.04]">
      <div className="max-w-6xl mx-auto px-6 h-[72px] flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold to-coral flex items-center justify-center shadow-lg shadow-gold/20 group-hover:shadow-gold/40 transition duration-500">
            <Sparkle size={20} strokeWidth={2} className="text-ink" />
          </div>
          <span className="text-2xl font-serif font-bold tracking-tight text-white">Aura<span className="text-gradient-gold">Commerce</span></span>
        </Link>

        <nav className="hidden md:flex items-center gap-10 text-[13px] font-medium tracking-wide uppercase text-mist/80">
          <Link to="/" className="hover:text-white transition duration-300 relative group">Products
            <span className="absolute -bottom-1 left-0 w-0 h-[1.5px] bg-gradient-to-r from-gold to-coral group-hover:w-full transition-all duration-300" />
          </Link>
          <Link to="/cart" className="hover:text-white transition duration-300 relative group">Cart
            <span className="absolute -bottom-1 left-0 w-0 h-[1.5px] bg-gradient-to-r from-gold to-coral group-hover:w-full transition-all duration-300" />
          </Link>
          <Link to="/orders" className="hover:text-white transition duration-300 relative group">Orders
            <span className="absolute -bottom-1 left-0 w-0 h-[1.5px] bg-gradient-to-r from-gold to-coral group-hover:w-full transition-all duration-300" />
          </Link>
          <Link to="/notifications" className="hover:text-white transition duration-300 relative group">Notifications
            <span className="absolute -bottom-1 left-0 w-0 h-[1.5px] bg-gradient-to-r from-gold to-coral group-hover:w-full transition-all duration-300" />
          </Link>
        </nav>

        <div className="hidden md:flex items-center gap-5">
          {!loading && user ? (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-xs tracking-wide text-white/80">
                <User size={12} className="text-gold" /> <span className="font-medium">{user.user_id}</span>
              </div>
              <button onClick={logout} className="text-xs text-coralSoft hover:text-coral transition duration-300 font-medium flex items-center gap-1.5">
                <LogOut size={13} /> Sign Out
              </button>
            </div>
          ) : !loading && (
            <Link to="/login" className="text-xs tracking-wide text-white/60 hover:text-white transition duration-300 font-medium flex items-center gap-1.5">
              <LogIn size={13} /> Sign In
            </Link>
          )}
          <Link to="/cart" className="relative inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-gradient-to-r from-gold to-coral text-ink font-bold text-sm hover:brightness-110 transition duration-300 shadow-lg shadow-gold/15">
            <ShoppingCart size={16} strokeWidth={2.5} />
            <span>Cart</span>
            {cartCount > 0 && <span className="absolute -top-1.5 -right-1 w-5 h-5 bg-ink text-gold text-[10px] font-extrabold rounded-full flex items-center justify-center border border-gold/30">{cartCount}</span>}
          </Link>
        </div>

        <button onClick={() => setOpen(!open)} className="md:hidden w-10 h-10 rounded-xl glass flex items-center justify-center text-white hover:bg-white/10 transition">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden glass border-t border-white/[0.05] px-6 py-6 flex flex-col gap-4 animate-fade-up">
          <Link to="/" onClick={() => setOpen(false)} className="text-lg font-serif text-white">Products</Link>
          <Link to="/cart" onClick={() => setOpen(false)} className="text-lg font-serif text-white">Cart</Link>
          <Link to="/orders" onClick={() => setOpen(false)} className="text-lg font-serif text-white">Orders</Link>
          <Link to="/notifications" onClick={() => setOpen(false)} className="text-lg font-serif text-white">Notifications</Link>
          {!loading && user ? (
            <button onClick={() => { logout(); setOpen(false); }} className="text-left text-coralSoft">Sign Out</button>
          ) : !loading && (
            <Link to="/login" onClick={() => setOpen(false)} className="text-left text-gold">Sign In</Link>
          )}
        </div>
      )}
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* Hero - Premium Luxury                                                 */
/* ------------------------------------------------------------------ */
function Hero() {
  return (
    <section className="relative min-h-[92vh] flex items-center overflow-hidden">
      {/* Background layers */}
      <div className="absolute inset-0 bg-gradient-to-b from-ink via-[#070c1a] to-[#060a14]" />
      <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full bg-gold/10 blur-[150px]" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full bg-rose/10 blur-[120px]" />
      <div className="absolute top-1/3 left-1/3 w-[300px] h-[300px] rounded-full bg-tealSoft/10 blur-[100px]" />

      <div className="relative max-w-6xl mx-auto px-6 py-32 md:py-40">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="animate-fade-up">
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full glass mb-8 border border-white/[0.06]">
              <Star size={13} className="text-gold fill-gold" />
              <span className="text-[11px] font-medium tracking-[0.15em] uppercase text-white/60">AI-Powered Luxury Marketplace</span>
            </div>
            <h1 className="text-[3.5rem] md:text-[5rem] lg:text-[6rem] font-serif font-light leading-[0.92] text-white mb-8 tracking-tight">
              <span className="block">Discover</span>
              <span className="block text-gradient-gold">Excellence.</span>
              <span className="block italic font-light text-white/50">Every detail.</span>
            </h1>
            <p className="text-lg md:text-xl text-white/50 leading-relaxed max-w-md mb-10 font-light">
              A curated luxury e-commerce experience built on resilient microservices architecture, real-time events, and AI-driven incident management.
            </p>
            <div className="flex gap-4">
              <a href="#catalog" className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-gradient-to-r from-gold to-coral text-ink font-bold text-sm tracking-wide hover:brightness-110 transition duration-300 shadow-2xl shadow-gold/20 gold-glow">
                Explore Catalog <ArrowRight size={16} strokeWidth={2.5} />
              </a>
            </div>
          </div>

          {/* Featured product card in hero */}
          <div className="hidden lg:block animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="glass rounded-[32px] p-6 gold-glow relative overflow-hidden">
              <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-gold/20 to-transparent rounded-full -translate-y-1/4 translate-x-1/4" />
              <img src="/products/fashion-gown.jpg" alt="Luxury fashion" className="w-full h-[420px] object-cover rounded-2xl mb-6 shadow-2xl shadow-black/30" />
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-2xl font-serif font-medium text-white mb-1">Silk Evening Gown</h3>
                  <p className="text-sm text-white/40 font-light">Midnight silk with pearl embroidery</p>
                </div>
                <span className="text-xl font-serif text-gold">$389</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Product Card - Luxury                                                */
/* ------------------------------------------------------------------ */
function ProductCard({ p, onAdd }) {
  const imgPath = `/products/${p.image_url ? p.image_url.split('/').pop() : p.sku.toLowerCase() + '.jpg'}`;
  return (
    <div className="group glass rounded-[28px] overflow-hidden glass-hover transition-all duration-500 hover:-translate-y-3 hover:shadow-2xl hover:shadow-gold/10 flex flex-col">
      <div className="relative overflow-hidden">
        <img
          src={imgPath}
          alt={p.name}
          className="w-full h-[320px] object-cover transition-transform duration-700 group-hover:scale-110"
          onError={(e) => { e.target.src = `https://picsum.photos/seed/${p.id || p.sku}/600/480`; }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-ink/60 via-transparent to-transparent" />
        <div className="absolute top-4 left-4">
          <span className="px-3 py-1 rounded-full glass text-[11px] font-semibold tracking-wide uppercase text-white/70 border border-white/[0.08]">{p.category}</span>
        </div>
        <div className="absolute bottom-4 right-4">
          <button onClick={() => onAdd(p)} className="w-10 h-10 rounded-full bg-gradient-to-br from-gold to-coral text-ink flex items-center justify-center shadow-lg shadow-gold/30 hover:scale-110 transition duration-300">
            <Plus size={18} strokeWidth={2.5} />
          </button>
        </div>
      </div>
      <div className="p-6 flex flex-col flex-1">
        <h3 className="text-xl font-serif font-medium text-white mb-2 group-hover:text-gold transition-colors duration-300">{p.name}</h3>
        <p className="text-sm text-white/40 mb-5 leading-relaxed font-light flex-1">{p.description}</p>
        <div className="flex items-end justify-between pt-4 border-t border-white/[0.06]">
          <span className="text-sm text-white/30 font-light">SKU: {p.sku}</span>
          <span className="text-2xl font-serif font-medium text-gradient-gold">${parseFloat(p.price || 0).toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Products Page                                                        */
/* ------------------------------------------------------------------ */
function ProductsPage({ onAddToCart }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await API.products(search, selectedCategory);
      setProducts(data.results || data);
    } catch (e) {
      setProducts([
        { id: 'f1', name: 'Silk Evening Gown', description: 'Luxurious midnight silk evening gown with delicate pearl embroidery.', price: 389.00, category: 'Fashion', sku: 'FASH-001', image_url: '/products/fashion-gown.jpg' },
        { id: 'e1', name: 'Noise-Canceling Headphones', description: 'Premium over-ear headphones with 40-hour battery and crystal-clear audio.', price: 349.99, category: 'Electronics', sku: 'ELEC-001', image_url: '/products/electronics-headphones.jpg' },
        { id: 'c1', name: 'Organic Rose Serum', description: 'Anti-aging facial serum with organic rose extract and vitamin C.', price: 89.50, category: 'Cosmetics', sku: 'COSM-001', image_url: '/products/cosmetics-serum.jpg' },
        { id: 'f2', name: 'Artisan Leather Tote', description: 'Handcrafted Italian full-grain leather tote with brass hardware.', price: 425.00, category: 'Fashion', sku: 'FASH-002', image_url: '/products/fashion-tote.jpg' },
        { id: 'e2', name: 'Smart Mirror Pro', description: 'Interactive smart mirror with fitness tracking and AI skin analysis.', price: 599.00, category: 'Electronics', sku: 'ELEC-002', image_url: '/products/electronics-mirror.jpg' },
        { id: 'c2', name: 'Luxury Bath Gift Set', description: 'Spa gift set with lavender salts, body scrub, silk eye mask and candle.', price: 129.99, category: 'Cosmetics', sku: 'COSM-002', image_url: '/products/cosmetics-bath.jpg' },
      ]);
    } finally { setLoading(false); }
  }, [search, selectedCategory]);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  useEffect(() => {
    (async () => {
      try {
        const data = await API.categories();
        setCategories(data.categories || ['Fashion', 'Electronics', 'Cosmetics', 'Sports', 'Home']);
      } catch (e) {
        setCategories(['Fashion', 'Electronics', 'Cosmetics', 'Sports', 'Home']);
      }
    })();
  }, []);

  const handleSearch = (e) => { e.preventDefault(); loadProducts(); };
  const handleCategoryClick = (cat) => { setSelectedCategory(cat === selectedCategory ? '' : cat); };

  return (
    <section id="catalog" className="max-w-6xl mx-auto px-6 pt-28 pb-32">
      <div className="text-center mb-16">
        <span className="inline-block text-[11px] tracking-[0.3em] uppercase text-gold/80 mb-6 font-medium">Curated Collection</span>
        <h2 className="text-5xl md:text-6xl font-serif font-light text-white mb-6 tracking-tight">The Art of <span className="italic font-normal text-gradient-gold">Luxury</span></h2>
        <p className="text-white/30 max-w-lg mx-auto font-light text-lg">Discover hand-selected products from the world's finest artisans, designers, and innovators.</p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-14">
        <form onSubmit={handleSearch} className="relative w-full md:w-[420px]">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" />
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search fashion, electronics, cosmetics..."
            className="w-full pl-11 pr-5 py-3.5 rounded-2xl glass text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-gold/30 focus:bg-white/[0.06] transition-all duration-300"
          />
        </form>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => handleCategoryClick('')} className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide border transition duration-300 ${selectedCategory === '' ? 'bg-gradient-to-r from-gold to-coral text-ink border-transparent' : 'glass text-white/50 hover:text-white border-white/10'}`}>
            All
          </button>
          {categories.map(cat => (
            <button key={cat} onClick={() => handleCategoryClick(cat)} className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide border transition duration-300 ${selectedCategory === cat ? 'bg-gradient-to-r from-gold to-coral text-ink border-transparent' : 'glass text-white/50 hover:text-white border-white/10'}`}>
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[1, 2, 3, 4, 5, 6].map(i => <div key={i} className="h-[480px] rounded-[28px] glass animate-pulse" />)}
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-24 text-white/20 font-serif text-2xl">No treasures found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {products.map(p => <ProductCard key={p.id || p.sku} p={p} onAdd={onAddToCart} />)}
        </div>
      )}
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* Cart Page - Elegant                                                    */
/* ------------------------------------------------------------------ */
function CartPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();
  const userId = user ? user.user_id : DEMO_USER;

  const loadCart = useCallback(async () => {
    setLoading(true); try { const data = await API.cart(userId); setItems(data.items || []); } catch (e) { setItems([]); } finally { setLoading(false); }
  }, [userId]);

  useEffect(() => { loadCart(); }, [loadCart]);

  const handleRemove = async (itemId) => { await API.removeCartItem(userId, itemId); loadCart(); };
  const handleClear = async () => { await API.clearCart(userId); loadCart(); };
  const handleCheckout = async () => { if (items.length === 0) return; await API.createOrder(userId, items); await handleClear(); navigate('/orders'); };
  const total = items.reduce((sum, i) => sum + (i.quantity || 1) * parseFloat(i.product_price || 25.99), 0);

  return (
    <div className="max-w-5xl mx-auto px-6 pt-28 pb-20">
      <h2 className="text-4xl md:text-5xl font-serif font-light text-white mb-3">Your <span className="italic text-gradient-gold">Selection</span></h2>
      <p className="text-white/20 mb-14 font-light">Curated items awaiting your approval.</p>

      {loading ? <div className="h-[400px] rounded-[28px] glass animate-pulse" /> : items.length === 0 ? (
        <div className="glass rounded-[32px] p-16 text-center">
          <ShoppingCart size={48} className="mx-auto text-white/10 mb-6" />
          <h3 className="text-2xl font-serif text-white mb-3">Cart is empty</h3>
          <p className="text-white/20 mb-8">Browse the collection and add pieces that resonate with you.</p>
          <Link to="/" className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-gradient-to-r from-gold to-coral text-ink font-bold hover:brightness-110 transition shadow-xl shadow-gold/10">Browse Catalog <ArrowRight size={16} /></Link>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map(item => (
            <div key={item.id} className="glass rounded-[24px] p-5 flex items-center gap-6 glass-hover transition-all duration-300">
              <img src={`https://picsum.photos/seed/${item.product_id}/120/120`} alt={item.product_name} className="w-20 h-20 rounded-2xl object-cover shadow-lg" onError={e => { e.target.src = 'https://images.unsplash.com/photo-1518770660439-4636500cff5f?w=200&q=80'; }} />
              <div className="flex-1">
                <h4 className="font-serif text-xl text-white mb-0.5">{item.product_name || 'Luxury Item'}</h4>
                <p className="text-xs text-white/20 tracking-wide">Qty: {item.quantity}</p>
                <p className="text-sm text-white/40 font-light">${(parseFloat(item.product_price || 25.99) * item.quantity).toFixed(2)}</p>
              </div>
              <button onClick={() => handleRemove(item.id)} className="w-10 h-10 rounded-full glass flex items-center justify-center text-coral hover:text-white hover:bg-coral/10 transition duration-300"><Trash2 size={16} /></button>
            </div>
          ))}
          <div className="glass rounded-[32px] p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <span className="text-xs tracking-[0.2em] uppercase text-white/20 block mb-1">Total</span>
              <span className="text-4xl font-serif font-light text-gradient-gold">${total.toFixed(2)}</span>
            </div>
            <button onClick={handleCheckout} className="px-10 py-4 rounded-full bg-gradient-to-r from-gold to-coral text-ink font-bold tracking-wide hover:brightness-110 transition shadow-2xl shadow-gold/15">Complete Order</button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Orders Page - Premium                                                 */
/* ------------------------------------------------------------------ */
function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const userId = user ? user.user_id : DEMO_USER;

  const loadOrders = useCallback(async () => {
    setLoading(true); try { const data = await API.orders(userId); setOrders(data || []); } catch (e) { setOrders([]); } finally { setLoading(false); }
  }, [userId]);

  useEffect(() => { loadOrders(); }, [loadOrders]);

  const statusColor = (s) => {
    if (s === 'pending') return 'text-amber-300';
    if (['confirmed', 'shipped', 'delivered'].includes(s)) return 'text-teal-400';
    return 'text-rose-400';
  };

  return (
    <div className="max-w-5xl mx-auto px-6 pt-28 pb-20">
      <h2 className="text-4xl md:text-5xl font-serif font-light text-white mb-3">Your <span className="italic text-gradient-gold">Orders</span></h2>
      <p className="text-white/20 mb-14 font-light">Live transactions flowing through our event-driven architecture.</p>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-6">{[1, 2].map(i => <div key={i} className="h-[280px] rounded-[28px] glass animate-pulse" />)}</div>
      ) : orders.length === 0 ? (
        <div className="glass rounded-[32px] p-16 text-center">
          <Package size={48} className="mx-auto text-white/10 mb-6" />
          <h3 className="text-2xl font-serif text-white mb-3">No orders placed</h3>
          <p className="text-white/20 mb-8">Begin your journey by selecting from our curated collection.</p>
          <Link to="/cart" className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-gold to-coral text-ink font-bold hover:brightness-110 transition shadow-xl shadow-gold/10">Go to Cart <ArrowRight size={18} /></Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {orders.map(order => (
            <div key={order.id} className="glass rounded-[28px] p-7 glass-hover transition-all duration-300 hover:-translate-y-1">
              <div className="flex items-center justify-between mb-5">
                <span className="text-[11px] font-mono text-white/20 tracking-wider">{order.id?.slice(-8) || 'N/A'}</span>
                <span className={`text-[10px] font-extrabold uppercase tracking-[0.15em] px-3 py-1 rounded-full border ${statusColor(order.status)} bg-white/[0.03] border-white/[0.06]`}>{order.status}</span>
              </div>
              <h4 className="font-serif text-xl text-white mb-2">Order #{order.id?.slice(0, 8) || '--'}</h4>
              <p className="text-sm text-white/20 mb-6 font-light">{order.shipping_address || 'Delivery address pending'}</p>
              <div className="space-y-3 mb-6">
                {order.items && order.items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm border-b border-white/[0.03] pb-2 last:border-0">
                    <span className="text-white/40 font-light">Item x{item.quantity}</span>
                    <span className="text-white/80 font-medium">${(parseFloat(item.unit_price || 0) * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="pt-5 border-t border-white/[0.05] flex items-center justify-between">
                <span className="text-[11px] text-white/15 tracking-wide">{new Date(order.created_at || Date.now()).toLocaleString()}</span>
                <span className="text-2xl font-serif text-gradient-gold">${parseFloat(order.total_amount || 0).toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Incident Simulation */}
      <div id="incidents" className="mt-24 p-10 rounded-[32px] glass border border-white/[0.05]">
        <div className="flex items-center gap-3 mb-3">
          <Heart size={18} className="text-coral fill-coral" />
          <h3 className="text-3xl font-serif font-light text-white">Incident Simulation</h3>
        </div>
        <p className="text-white/20 mb-10 font-light">Trigger controlled failures to observe our AI agent layer detect, classify, and remediate issues automatically.</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { title: 'Payment CrashLoopBackOff', desc: 'Simulate payment pod crash and observe AI agent selecting RB-001 restart.', tag: 'RB-001' },
            { title: 'Failed Deployment', desc: 'Deploy broken image. AI detects deployment failure and executes rollback (RB-002).', tag: 'RB-002' },
            { title: 'Queue Backlog', desc: 'Back up message queue. Agent scales consumers automatically (RB-003 / RB-006).', tag: 'RB-003' },
            { title: 'High CPU', desc: 'Load spike triggers HPA scale-up via automated runbook (RB-003).', tag: 'RB-003' },
            { title: 'DB Connectivity', desc: 'Connection pool failure. Agent executes database recovery (RB-005).', tag: 'RB-005' },
            { title: 'Config Error', desc: 'Misconfigured ConfigMap. Agent patches and restarts deployment (RB-006).', tag: 'RB-006' },
          ].map(s => (
            <button key={s.title} onClick={() => alert(`Simulating: ${s.title}\nRunbook: ${s.tag}\n\nThis injects a controlled failure and triggers the AI agent pipeline.`)}
              className="text-left p-6 rounded-[24px] glass glass-hover transition-all duration-300 group">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-extrabold text-gold tracking-widest">{s.tag}</span>
                <ArrowRight size={14} className="text-white/20 group-hover:text-gold transition-colors" />
              </div>
              <h4 className="font-serif text-lg text-white mb-2 group-hover:text-gold transition-colors">{s.title}</h4>
              <p className="text-sm text-white/30 font-light leading-relaxed">{s.desc}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Footer - Premium                                                      */
/* ------------------------------------------------------------------ */
function Footer() {
  return (
    <footer className="border-t border-white/[0.04] bg-ink/80 backdrop-blur-xl mt-auto">
      <div className="max-w-6xl mx-auto px-6 py-14 flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-gold to-coral flex items-center justify-center shadow-xl shadow-gold/20">
            <Sparkle size={20} strokeWidth={2.5} className="text-ink" />
          </div>
          <div>
            <span className="font-serif font-bold text-xl text-white tracking-tight block">Aura<span className="text-gradient-gold">Commerce</span></span>
            <span className="text-[10px] text-white/15 tracking-[0.2em] uppercase">Luxury Microservices Platform</span>
          </div>
        </div>
        <div className="text-sm text-white/20 font-light">Microservices &bull; FastAPI &bull; React &bull; Kubernetes &bull; Event-Driven &bull; AI Agents</div>
        <div className="text-xs text-white/10">Built for Enterprise Architecture Review</div>
      </div>
    </footer>
  );
}

function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const userId = user ? user.user_id : DEMO_USER;

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await API.notifications(userId);
      setNotifications(data || []);
    } catch (e) {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { loadNotifications(); }, [loadNotifications]);

  return (
    <div className="max-w-4xl mx-auto px-6 pt-28 pb-20">
      <h2 className="text-4xl md:text-5xl font-serif font-light text-white mb-3">Your <span className="italic text-gradient-gold">Notifications</span></h2>
      <p className="text-white/20 mb-14 font-light">Real-time event-driven updates from the AuraCommerce platform.</p>
      {loading ? (
        <div className="grid gap-4">{[1, 2, 3].map(i => <div key={i} className="h-[120px] rounded-[24px] glass animate-pulse" />)}</div>
      ) : notifications.length === 0 ? (
        <div className="glass rounded-[32px] p-16 text-center">
          <Zap size={48} className="mx-auto text-white/10 mb-6" />
          <h3 className="text-2xl font-serif text-white mb-3">No notifications</h3>
          <p className="text-white/20 mb-8">Event-driven messages will appear here when triggered.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map(n => (
            <div key={n.id} className="glass rounded-[24px] p-6 glass-hover transition-all duration-300">
              <div className="flex items-start justify-between gap-6">
                <div>
                  <h4 className="font-serif text-xl text-white mb-2">{n.subject || 'AuraCommerce Alert'}</h4>
                  <p className="text-sm text-white/30 font-light mb-4">{n.message || 'No message content.'}</p>
                  <div className="flex gap-3 text-[11px] text-white/15 tracking-wide">
                    <span>Channel: {n.channel || 'email'}</span>
                    <span>Event: {n.event_reference || 'N/A'}</span>
                  </div>
                </div>
                <span className="text-xs text-white/10 font-mono shrink-0">{n.created_at ? new Date(n.created_at).toLocaleString() : '--'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main App                                                             */
/* ------------------------------------------------------------------ */
function MainApp() {
  const [cartCount, setCartCount] = useState(0);
  const { user } = useAuth();
  const userId = user ? user.user_id : DEMO_USER;

  const refreshCartCount = useCallback(async () => {
    try {
      const data = await API.cart(userId);
      const count = (data.items || []).reduce((sum, i) => sum + (i.quantity || 1), 0);
      setCartCount(count);
    } catch (e) { setCartCount(0); }
  }, [userId]);

  useEffect(() => { refreshCartCount(); }, [refreshCartCount]);

  const handleAddToCart = async (product) => {
    try {
      await API.addToCart(userId, product.id || product.sku, 1);
      await refreshCartCount();
    } catch (e) { await refreshCartCount(); }
  };

  return (
    <div className="min-h-screen flex flex-col bg-ink text-white font-sans selection:bg-gold/25">
      <Header cartCount={cartCount} />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<><Hero /><ProductsPage onAddToCart={handleAddToCart} /></>} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
