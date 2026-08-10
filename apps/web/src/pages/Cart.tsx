import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { Cart } from '../api/types';

export default function CartPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.getCart().then(setCart).catch((e) => setError(e.message));
  }, [token]);

  useEffect(load, [load]);

  if (!token) {
    return (
      <p>
        <Link to="/login">Login</Link> to view your cart.
      </p>
    );
  }
  if (!cart) return <p>{error ?? 'Loading…'}</p>;

  const update = (productId: string, quantity: number) => {
    if (quantity < 1) {
      api.removeCartItem(productId).then(setCart);
    } else {
      api.updateCartItem(productId, quantity).then(setCart);
    }
  };

  const checkout = async () => {
    try {
      const order = await api.checkout();
      navigate(`/orders`);
      alert(`Order ${order.number} created.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Checkout failed');
    }
  };

  return (
    <div>
      <h1>Cart</h1>
      {error && <p className="muted">{error}</p>}
      {cart.items.length === 0 ? (
        <p>
          Your cart is empty. <Link to="/">Browse the catalog</Link>.
        </p>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Unit price</th>
                <th>Qty</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
                <tr key={item.productId}>
                  <td>
                    <Link to={`/products/${item.productId}`}>{item.product.name}</Link>
                  </td>
                  <td>
                    {(item.product.price_cents / 100).toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </td>
                  <td>
                    <button
                      className="btn"
                      onClick={() => update(item.productId, item.quantity - 1)}
                    >
                      −
                    </button>{' '}
                    {item.quantity}{' '}
                    <button
                      className="btn"
                      onClick={() => update(item.productId, item.quantity + 1)}
                    >
                      +
                    </button>
                  </td>
                  <td>
                    {(item.product.price_cents * item.quantity / 100).toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </td>
                  <td>
                    <button
                      className="btn"
                      onClick={() => api.removeCartItem(item.productId).then(setCart)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="price">
            Total:{' '}
            {(cart.totalCents / 100).toLocaleString('pt-BR', {
              style: 'currency',
              currency: 'BRL',
            })}
          </p>
          <button className="btn btn-primary" onClick={checkout}>
            Checkout
          </button>
        </>
      )}
    </div>
  );
}
