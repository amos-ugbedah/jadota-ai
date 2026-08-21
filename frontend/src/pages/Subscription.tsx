import React from 'react';

const Subscription: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-6">Subscription Plans</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PlanCard tier="Basic" price="Free" features={['Demo Trading', 'Basic AI Signals', 'Paper Trading']} />
        <PlanCard tier="Pro" price="$29/mo" features={['Live Trading', 'Advanced AI', 'Risk Management', 'Priority Support']} popular />
        <PlanCard tier="Enterprise" price="$99/mo" features={['All Pro Features', 'Multiple Exchanges', 'Custom Strategies', 'Dedicated Support']} />
      </div>
    </div>
  );
};

const PlanCard: React.FC<{ tier: string; price: string; features: string[]; popular?: boolean }> = 
  ({ tier, price, features, popular }) => (
    <div className={`bg-jadota-card p-6 rounded-xl border ${popular ? 'border-primary-500' : 'border-jadota-border'} relative`}>
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-500 text-white text-xs px-3 py-1 rounded-full">
          Most Popular
        </span>
      )}
      <h3 className="text-xl font-bold text-white">{tier}</h3>
      <p className="text-2xl font-bold text-primary-400 my-2">{price}</p>
      <ul className="space-y-2 mb-6">
        {features.map((feature, i) => (
          <li key={i} className="text-gray-400 text-sm flex items-center gap-2">
            <span className="text-green-400">✓</span> {feature}
          </li>
        ))}
      </ul>
      <button className="w-full py-2 bg-primary-500 text-white rounded-lg font-semibold hover:bg-primary-600 transition">
        Choose Plan
      </button>
    </div>
  );

export default Subscription;