import { NavLink, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand" style={{ textDecoration: 'none' }}>
        <div className="shield-icon">🛡</div>
        FraudShield
      </NavLink>

      <div className="navbar-links">
        <NavLink to="/"        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          end>Home</NavLink>
        <NavLink to="/analyze" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Analyze
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          History
        </NavLink>
      </div>

      <button className="nav-cta" onClick={() => navigate('/analyze')}>
        🔍 Start Analysis
      </button>
    </nav>
  )
}
