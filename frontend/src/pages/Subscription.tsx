import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { 
  Crown, Check, Loader2, AlertCircle, 
  Shield, Zap, Users, Star, ArrowRight
} from 'lucide-react';

interface Plan {
  id: string;
  name: string;
  tier: 'BASIC' | 'PRO' | 'ENTERPRISE';
  price: number;
  currency: 'USDT';
  duration: number;
  features: string[];
  isPopular?: boolean;
}

const Subscription: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedPlan, setSelectedPlan] = useState<string>('pro');
  const [isLoading, setIsLoading] = useState(false);
  const [plans, setPlans] = useState<Plan[]>([
    {
      id: 'basic',
      name: 'Basic',
      tier: 'BASIC',
      price: 0,
      currency: 'USDT',
      duration: 1,
      features: [
        '📊 Demo Trading',
        '📈 Basic AI Signals',
        '📋 Paper Trading',
        '📱 Basic Dashboard'
      ],
      isPopular: false
    },
    {
      id: 'pro',
      name: 'Pro',
      tier: 'PRO',
      price: 29.99,
      currency: 'USDT',
      duration: 1,
      features: [
        '🔴 Live Trading',
        '🧠 Advanced AI Engine',
        '🛡️ Risk Management',
        '⚡ Priority Support',
        '📊 Real-time Analytics',
        '🔔 Custom Alerts'
      ],
      isPopular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      tier: 'ENTERPRISE',
      price: 99.99,
      currency: 'USDT',
      duration: 1,
      features: [
        '🏢 All Pro Features',
        '🔄 Multiple Exchanges',
        '🎯 Custom Strategies',
        '👨‍💼 Dedicated Support',
        '📈 Advanced Analytics',
        '🔐 White-label Options'
      ],
      isPopular: false
    }
  ]);

  useEffect(() => {
    // In production, fetch plans from API
    // subscriptionApi.getPlans().then(setPlans);
  }, []);

  const handleSubscribe = (plan: Plan) => {
    if (plan.price === 0) {
      toast.success('✅ Basic plan activated! Free demo trading is now available.');
      return;
    }

    if (!user?.id) {
      toast.error('Please login first');
      return;
    }

    setIsLoading(true);
    // In production, redirect to payment flow
    toast.info(`💳 Redirecting to payment for ${plan.name} plan...`);
    
    // Simulate payment flow
    setTimeout(() => {
      setIsLoading(false);
      toast.success(`✅ ${plan.name} plan activated! You now have full access.`);
    }, 2000);
  };

  return (
    <div className="p-6 mx-auto space-y-8 max-w-7xl">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Crown className="w-8 h-8 text-yellow-400" />
          <h1 className="text-3xl font-bold text-white">Subscription Plans</h1>
        </div>
        <p className="max-w-2xl mx-auto text-gray-400">
          Choose the plan that fits your trading needs. All plans include demo trading.
        </p>
        {user?.subscription?.isActive && (
          <div className="inline-flex items-center gap-2 px-4 py-2 mt-2 text-sm text-green-400 border rounded-full bg-green-500/20 border-green-500/30">
            <Check className="w-4 h-4" />
            Current Plan: {user.subscription.plan || 'Active'}
          </div>
        )}
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {plans.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            isCurrent={user?.subscription?.plan === plan.tier && user?.subscription?.isActive}
            onSubscribe={() => handleSubscribe(plan)}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Features Comparison */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-center text-white">Compare Features</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a4a]">
                <th className="px-4 py-3 text-sm text-left text-gray-400">Feature</th>
                <th className="px-4 py-3 text-sm text-center text-gray-400">Basic</th>
                <th className="px-4 py-3 text-center text-[#6366f1] text-sm font-bold">Pro</th>
                <th className="px-4 py-3 text-sm text-center text-gray-400">Enterprise</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2a4a]">
              <FeatureRow feature="Demo Trading" basic="✅" pro="✅" enterprise="✅" />
              <FeatureRow feature="AI Signals" basic="📊 Basic" pro="🧠 Advanced" enterprise="🎯 Custom" />
              <FeatureRow feature="Live Trading" basic="❌" pro="✅" enterprise="✅" />
              <FeatureRow feature="Risk Management" basic="❌" pro="✅" enterprise="✅" />
              <FeatureRow feature="Multiple Exchanges" basic="❌" pro="❌" enterprise="✅" />
              <FeatureRow feature="Priority Support" basic="❌" pro="✅" enterprise="👨‍💼 Dedicated" />
              <FeatureRow feature="Custom Strategies" basic="❌" pro="❌" enterprise="✅" />
              <FeatureRow feature="Analytics" basic="📊 Basic" pro="📈 Advanced" enterprise="📊 Full" />
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Info */}
      <div className="p-6 border bg-yellow-500/10 border-yellow-500/30 rounded-xl">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-yellow-400">Payment Information</p>
            <p className="mt-1 text-sm text-gray-400">
              All payments are processed in USDT (ERC20). After payment confirmation, 
              your subscription will be automatically activated. Demo trading is always free.
            </p>
            <div className="flex flex-wrap gap-3 mt-3">
              <span className="px-3 py-1 bg-[#0a0a1a] rounded-lg text-gray-400 text-sm border border-[#2a2a4a]">
                💰 USDT (ERC20)
              </span>
              <span className="px-3 py-1 bg-[#0a0a1a] rounded-lg text-gray-400 text-sm border border-[#2a2a4a]">
                🔒 Secure Payment
              </span>
              <span className="px-3 py-1 bg-[#0a0a1a] rounded-lg text-gray-400 text-sm border border-[#2a2a4a]">
                ⚡ Auto-activation
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Frequently Asked Questions</h3>
        <div className="space-y-4">
          <FAQItem 
            question="What is the difference between demo and live trading?" 
            answer="Demo trading uses virtual funds and is completely free. Live trading uses your real exchange account with real money and requires a Pro or Enterprise subscription."
          />
          <FAQItem 
            question="How do I connect my Bitget account?" 
            answer="Go to Settings > API Keys, enter your Bitget API credentials. Make sure to create an API key with READ + TRADE permissions only (NO WITHDRAW)."
          />
          <FAQItem 
            question="What happens if my subscription expires?" 
            answer="You will lose access to live trading features, but demo trading remains available. Your trading history and account data are preserved."
          />
          <FAQItem 
            question="Can I upgrade or downgrade my plan?" 
            answer="Yes, you can change your plan at any time. Upgrades take effect immediately, downgrades will take effect at the end of your current billing period."
          />
        </div>
      </div>
    </div>
  );
};

const PlanCard: React.FC<{
  plan: Plan;
  isCurrent: boolean;
  onSubscribe: () => void;
  isLoading: boolean;
}> = ({ plan, isCurrent, onSubscribe, isLoading }) => {
  const isFree = plan.price === 0;
  
  return (
    <div className={`bg-[#1a1a2e] rounded-xl p-6 border relative ${
      plan.isPopular ? 'border-[#6366f1]' : 'border-[#2a2a4a]'
    } ${isCurrent ? 'border-green-500' : ''}`}>
      {plan.isPopular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#6366f1] text-white text-xs px-3 py-1 rounded-full">
          Most Popular
        </span>
      )}
      {isCurrent && (
        <span className="absolute px-3 py-1 text-xs text-white bg-green-500 rounded-full -top-3 right-4">
          Current Plan
        </span>
      )}
      
      <div className="mb-4 text-center">
        <h3 className="text-xl font-bold text-white">{plan.name}</h3>
        <div className="mt-2">
          <span className="text-3xl font-bold text-[#6366f1]">
            {isFree ? 'Free' : `$${plan.price}`}
          </span>
          {!isFree && <span className="text-sm text-gray-400">/month</span>}
        </div>
        <p className="mt-1 text-sm text-gray-400">
          {isFree ? 'Forever free' : 'Billed monthly'}
        </p>
      </div>

      <ul className="mb-6 space-y-2">
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <Check className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={onSubscribe}
        disabled={isLoading || isCurrent}
        className={`w-full py-2.5 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
          isCurrent
            ? 'bg-green-500/20 text-green-400 cursor-default'
            : plan.isPopular
              ? 'bg-[#6366f1] text-white hover:bg-[#4f46e5]'
              : isFree
                ? 'bg-[#2a2a4a] text-white hover:bg-[#3a3a5a]'
                : 'bg-[#2a2a4a] text-gray-300 hover:bg-[#3a3a5a]'
        }`}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isCurrent ? (
          '✅ Active'
        ) : isFree ? (
          'Start Free'
        ) : (
          <>
            Subscribe
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
};

const FeatureRow: React.FC<{
  feature: string;
  basic: string;
  pro: string;
  enterprise: string;
}> = ({ feature, basic, pro, enterprise }) => (
  <tr>
    <td className="px-4 py-3 text-sm text-gray-300">{feature}</td>
    <td className="px-4 py-3 text-sm text-center">{basic}</td>
    <td className="px-4 py-3 text-center text-sm text-[#6366f1] font-medium">{pro}</td>
    <td className="px-4 py-3 text-sm text-center">{enterprise}</td>
  </tr>
);

const FAQItem: React.FC<{
  question: string;
  answer: string;
}> = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="border-b border-[#2a2a4a] last:border-0 pb-4 last:pb-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="font-medium text-white">{question}</span>
        <span className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {isOpen && (
        <p className="mt-2 text-sm text-gray-400">{answer}</p>
      )}
    </div>
  );
};

export default Subscription;