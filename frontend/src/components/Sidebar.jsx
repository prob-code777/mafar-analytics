import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, BriefcaseIcon, Filter, BarChart2, Settings, ChevronLeft, ChevronRight } from 'lucide-react';

const Sidebar = ({ open, setOpen }) => {
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Portfolios', path: '/portfolios', icon: BriefcaseIcon },
    { name: 'Screener', path: '/screener', icon: Filter },
    { name: 'Backtest', path: '/backtest', icon: BarChart2 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div
      className={`fixed left-0 top-0 h-screen bg-slate-900 border-r border-slate-800 transition-all duration-300 z-50 ${
        open ? 'w-64' : 'w-16'
      }`}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          {open && <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">MAFAR</h1>}
          <button
            onClick={() => setOpen(!open)}
            className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            {open ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-cyan-400'
                    : 'hover:bg-slate-800 text-gray-400 hover:text-gray-200'
                }`}
              >
                <Icon size={20} />
                {open && <span className="font-medium">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;
