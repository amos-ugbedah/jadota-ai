import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  BarChart3, TrendingUp, TrendingDown, Activity,
  Target, Award, Percent, Shield, Loader2,
  RefreshCw, AlertCircle, FlaskConical, DollarSign, LineChart as LineChartIcon,
} from 'lucide-react';
import {
  createChart, ColorType, LineStyle,
  type IChartApi, type ISeriesApi, type UTCTimestamp,
} from 'lightweight-charts';
import { toast } from 'react-hot-toast';
import apiClient from '@/api/client';
import analyticsApi, {
  type SummaryStats, type EquityCurve, type Drawdown,
  type WinLoss, type BySymbol, type MonthlyHeatmap,
  type Ratios, type TradeJournal,
} from '@/api/analytics';

// ============================================
// Page
// ============================================
const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [equity, setEquity] = useState<EquityCurve | null>(null);
  const [drawdown, setDrawdown] = useState<Drawdown | null>(null);
  const [winLoss, setWinLoss] = useState<WinLoss | null>(null);
  const [bySymbol, setBySymbol] = useState<BySymbol | null>(null);
  const [heatmap, setHeatmap] = useState<MonthlyHeatmap | null>(null);
  const [ratios, setRatios] = useState<Ratios | null>(null);
  const [journal, setJournal] = useState<TradeJournal | null>(null);
  const [seedKey, setSeedKey] = useState('');
  const [seeding, setSeeding] = useState(false);

  const loadAll = async (silent = false) => {
    if (!silent) setLoading(true); else setRefreshing(true);
    try {
      const [s, e, d, wl, bs, hm, r, j] = await Promise.all([
        analyticsApi.getSummary(),
        analyticsApi.getEquityCurve(days),
        analyticsApi.getDrawdown(days),
        analyticsApi.getWinLoss(),
        analyticsApi.getBySymbol(),
        analyticsApi.getMonthlyHeatmap(6),
        analyticsApi.getRatios(days),
        analyticsApi.getTradeJournal({ limit: 100 }),
      ]);
      setSummary(s);
      setEquity(e);
      setDrawdown(d);
      setWinLoss(wl);
      setBySymbol(bs);
      setHeatmap(hm);
      setRatios(r);
      setJournal(j);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const handleSeed = async () => {
    if (!seedKey) {
      toast.error('Enter your ADMIN_BOOTSTRAP_KEY to seed demo data');
      return;
    }
    setSeeding(true);
    try {
      const res = await analyticsApi.seedDemoData(seedKey, 80);
      toast.success(`Generated ${res.generated} demo trades — reloading...`);
      await loadAll(true);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to seed data');
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const isEmpty = (summary?.closed_positions || 0) === 0 && (summary?.open_positions || 0) === 0;

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-white">
            <BarChart3 className="w-8 h-8 text-[#6366f1]" />
            Advanced Analytics
          </h1>
          <p className="mt-1 text-gray-400">
            Performance breakdown, risk metrics, and trade insights
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg p-1">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  days === d ? 'bg-[#6366f1] text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                {d}D
              </button>
            ))}
          </div>
          <button
            onClick={() => loadAll(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-gray-300 hover:text-white hover:border-[#3a3a5a] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Empty state with seed tool */}
      {isEmpty && (
        <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-8">
          <div className="flex items-start gap-4">
            <FlaskConical className="w-8 h-8 text-[#6366f1] flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="mb-1 font-semibold text-white">No trades yet</h3>
              <p className="mb-4 text-sm text-gray-400">
                Analytics needs trade data. Open some demo trades via AI Auto-Trade,
                or generate demo data below to preview the dashboard.
              </p>
              <div className="flex gap-2">
                <input
                  type="password"
                  placeholder="Admin bootstrap key"
                  value={seedKey}
                  onChange={(e) => setSeedKey(e.target.value)}
                  className="px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white text-sm flex-1 max-w-xs focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                />
                <button
                  onClick={handleSeed}
                  disabled={seeding}
                  className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                  Generate 80 demo trades
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top stat cards */}
      {summary && <SummaryCards stats={summary} />}

      {/* Ratios row */}
      {ratios && <RatiosRow ratios={ratios} />}

      {/* Equity curve */}
      {equity && <EquityChart equity={equity} days={days} />}

      {/* Drawdown */}
      {drawdown && <DrawdownChart drawdown={drawdown} />}

      {/* Two-column: Win/Loss + By Symbol */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {winLoss && <WinLossChart data={winLoss} />}
        {bySymbol && <BySymbolTable data={bySymbol} />}
      </div>

      {/* Monthly heatmap */}
      {heatmap && <MonthlyHeatmapView data={heatmap} />}

      {/* Trade journal */}
      {journal && <TradeJournalTable data={journal} />}
    </div>
  );
};

// ============================================
// Summary cards
// ============================================
const SummaryCards: React.FC<{ stats: SummaryStats }> = ({ stats }) => {
  const pnl = stats.total_pnl;
  const positive = pnl >= 0;

  const cards = [
    {
      label: 'Total P&L',
      value: `$${pnl.toFixed(2)}`,
      icon: <DollarSign className="w-5 h-5" />,
      tone: positive ? 'positive' : 'negative',
    },
    {
      label: 'Win Rate',
      value: `${stats.win_rate.toFixed(1)}%`,
      icon: <Target className="w-5 h-5" />,
      tone: stats.win_rate >= 50 ? 'positive' : 'negative',
    },
    {
      label: 'Profit Factor',
      value: stats.profit_factor.toFixed(2),
      icon: <Percent className="w-5 h-5" />,
      tone: stats.profit_factor >= 1 ? 'positive' : 'negative',
    },
    {
      label: 'Avg Win / Loss',
      value: `$${stats.avg_win.toFixed(2)} / $${stats.avg_loss.toFixed(2)}`,
      icon: <Activity className="w-5 h-5" />,
      tone: stats.avg_win + stats.avg_loss > 0 ? 'positive' : 'negative',
    },
    {
      label: 'Best Trade',
      value: `+$${stats.best_trade.toFixed(2)}`,
      icon: <Award className="w-5 h-5" />,
      tone: 'positive',
    },
    {
      label: 'Worst Trade',
      value: `$${stats.worst_trade.toFixed(2)}`,
      icon: <TrendingDown className="w-5 h-5" />,
      tone: 'negative',
    },
    {
      label: 'Win Streak',
      value: `${stats.max_win_streak}`,
      icon: <TrendingUp className="w-5 h-5" />,
      tone: 'positive',
    },
    {
      label: 'Loss Streak',
      value: `${stats.max_loss_streak}`,
      icon: <Shield className="w-5 h-5" />,
      tone: 'negative',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs tracking-wider text-gray-400 uppercase">{c.label}</span>
            <div className="p-1.5 bg-[#6366f1]/10 rounded-lg text-[#6366f1]">{c.icon}</div>
          </div>
          <p className={`text-xl font-bold ${
            c.tone === 'positive' ? 'text-green-400' :
            c.tone === 'negative' ? 'text-red-400' : 'text-white'
          }`}>
            {c.value}
          </p>
        </div>
      ))}
    </div>
  );
};

// ============================================
// Ratios row
// ============================================
const RatiosRow: React.FC<{ ratios: Ratios }> = ({ ratios }) => {
  const items = [
    { label: 'Sharpe Ratio', value: ratios.sharpe.toFixed(2), note: 'Risk-adjusted return' },
    { label: 'Sortino Ratio', value: ratios.sortino.toFixed(2), note: 'Downside-adjusted' },
    { label: 'Calmar Ratio', value: ratios.calmar.toFixed(2), note: 'Return / Max DD' },
    { label: 'Max Drawdown', value: `${ratios.max_drawdown_pct.toFixed(2)}%`, note: 'Peak to trough' },
    { label: 'Volatility (Ann.)', value: `${ratios.volatility_annual_pct.toFixed(1)}%`, note: 'Std dev of returns' },
    { label: 'Total Return', value: `${ratios.total_return_pct.toFixed(2)}%`, note: `${ratios.sample_days} days` },
  ];

  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-4">
      <h3 className="mb-3 text-sm font-semibold tracking-wider text-white uppercase">
        Risk-Adjusted Metrics
      </h3>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {items.map((it) => (
          <div key={it.label} className="text-center">
            <div className="text-xl font-bold text-[#6366f1]">{it.value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{it.label}</div>
            <div className="text-[10px] text-gray-600 mt-0.5">{it.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================
// Equity chart (lightweight-charts)
// ============================================
const EquityChart: React.FC<{ equity: EquityCurve; days: number }> = ({ equity }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 320,
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a1a' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: 'rgba(42,42,74,0.35)' },
        horzLines: { color: 'rgba(42,42,74,0.35)' },
      },
      rightPriceScale: { borderColor: '#2a2a4a' },
      timeScale: { borderColor: '#2a2a4a', timeVisible: false },
    });
    const series = chart.addAreaSeries({
      lineColor: '#6366f1',
      topColor: 'rgba(99,102,241,0.4)',
      bottomColor: 'rgba(99,102,241,0.02)',
      lineWidth: 2,
      priceLineVisible: false,
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width);
        if (w > 0) chart.applyOptions({ width: w });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = equity.points
      .map((p) => ({
        time: Math.floor(new Date(p.time + 'T00:00:00Z').getTime() / 1000) as UTCTimestamp,
        value: p.value,
      }))
      .sort((a, b) => a.time - b.time);
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [equity]);

  const positive = equity.total_return_pct >= 0;

  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold tracking-wider text-white uppercase">
          <LineChartIcon className="w-4 h-4 text-[#6366f1]" />
          Equity Curve
        </h3>
        <div className="flex items-baseline gap-3">
          <span className="text-2xl font-bold text-white">${equity.final_balance.toLocaleString()}</span>
          <span className={`text-sm font-semibold ${positive ? 'text-green-400' : 'text-red-400'}`}>
            {positive ? '+' : ''}{equity.total_return_pct.toFixed(2)}%
          </span>
        </div>
      </div>
      <div ref={containerRef} className="w-full overflow-hidden rounded-lg" />
    </div>
  );
};

// ============================================
// Drawdown chart
// ============================================
const DrawdownChart: React.FC<{ drawdown: Drawdown }> = ({ drawdown }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 200,
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a1a' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: 'rgba(42,42,74,0.35)' },
        horzLines: { color: 'rgba(42,42,74,0.35)' },
      },
      rightPriceScale: { borderColor: '#2a2a4a' },
      timeScale: { borderColor: '#2a2a4a' },
    });
    const series = chart.addAreaSeries({
      lineColor: '#ef4444',
      topColor: 'rgba(239,68,68,0.02)',
      bottomColor: 'rgba(239,68,68,0.4)',
      lineWidth: 2,
      priceLineVisible: false,
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width);
        if (w > 0) chart.applyOptions({ width: w });
      }
    });
    ro.observe(containerRef.current);
    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = drawdown.points
      .map((p) => ({
        time: Math.floor(new Date(p.time + 'T00:00:00Z').getTime() / 1000) as UTCTimestamp,
        value: p.value,
      }))
      .sort((a, b) => a.time - b.time);
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [drawdown]);

  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold tracking-wider text-white uppercase">
          <TrendingDown className="w-4 h-4 text-red-400" />
          Drawdown
        </h3>
        <div className="text-right">
          <div className="text-lg font-bold text-red-400">{drawdown.max_drawdown_pct.toFixed(2)}%</div>
          <div className="text-xs text-gray-500">Max drawdown</div>
        </div>
      </div>
      <div ref={containerRef} className="w-full overflow-hidden rounded-lg" />
    </div>
  );
};

// ============================================
// Win/Loss histogram (custom SVG)
// ============================================
const WinLossChart: React.FC<{ data: WinLoss }> = ({ data }) => {
  const max = Math.max(1, ...data.buckets.map((b) => b.count));
  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold tracking-wider text-white uppercase">
          Win / Loss Distribution
        </h3>
        <div className="text-xs text-gray-500">
          {data.wins}W · {data.losses}L · {data.total} total
        </div>
      </div>
      <div className="space-y-3">
        {data.buckets.map((b) => {
          const pct = (b.count / max) * 100;
          return (
            <div key={b.label} className="flex items-center gap-3">
              <div className="text-xs text-right text-gray-400 w-28">{b.label}</div>
              <div className="flex-1 h-6 bg-[#0a0a1a] rounded overflow-hidden relative">
                <div
                  className={`h-full ${b.type === 'win' ? 'bg-green-500/60' : 'bg-red-500/60'}`}
                  style={{ width: `${pct}%` }}
                />
                <span className="absolute inset-0 flex items-center pl-2 text-xs font-medium text-white">
                  {b.count}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ============================================
// By-symbol table
// ============================================
const BySymbolTable: React.FC<{ data: BySymbol }> = ({ data }) => (
  <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
    <h3 className="mb-4 text-sm font-semibold tracking-wider text-white uppercase">
      Performance by Symbol
    </h3>
    {data.symbols.length === 0 ? (
      <p className="py-8 text-sm text-center text-gray-500">No closed trades yet</p>
    ) : (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase border-b border-[#2a2a4a]">
              <th className="py-2 text-left">Symbol</th>
              <th className="py-2 text-right">Trades</th>
              <th className="py-2 text-right">Win %</th>
              <th className="py-2 text-right">P&L</th>
              <th className="py-2 text-right">Avg P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2a2a4a]">
            {data.symbols.map((s) => (
              <tr key={s.symbol} className="hover:bg-[#0a0a1a]">
                <td className="py-2.5 text-white font-medium">{s.symbol}</td>
                <td className="py-2.5 text-right text-gray-300">{s.trades}</td>
                <td className={`py-2.5 text-right font-medium ${s.win_rate >= 50 ? 'text-green-400' : 'text-yellow-400'}`}>
                  {s.win_rate.toFixed(1)}%
                </td>
                <td className={`py-2.5 text-right font-semibold ${s.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${s.pnl.toFixed(2)}
                </td>
                <td className={`py-2.5 text-right ${s.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${s.avg_pnl.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
);

// ============================================
// Monthly heatmap
// ============================================
const MonthlyHeatmapView: React.FC<{ data: MonthlyHeatmap }> = ({ data }) => {
  const values = data.months.map((m) => m.pnl);
  const maxAbs = Math.max(1, ...values.map((v) => Math.abs(v)));

  const getBg = (pnl: number) => {
    if (pnl === 0) return 'bg-[#0a0a1a] border-[#2a2a4a]';
    const intensity = Math.min(1, Math.abs(pnl) / maxAbs);
    if (pnl > 0) return `bg-green-500/${Math.round(10 + intensity * 50)} border-green-500/40`;
    return `bg-red-500/${Math.round(10 + intensity * 50)} border-red-500/40`;
  };

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
      <h3 className="mb-4 text-sm font-semibold tracking-wider text-white uppercase">
        Monthly P&L Heatmap
      </h3>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
        {data.months.map((m) => (
          <div
            key={m.label}
            className={`rounded-lg border p-3 text-center transition hover:scale-105 ${getBg(m.pnl)}`}
            title={`${m.trades} trades · ${m.win_rate.toFixed(0)}% win rate`}
          >
            <div className="text-xs text-gray-400">{monthNames[m.month - 1]} {String(m.year).slice(2)}</div>
            <div className={`text-lg font-bold mt-1 ${m.pnl >= 0 ? 'text-green-300' : 'text-red-300'}`}>
              {m.pnl >= 0 ? '+' : ''}{m.pnl.toFixed(0)}
            </div>
            <div className="text-[10px] text-gray-500 mt-0.5">{m.trades}t · {m.win_rate.toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================
// Trade journal
// ============================================
const TradeJournalTable: React.FC<{ data: TradeJournal }> = ({ data }) => (
  <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
    <h3 className="flex items-center justify-between mb-4 text-sm font-semibold tracking-wider text-white uppercase">
      <span>Trade Journal</span>
      <span className="text-xs font-normal text-gray-500">Last {data.count} trades</span>
    </h3>
    {data.trades.length === 0 ? (
      <p className="py-8 text-sm text-center text-gray-500">No trades yet</p>
    ) : (
      <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#1a1a2e] z-10">
            <tr className="text-xs text-gray-500 uppercase border-b border-[#2a2a4a]">
              <th className="py-2 text-left">Symbol</th>
              <th className="py-2 text-left">Side</th>
              <th className="py-2 text-right">Entry</th>
              <th className="py-2 text-right">Exit</th>
              <th className="py-2 text-right">P&L</th>
              <th className="py-2 text-right">Conf</th>
              <th className="py-2 text-right">Status</th>
              <th className="py-2 pl-4 text-left">Opened</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2a2a4a]">
            {data.trades.map((t) => (
              <tr key={t.id} className="hover:bg-[#0a0a1a]">
                <td className="py-2 font-medium text-white">{t.symbol}</td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.side === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {t.side}
                  </span>
                </td>
                <td className="py-2 text-right text-gray-300">${t.entryPrice.toFixed(2)}</td>
                <td className="py-2 text-right text-gray-300">
                  {t.status === 'CLOSED' ? `$${t.currentPrice.toFixed(2)}` : '—'}
                </td>
                <td className={`py-2 text-right font-semibold ${
                  (t.realizedPnl || t.unrealizedPnl) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${(t.realizedPnl || t.unrealizedPnl).toFixed(2)}
                </td>
                <td className="py-2 text-right text-gray-400">{t.aiConfidence}%</td>
                <td className="py-2 text-right">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.status === 'OPEN' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {t.status}
                  </span>
                </td>
                <td className="py-2 pl-4 text-xs text-gray-500">
                  {t.openedAt ? new Date(t.openedAt).toLocaleString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
);

export default Analytics;