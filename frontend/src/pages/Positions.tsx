import React from 'react';

const Positions: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-6">Positions</h1>
      <div className="bg-jadota-card p-8 rounded-xl border border-jadota-border text-center">
        <p className="text-gray-400">No open positions</p>
      </div>
    </div>
  );
};

export default Positions;