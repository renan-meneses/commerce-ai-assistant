import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { token, logout } = useAuth();

  return (
    <>
      <nav className="nav">
        <span className="brand">Commerce AI</span>
        <NavLink to="/">Catalog</NavLink>
        <NavLink to="/cart">Cart</NavLink>
        {token ? (
          <>
            <NavLink to="/orders">Orders</NavLink>
            <button className="btn" onClick={logout}>
              Logout
            </button>
          </>
        ) : (
          <NavLink to="/login">Login</NavLink>
        )}
      </nav>
      <main className="container">
        <Outlet />
      </main>
    </>
  );
}
