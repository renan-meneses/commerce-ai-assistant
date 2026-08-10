import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await register(name, email, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: '0 auto' }}>
      <h1>Create account</h1>
      <form onSubmit={submit} style={{ display: 'grid', gap: '0.75rem' }}>
        <input
          className="input"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="input"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="input"
          type="password"
          placeholder="Password (min 8 chars)"
          value={password}
          minLength={8}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="muted">{error}</p>}
        <button className="btn btn-primary" type="submit">
          Register
        </button>
      </form>
      <p>
        <Link to="/login">Already have an account?</Link>
      </p>
    </div>
  );
}
