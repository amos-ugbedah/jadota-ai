import React from 'react';

const SYMBOLS = [
  { symbol: 'BTC/USDT', label: 'BTC' },
  { symbol: 'ETH/USDT', label: 'ETH' },
  { symbol: 'SOL/USDT', label: 'SOL' },
  { symbol: 'BNB/USDT', label: 'BNB' },
  { symbol: 'XRP/USDT', label: 'XRP' },
  { symbol: 'DOGE/USDT', label: 'DOGE' },
  { symbol: 'ADA/USDT', label: 'ADA' },
];

const TIMEFRAMES = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
];

export interface ChartOverlayState {
  sma20: boolean;
  sma50: boolean;
  ema12: boolean;
  ema26: boolean;
  bollingerBands: boolean;
}

export interface ChartToolbarProps {
  symbol: string;
  interval: string;
  onSymbolChange: (s: string) => void;
  onIntervalChange: (i: string) => void;
  overlays: ChartOverlayState;
  onToggleOverlay: (key: keyof ChartOverlayState) => void;
  showRSI: boolean;
  showMACD: boolean;
  onToggleRSI: () => void;
  onToggleMACD: () => void;
}

const OVERLAY_BUTTONS: {
  key: keyof ChartOverlayState;
  label: string;
  color: string;
}[] = [
  { key: 'sma20', label: 'SMA 20', color: '#3b82f6' },
  { key: 'sma50', label: 'SMA 50', color: '#a855f7' },
  { key: 'ema12', label: 'EMA 12', color: '#fbbf24' },
  { key: 'ema26', label: 'EMA 26', color: '#f97316' },
  { key: 'bollingerBands', label: 'BB', color: '#94a3b8' },
];

export const ChartToolbar: React.FC<ChartToolbarProps> = ({
  symbol,
  interval,
  onSymbolChange,
  onIntervalChange,
  overlays,
  onToggleOverlay,
  showRSI,
  showMACD,
  onToggleRSI,
  onToggleMACD,
}) => {
  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-4 space-y-4">
      {/* Symbols */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-2 text-xs tracking-wider text-gray-500 uppercase">
          Symbol
        </span>
        {SYMBOLS.map((s) => {
          const active = symbol === s.symbol;
          return (
            <button
              key={s.symbol}
              onClick={() => onSymbolChange(s.symbol)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition border ${
                active
                  ? 'bg-[#6366f1] text-white border-[#6366f1]'
                  : 'bg-[#0a0a1a] text-gray-300 border-[#2a2a4a] hover:border-[#3a3a5a] hover:text-white'
              }`}
            >
              {s.label}
            </button>
          );
        })}
      </div>

      {/* Timeframes + Indicators */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="mr-2 text-xs tracking-wider text-gray-500 uppercase">
            Timeframe
          </span>
          <div className="inline-flex bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg p-1">
            {TIMEFRAMES.map((tf) => {
              const active = interval === tf.value;
              return (
                <button
                  key={tf.value}
                  onClick={() => onIntervalChange(tf.value)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
                    active
                      ? 'bg-[#6366f1] text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tf.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-2 text-xs tracking-wider text-gray-500 uppercase">
            Indicators
          </span>

          {OVERLAY_BUTTONS.map((b) => (
            <ToggleButton
              key={b.key}
              active={overlays[b.key]}
              onClick={() => onToggleOverlay(b.key)}
              label={b.label}
              color={b.color}
            />
          ))}

          <ToggleButton
            active={showRSI}
            onClick={onToggleRSI}
            label="RSI"
            color="#6366f1"
          />
          <ToggleButton
            active={showMACD}
            onClick={onToggleMACD}
            label="MACD"
            color="#fbbf24"
          />
        </div>
      </div>
    </div>
  );
};

const ToggleButton: React.FC<{
  active: boolean;
  onClick: () => void;
  label: string;
  color: string;
}> = ({ active, onClick, label, color }) => (
  <button
    onClick={onClick}
    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition border flex items-center gap-1.5 ${
      active
        ? 'bg-[#0a0a1a] border-[#2a2a4a] text-white'
        : 'bg-transparent border-[#2a2a4a] text-gray-500 hover:text-gray-300'
    }`}
  >
    <span
      className="w-2 h-2 rounded-full"
      style={{ background: active ? color : '#4b5563' }}
    />
    {label}
  </button>
);

export default ChartToolbar;