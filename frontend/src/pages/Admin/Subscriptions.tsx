import React from 'react';
import { Crown, Users, DollarSign, Clock } from 'lucide-react';

const Subscriptions: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Subscriptions</h1>
        <p className="mt-1 text-gray-400">Manage user subscriptions and plans</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SubscriptionStatCard
          title="Total Subscriptions"
          value="0"
          icon={<Crown className="w-5 h-5 text-yellow-400" />}
        />
        <SubscriptionStatCard
          title="Active Subscriptions"
          value="0"
          icon={<Users className="w-5 h-5 text-green-400" />}
        />
        <SubscriptionStatCard
          title="Monthly Revenue"
          value="$0.00"
          icon={<DollarSign className="w-5 h-5 text-blue-400" />}
        />
        <SubscriptionStatCard
          title="Pending Payments"
          value="0"
          icon={<Clock className="w-5 h-5 text-orange-400" />}
        />
      </div>

      {/* Plans Section */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Available Plans</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <PlanCard 
            name="Basic"
            price="$0"
            features={['Demo Trading', 'Basic AI Signals', 'Paper Trading']}
          />
          <PlanCard 
            name="Pro"
            price="$29/mo"
            features={['Live Trading', 'Advanced AI', 'Risk Management', 'Priority Support']}
            popular
          />
          <PlanCard 
            name="Enterprise"
            price="$99/mo"
            features={['All Pro Features', 'Multiple Exchanges', 'Custom Strategies', 'Dedicated Support']}
          />
        </div>
      </div>

      {/* Recent Subscriptions */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Recent Subscriptions</h3>
        <div className="py-8 text-center text-gray-400">
          No recent subscriptions found
        </div>
      </div>
    </div>
  );
};

const SubscriptionStatCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
}> = ({ title, value, icon }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

const PlanCard: React.FC<{
  name: string;
  price: string;
  features: string[];
  popular?: boolean;
}> = ({ name, price, features, popular }) => (
  <div className={`bg-[#0a0a1a] rounded-xl p-6 border ${popular ? 'border-[#6366f1]' : 'border-[#2a2a4a]'} relative`}>
    {popular && (
      <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#6366f1] text-white text-xs px-3 py-1 rounded-full">
        Most Popular
      </span>
    )}
    <h4 className="text-xl font-bold text-white">{name}</h4>
    <p className="text-2xl font-bold text-[#6366f1] my-2">{price}</p>
    <ul className="mb-4 space-y-2">
      {features.map((feature, i) => (
        <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
          <span className="text-green-400">✓</span> {feature}
        </li>
      ))}
    </ul>
    <button className={`w-full py-2 rounded-lg font-medium transition ${
      popular 
        ? 'bg-[#6366f1] text-white hover:bg-[#4f46e5]'
        : 'bg-[#2a2a4a] text-gray-300 hover:bg-[#3a3a5a]'
    }`}>
      {popular ? 'Subscribe Now' : 'Coming Soon'}
    </button>
  </div>
);

export default Subscriptions;