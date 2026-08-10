import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Product } from '../api/types';

function formatPrice(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

export default function Catalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listProducts({ page, limit: 12, search })
      .then((res) => {
        setProducts(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }, [page, search]);

  return (
    <div>
      <h1>Catalog</h1>
      <input
        className="input"
        style={{ maxWidth: 320, marginBottom: '1rem' }}
        placeholder="Search products…"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />
      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <div className="grid">
            {products.map((p) => (
              <Link key={p.id} to={`/products/${p.id}`} className="card">
                <h3>{p.name}</h3>
                <div className="muted">
                  {p.brand} · {p.category?.name}
                </div>
                <div className="price">{formatPrice(p.price_cents)}</div>
              </Link>
            ))}
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
            <button
              className="btn"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>
              Page {page} of {Math.max(1, Math.ceil(total / 12))}
            </span>
            <button
              className="btn"
              disabled={page >= Math.ceil(total / 12)}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
