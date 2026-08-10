import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { Order } from '../api/types';

export default function Orders() {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getOrders()
      .then(setOrders)
      .catch((e) => setError(e.message));
  }, [token]);

  if (!token) {
    return (
      <p>
        <Link to="/login">Login</Link> to view your orders.
      </p>
    );
  }
  if (!orders) return <p>{error ?? 'Loading…'}</p>;

  return (
    <div>
      <h1>My Orders</h1>
      {orders.length === 0 && <p>No orders yet.</p>}
      {orders.map((order) => (
        <div key={order.id} className="card" style={{ marginBottom: '1rem' }}>
          <div>
            <strong>{order.number}</strong>{' '}
            <span className="muted">
              {order.status} ·{' '}
              {new Date(order.createdAt).toLocaleString('pt-BR')}
            </span>
          </div>
          <div className="muted">
            {order.items.map((i) => `${i.quantity}× ${i.productId.slice(0, 8)}`).join(', ')}
          </div>
          <div className="price">
            {(order.totalCents / 100).toLocaleString('pt-BR', {
              style: 'currency',
              currency: 'BRL',
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
