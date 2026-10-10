import React from 'react';

interface Props {
  source?: string;
  /** Optional: controls badge size. Defaults to "sm". */
  size?: 'sm' | 'md';
}

/**
 * Small badge showing whether a position is simulated (demo) or
 * backed by a real Bitget order (live).
 *
 * Reads `position.source` from the backend:
 *   "demo"   → grey badge
 *   "bitget" → red badge with a pulsing dot
 *
 * If `source` is missing (old data before Task #4a-2), defaults to DEMO.
 */
const PositionSourceBadge: React.FC<Props> = ({ source, size = 'sm' }) => {
  const isLive = source === 'bitget';

  const padding = size === 'md' ? 'px-2.5 py-1 text-xs' : 'px-2 py-0.5 text-[10px]';

  if (isLive) {
    return (
      <span
        className={`inline-flex items-center gap-1 ${padding} font-bold rounded-full bg-red-500/20 text-red-400 border border-red-500/40`}
        title="This position is backed by a real order on Bitget"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        LIVE
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center ${padding} font-bold rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30`}
      title="Simulated position — no real money involved"
    >
      DEMO
    </span>
  );
};

export default PositionSourceBadge;