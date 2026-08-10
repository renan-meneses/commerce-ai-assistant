import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import type { Inventory, Product } from '../api/types';

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (!id) return;
    api
      .getProduct(id)
      .then(setProduct)
      .catch((e) => setError(e instanceof Error ? e.message : 'Not found'));
    api.getInventory(id).then(setInventory).catch(() => undefined);
  }, [id]);

  const addToCart = async () => {
    if (!id) return;
    setAdding(true);
    try {
      await api.addCartItem(id, 1);
      setNotice('Added to cart.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add');
    } finally {
      setAdding(false);
    }
  };

  if (error) return <p>{error}</p>;
  if (!product) return <p>Loading…</p>;

  return (
    <div>
      <Link to="/" className="muted">
        ← Back to catalog
      </Link>
      <h1>{product.name}</h1>
      <p className="muted">
        {product.brand} · {product.category?.name} · SKU {product.sku}
      </p>
      <p>{product.description}</p>
      <p className="price">
        {(product.price_cents / 100).toLocaleString('pt-BR', {
          style: 'currency',
          currency: 'BRL',
        })}
      </p>
      <p>
        Availability:{' '}
        {inventory
          ? `${inventory.available} in stock`
          : 'unknown'}
      </p>
      <button className="btn btn-primary" onClick={addToCart} disabled={adding}>
        Add to cart
      </button>
      {notice && <p className="muted">{notice}</p>}
      <h3 style={{ marginTop: '2rem' }}>Specifications</h3>
      <table>
        <tbody>
          {Object.entries(product.specifications ?? {}).map(([key, value]) => (
            <tr key={key}>
              <td className="muted">{key}</td>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
