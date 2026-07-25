const getHeaders = () => {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('auth_token');
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
};

const API = {
  products: async (search = '', category = '', page = 1) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    params.append('page', String(page));
    const res = await fetch(`/api/products?${params}`);
    if (!res.ok) throw new Error('Failed to fetch products');
    return res.json();
  },
  product: async (id) => {
    const res = await fetch(`/api/products/${id}`);
    return res.json();
  },
  categories: async () => {
    const res = await fetch(`/api/categories`);
    return res.json();
  },
  cart: async (userId = 'demo-user') => {
    const res = await fetch(`/cart/${userId}`);
    return res.json();
  },
  addToCart: async (userId, productId, quantity = 1) => {
    const res = await fetch(`/cart/${userId}/items`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ product_id: productId, quantity })
    });
    return res.json();
  },
  removeCartItem: async (userId, itemId) => {
    const res = await fetch(`/cart/${userId}/items/${itemId}`, { method: 'DELETE' });
    return res.status === 204 ? true : false;
  },
  clearCart: async (userId) => {
    const res = await fetch(`/cart/${userId}`, { method: 'DELETE' });
    return res.status === 204;
  },
  orders: async (userId = 'demo-user') => {
    const res = await fetch(`/orders/user/${userId}`);
    return res.json();
  },
  createOrder: async (userId, items, shippingAddress = '') => {
    const orderItems = items.map(i => ({
      product_id: i.product_id,
      quantity: i.quantity,
      unit_price: parseFloat(i.product_price || 25.99)
    }));
    const res = await fetch(`/orders`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        user_id: userId,
        shipping_address: shippingAddress,
        items: orderItems
      })
    });
    return res.json();
  },
  order: async (id) => {
    const res = await fetch(`/orders/${id}`);
    return res.json();
  },
  notifications: async (userId = 'demo-user') => {
    try {
      const res = await fetch(`/notifications/user/${userId}`);
      return res.json();
    } catch (e) {
      return [];
    }
  },
  sendNotification: async (userId, message, channel = 'email', subject = 'AuraCommerce Alert') => {
    const res = await fetch(`/notifications/send`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ user_id: userId, message, channel, subject })
    });
    return res.json();
  }
};

export default API;
