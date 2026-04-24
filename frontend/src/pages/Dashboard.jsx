import { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';

const Dashboard = () => {
  const [stocks, setStocks] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState(null);

  const fetchStocks = async () => {
    try {
      const response = await fetch('/api/stocks');
      const data = await response.json();
      setStocks(data.slice(0, 50)); // Show top 50
    } catch (error) {
      console.error('Error fetching stocks:', error);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_size: 100 }),
      });
      const data = await response.json();
      setProgress(data);
      await fetchStocks();
    } catch (error) {
      console.error('Error syncing:', error);
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            MAFAR Analytics Dashboard
          </h1>
          <p className="text-gray-400 mt-2">13,000+ stocks with real-time pricing</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg hover:from-cyan-600 hover:to-blue-700 disabled:opacity-50 transition-all"
        >
          <RefreshCw className={syncing ? 'animate-spin' : ''} size={20} />
          {syncing ? 'Syncing...' : 'Sync Prices'}
        </button>
      </div>

      {progress && (
        <div className="mb-6 p-4 bg-slate-800 rounded-lg border border-slate-700">
          <p className="text-sm text-gray-300">
            Processed: {progress.processed}/{progress.total} | Success: {progress.success} | Failed: {progress.failed}
          </p>
        </div>
      )}

      <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-800 border-b border-slate-700">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Symbol</th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Price</th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Change</th>
              <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Market Cap</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {stocks.map((stock) => (
              <tr key={stock.ISIN} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-6 py-4 font-mono text-sm text-cyan-400">{stock.Ticker}</td>
                <td className="px-6 py-4 text-sm">{stock.Name}</td>
                <td className="px-6 py-4 text-sm font-medium">
                  {stock.current_price ? `$${stock.current_price.toFixed(2)}` : '-'}
                </td>
                <td className="px-6 py-4 text-sm">
                  {stock.day_change_pct && (
                    <span className={`flex items-center gap-1 ${stock.day_change_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stock.day_change_pct > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      {Math.abs(stock.day_change_pct).toFixed(2)}%
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-gray-400">
                  {stock.market_cap ? `$${(stock.market_cap / 1e9).toFixed(2)}B` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
