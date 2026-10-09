import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { useAuthStore } from '../store/authStore';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/market', label: 'Market Explorer' },
  { to: '/strategy-lab', label: 'Strategy Lab' },
  { to: '/history', label: 'Backtest History' },
  { to: '/compare', label: 'Strategy Comparison' },
  { to: '/risk', label: 'Risk Analysis' },
];

export default function Sidebar() {
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="w-56 shrink-0 border-r border-terminal-border bg-terminal-panel flex flex-col">
      <div className="p-4 border-b border-terminal-border">
        <div className="text-terminal-accent font-bold text-lg tracking-tight">QuantX</div>
        <div className="text-[10px] text-terminal-muted uppercase tracking-wider">
          Research &amp; Simulation
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              clsx(
                'block px-3 py-2 rounded-md text-sm transition',
                isActive
                  ? 'bg-terminal-accent/10 text-terminal-accent border border-terminal-accent/40'
                  : 'text-slate-300 hover:bg-white/5'
              )
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-terminal-border">
        <button onClick={logout} className="btn-secondary w-full text-xs">
          Sign out
        </button>
        <p className="text-[10px] text-terminal-muted mt-3 leading-snug">
          Simulation only. No real trades are executed. Not investment advice.
        </p>
      </div>
    </aside>
  );
}
