import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Brain,
  CandlestickChart,
  Target,
  LineChart,
  Bell,
  DollarSign,
  Check,
  ArrowRight,
  ChevronDown,
  Shield,
  Zap,
  Sparkles,
  TrendingUp,
  Users,
  Clock,
  Lock,
  Menu,
  X,
} from 'lucide-react';

// ============================================
// Data
// ============================================
const STRATEGIES = [
  { icon: '🛡️', name: 'Conservative', risk: 'Low', desc: 'Capital preservation. High-confidence setups only.' },
  { icon: '⚖️', name: 'Balanced', risk: 'Medium', desc: 'Trend, momentum, and mean-reversion combined.' },
  { icon: '🔥', name: 'Aggressive', risk: 'High', desc: 'Momentum chaser. More trades, wider stops.' },
  { icon: '⚡', name: 'Scalping', risk: 'High', desc: 'Quick in-and-out on short timeframes.' },
  { icon: '📈', name: 'Swing', risk: 'Medium', desc: 'Ride multi-day trends through pullbacks.' },
  { icon: '💰', name: 'DCA Recovery', risk: 'High', desc: 'Buys dips, averages down, exits on recovery.' },
];

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Signal Engine',
    desc: 'Multi-indicator analysis (RSI, MACD, Bollinger Bands, SMA) generates BUY/SELL/HOLD signals every cycle.',
    color: '#6366f1',
  },
  {
    icon: CandlestickChart,
    title: 'Live Charts',
    desc: 'TradingView-style candlesticks with real-time AI trade markers — see exactly where the AI enters.',
    color: '#10b981',
  },
  {
    icon: Target,
    title: '6 Strategies',
    desc: 'From ultra-safe Conservative to aggressive DCA Recovery — pick the one that fits your risk profile.',
    color: '#f59e0b',
  },
  {
    icon: LineChart,
    title: 'Advanced Analytics',
    desc: 'Equity curves, drawdown charts, Sharpe/Sortino ratios, win/loss distribution, and per-symbol performance.',
    color: '#a855f7',
  },
  {
    icon: Bell,
    title: 'Telegram Alerts',
    desc: 'Real-time trade notifications sent straight to your phone or Telegram group. Never miss an entry.',
    color: '#3b82f6',
  },
  {
    icon: DollarSign,
    title: 'Hybrid Position Sizing',
    desc: 'Trade amount auto-scales with AI confidence. Small positions on weak signals, bigger on strong ones.',
    color: '#ef4444',
  },
];

const STATS = [
  { value: '6', label: 'AI Strategies' },
  { value: '7', label: 'Crypto Pairs' },
  { value: '24/7', label: 'Monitoring' },
  { value: '99.9%', label: 'Uptime' },
];

const PLANS = [
  {
    name: 'Basic',
    price: 0,
    period: 'forever',
    popular: false,
    features: [
      '📊 Demo Trading',
      '📈 Basic AI Signals',
      '📋 Paper Trading',
      '📱 Basic Dashboard',
    ],
    cta: 'Start Free',
  },
  {
    name: 'Pro',
    price: 29.99,
    period: 'per month',
    popular: true,
    features: [
      '🔴 Live Trading',
      '🧠 Advanced AI Engine',
      '🛡️ Risk Management',
      '⚡ Priority Support',
      '📊 Real-time Analytics',
      '🔔 Custom Alerts',
    ],
    cta: 'Start Pro Trial',
  },
  {
    name: 'Enterprise',
    price: 99.99,
    period: 'per month',
    popular: false,
    features: [
      '🏢 All Pro Features',
      '🔄 Multiple Exchanges',
      '🎯 Custom Strategies',
      '👨‍💼 Dedicated Support',
      '📈 Advanced Analytics',
      '🔐 White-label Options',
    ],
    cta: 'Contact Sales',
  },
];

const FAQ = [
  {
    q: 'What is JADOTA AI?',
    a: 'JADOTA AI is an AI-powered crypto trading platform. It analyzes live market data across multiple timeframes and generates trading signals using 6 built-in strategies — you can paper trade them for free or automate them with real money.',
  },
  {
    q: 'Do I need trading experience?',
    a: 'No. The AI handles market analysis and signal generation. You pick your strategy and risk level, and JADOTA handles the rest. Start with our free demo to learn without risking capital.',
  },
  {
    q: 'Is my money safe?',
    a: 'Your funds stay in your own exchange account (Bitget). JADOTA never has withdrawal permissions — we only place trades with your explicit API key. You retain full custody at all times.',
  },
  {
    q: 'Can I try it for free?',
    a: 'Yes! The Basic plan includes unlimited paper trading with live market data and real AI signals. No credit card required to get started.',
  },
  {
    q: 'What exchanges are supported?',
    a: 'Bitget is fully supported today. Additional exchanges (Binance, Bybit, OKX) are on the roadmap for Enterprise customers.',
  },
];

// ============================================
// Page
// ============================================
const Landing: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);

  // Smooth scroll helper
  const scrollTo = (id: string) => {
    setMobileMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-white overflow-x-hidden">
      {/* ============================================ */}
      {/* Top Navigation */}
      {/* ============================================ */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a1a]/80 backdrop-blur-md border-b border-[#2a2a4a]/60">
        <div className="flex items-center justify-between h-16 px-4 mx-auto max-w-7xl lg:px-8">
          {/* Logo */}
          <Link to="/" className="flex items-center flex-shrink-0 gap-2">
            <img
              src="/jadota-icon.png"
              alt="JADOTA AI"
              className="object-contain w-8 h-8"
            />
            <span className="text-lg font-bold text-white">
              JADOTA <span className="text-[#6366f1]">AI</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="items-center hidden gap-8 md:flex">
            <button onClick={() => scrollTo('features')} className="text-sm text-gray-400 transition hover:text-white">
              Features
            </button>
            <button onClick={() => scrollTo('strategies')} className="text-sm text-gray-400 transition hover:text-white">
              Strategies
            </button>
            <button onClick={() => scrollTo('pricing')} className="text-sm text-gray-400 transition hover:text-white">
              Pricing
            </button>
            <button onClick={() => scrollTo('faq')} className="text-sm text-gray-400 transition hover:text-white">
              FAQ
            </button>
          </div>

          {/* Desktop CTAs */}
          <div className="items-center hidden gap-3 md:flex">
            <Link to="/login" className="px-3 py-2 text-sm text-gray-400 transition hover:text-white">
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium bg-[#6366f1] hover:bg-[#4f46e5] text-white px-4 py-2 rounded-lg transition flex items-center gap-1.5"
            >
              Get Started
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen((v) => !v)}
            className="md:hidden p-2 -mr-2 rounded-lg text-gray-400 hover:text-white hover:bg-[#1a1a2e] transition"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[#2a2a4a] bg-[#0a0a1a] px-4 py-3 space-y-1">
            {['features', 'strategies', 'pricing', 'faq'].map((id) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className="block w-full text-left px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-[#1a1a2e] rounded-lg capitalize"
              >
                {id}
              </button>
            ))}
            <div className="pt-2 border-t border-[#2a2a4a] space-y-2">
              <Link
                to="/login"
                className="block w-full text-center px-3 py-2.5 text-sm text-gray-300 hover:text-white border border-[#2a2a4a] rounded-lg"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="block w-full text-center px-3 py-2.5 text-sm font-medium bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-lg"
              >
                Get Started Free
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* ============================================ */}
      {/* Hero */}
      {/* ============================================ */}
      <section className="relative px-4 pb-16 overflow-hidden pt-28 lg:pt-36 lg:pb-24 lg:px-8">
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-[#6366f1]/10 rounded-full blur-3xl" />
          <div className="absolute top-40 right-0 w-[400px] h-[400px] bg-[#a855f7]/10 rounded-full blur-3xl" />
        </div>

        <div className="mx-auto text-center max-w-7xl">
          {/* Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#6366f1]/10 border border-[#6366f1]/30 rounded-full text-xs font-medium text-[#a5b4fc] mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            Now with 6 AI strategies & DCA Recovery
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-white leading-[1.1] mb-6">
            AI-Powered{' '}
            <span className="bg-gradient-to-r from-[#6366f1] to-[#a855f7] bg-clip-text text-transparent">
              Crypto Trading
            </span>
            <br className="hidden sm:block" />
            Intelligence
          </h1>

          {/* Subheadline */}
          <p className="max-w-3xl px-4 mx-auto mb-10 text-base leading-relaxed text-gray-400 sm:text-lg lg:text-xl">
            Six institutional-grade strategies. Real-time AI signals. Automated execution with
            confidence-based position sizing. All in one platform — free to start.
          </p>

          {/* CTAs */}
          <div className="flex flex-col items-center justify-center gap-3 mb-8 sm:flex-row">
            <Link
              to="/register"
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold px-6 py-3.5 rounded-xl transition shadow-lg shadow-[#6366f1]/25 text-base"
            >
              Start Trading Free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => scrollTo('features')}
              className="w-full sm:w-auto px-6 py-3.5 bg-[#1a1a2e] hover:bg-[#2a2a4a] border border-[#2a2a4a] text-white font-medium rounded-xl transition text-base"
            >
              Explore Features
            </button>
          </div>

          <p className="flex flex-wrap items-center justify-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-green-400" />
              Free forever plan
            </span>
            <span className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-green-400" />
              No credit card
            </span>
            <span className="flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5 text-green-400" />
              Non-custodial
            </span>
          </p>
        </div>

        {/* Dashboard preview mockup */}
        <div className="max-w-5xl px-4 mx-auto mt-16 lg:mt-20">
          <div className="relative rounded-2xl border border-[#2a2a4a] bg-gradient-to-b from-[#1a1a2e] to-[#0a0a1a] overflow-hidden shadow-2xl shadow-[#6366f1]/10">
            {/* Fake window chrome */}
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[#2a2a4a] bg-[#0a0a1a]">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
              <div className="w-3 h-3 rounded-full bg-green-500/60" />
              <div className="flex justify-center flex-1 ml-4">
                <span className="text-[10px] text-gray-600 font-mono">jadota-ai.app/dashboard</span>
              </div>
            </div>

            {/* Preview content */}
            <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-3 lg:p-6">
              {/* Stat cards */}
              <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="text-[10px] uppercase text-gray-500 mb-1">Total P&amp;L</div>
                <div className="text-2xl font-bold text-green-400">+$1,247.83</div>
                <div className="text-xs text-green-400/70 mt-0.5">+12.4% this month</div>
              </div>
              <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="text-[10px] uppercase text-gray-500 mb-1">Win Rate</div>
                <div className="text-2xl font-bold text-[#6366f1]">68.5%</div>
                <div className="text-xs text-gray-500 mt-0.5">142 trades</div>
              </div>
              <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="text-[10px] uppercase text-gray-500 mb-1">Active Signals</div>
                <div className="text-2xl font-bold text-white">4</div>
                <div className="text-xs text-gray-500 mt-0.5">2 BUY · 2 HOLD</div>
              </div>

              {/* Chart preview */}
              <div className="md:col-span-3 bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a] h-40 flex items-end gap-1">
                {[40, 55, 48, 65, 72, 60, 78, 85, 72, 90, 95, 82, 100, 88, 95, 108, 115, 105, 122, 130].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t bg-gradient-to-t from-[#6366f1]/40 to-[#6366f1]"
                    style={{ height: `${(h / 140) * 100}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Stats Bar */}
      {/* ============================================ */}
      <section className="border-y border-[#2a2a4a]/60 py-10 px-4 lg:px-8">
        <div className="grid max-w-6xl grid-cols-2 gap-6 mx-auto md:grid-cols-4">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-[#6366f1] mb-1">{s.value}</div>
              <div className="text-xs tracking-wider text-gray-500 uppercase sm:text-sm">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================ */}
      {/* Features */}
      {/* ============================================ */}
      <section id="features" className="px-4 py-20 lg:py-28 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#6366f1]/10 border border-[#6366f1]/30 rounded-full text-xs font-medium text-[#a5b4fc] mb-4">
              <Zap className="w-3.5 h-3.5" />
              Platform
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Everything You Need To Trade Smarter
            </h2>
            <p className="max-w-2xl mx-auto text-base text-gray-400 lg:text-lg">
              From AI signal generation to automated execution and deep analytics — JADOTA AI is
              a complete trading intelligence platform.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-2xl p-6 hover:border-[#3a3a5a] transition group"
                >
                  <div
                    className="flex items-center justify-center w-12 h-12 mb-4 transition rounded-xl group-hover:scale-110"
                    style={{ backgroundColor: `${f.color}15`, border: `1px solid ${f.color}40` }}
                  >
                    <Icon className="w-6 h-6" style={{ color: f.color }} />
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-white">{f.title}</h3>
                  <p className="text-sm leading-relaxed text-gray-400">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Strategies */}
      {/* ============================================ */}
      <section id="strategies" className="py-20 lg:py-28 px-4 lg:px-8 bg-gradient-to-b from-transparent via-[#1a1a2e]/30 to-transparent">
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#10b981]/10 border border-[#10b981]/30 rounded-full text-xs font-medium text-[#6ee7b7] mb-4">
              <Target className="w-3.5 h-3.5" />
              Strategies
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Six Strategies, One Platform
            </h2>
            <p className="max-w-2xl mx-auto text-base text-gray-400 lg:text-lg">
              From ultra-safe capital preservation to aggressive DCA recovery — pick the strategy
              that matches your risk profile.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {STRATEGIES.map((s) => (
              <div
                key={s.name}
                className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5 hover:border-[#6366f1]/40 transition"
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="flex-shrink-0 text-3xl">{s.icon}</span>
                  <div>
                    <h3 className="font-semibold text-white">{s.name}</h3>
                    <span
                      className={`text-xs font-medium ${
                        s.risk === 'Low'
                          ? 'text-green-400'
                          : s.risk === 'High'
                          ? 'text-red-400'
                          : 'text-yellow-400'
                      }`}
                    >
                      {s.risk} Risk
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* How It Works */}
      {/* ============================================ */}
      <section className="px-4 py-20 lg:py-28 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#a855f7]/10 border border-[#a855f7]/30 rounded-full text-xs font-medium text-[#d8b4fe] mb-4">
              <TrendingUp className="w-3.5 h-3.5" />
              How It Works
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Live In Three Steps
            </h2>
          </div>

          <div className="relative grid grid-cols-1 gap-6 md:grid-cols-3 lg:gap-8">
            {[
              { n: '1', title: 'Pick Your Strategy', desc: 'Choose from 6 presets — Conservative, Balanced, Aggressive, Scalping, Swing, or DCA Recovery.' },
              { n: '2', title: 'Let AI Analyze Markets', desc: 'The AI engine scans 7 crypto pairs 24/7, running 15+ indicators to find high-probability setups.' },
              { n: '3', title: 'Trade Manually Or Automate', desc: 'Take signals manually or enable Auto-Trade. Position sizes scale automatically with AI confidence.' },
            ].map((step, i) => (
              <div key={step.n} className="relative text-center">
                <div className="w-16 h-16 rounded-full bg-[#6366f1]/10 border-2 border-[#6366f1] flex items-center justify-center mx-auto mb-5 text-2xl font-bold text-[#6366f1]">
                  {step.n}
                </div>
                <h3 className="mb-2 text-xl font-semibold text-white">{step.title}</h3>
                <p className="max-w-xs mx-auto text-sm text-gray-400">{step.desc}</p>
                {i < 2 && (
                  <div className="hidden md:block absolute top-8 -right-4 lg:-right-6 w-8 lg:w-12 h-0.5 bg-gradient-to-r from-[#6366f1] to-transparent" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Pricing */}
      {/* ============================================ */}
      <section id="pricing" className="px-4 py-20 lg:py-28 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#f59e0b]/10 border border-[#f59e0b]/30 rounded-full text-xs font-medium text-[#fcd34d] mb-4">
              <DollarSign className="w-3.5 h-3.5" />
              Pricing
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Simple, Transparent Pricing
            </h2>
            <p className="max-w-2xl mx-auto text-base text-gray-400 lg:text-lg">
              Start free. Upgrade when you're ready to trade with real money.
            </p>
          </div>

          <div className="grid max-w-5xl grid-cols-1 gap-6 mx-auto md:grid-cols-3">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl p-6 lg:p-8 border-2 transition ${
                  plan.popular
                    ? 'bg-gradient-to-b from-[#6366f1]/10 to-[#1a1a2e] border-[#6366f1] shadow-xl shadow-[#6366f1]/20'
                    : 'bg-[#1a1a2e] border-[#2a2a4a]'
                }`}
              >
                {plan.popular && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#6366f1] text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                )}

                <div className="mb-6 text-center">
                  <h3 className="mb-3 text-xl font-bold text-white">{plan.name}</h3>
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold text-[#6366f1]">
                      {plan.price === 0 ? 'Free' : `$${plan.price}`}
                    </span>
                    {plan.price > 0 && (
                      <span className="text-sm text-gray-500">/{plan.period.split(' ')[1]}</span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-400">{plan.period}</p>
                </div>

                <ul className="mb-8 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm text-gray-300">
                      <Check className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  to="/register"
                  className={`block w-full text-center py-3 rounded-lg font-semibold transition ${
                    plan.popular
                      ? 'bg-[#6366f1] hover:bg-[#4f46e5] text-white'
                      : 'bg-[#0a0a1a] hover:bg-[#2a2a4a] text-white border border-[#2a2a4a]'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>

          <p className="flex flex-wrap items-center justify-center gap-4 mt-8 text-xs text-center text-gray-500">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              Secure payments in USDT
            </span>
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" />
              7-day refund policy
            </span>
          </p>
        </div>
      </section>

      {/* ============================================ */}
      {/* FAQ */}
      {/* ============================================ */}
      <section id="faq" className="py-20 lg:py-28 px-4 lg:px-8 bg-gradient-to-b from-transparent via-[#1a1a2e]/30 to-transparent">
        <div className="max-w-3xl mx-auto">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Frequently Asked Questions
            </h2>
            <p className="text-gray-400">Everything you need to know before getting started.</p>
          </div>

          <div className="space-y-3">
            {FAQ.map((item, i) => (
              <div
                key={item.q}
                className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaqIndex(openFaqIndex === i ? null : i)}
                  className="w-full flex items-center justify-between p-5 text-left hover:bg-[#2a2a4a]/30 transition"
                >
                  <span className="pr-4 font-medium text-white">{item.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${
                      openFaqIndex === i ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {openFaqIndex === i && (
                  <div className="px-5 pb-5 text-sm text-gray-400 leading-relaxed border-t border-[#2a2a4a] pt-4">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Final CTA */}
      {/* ============================================ */}
      <section className="px-4 py-20 lg:py-28 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-3xl border border-[#6366f1]/30 bg-gradient-to-br from-[#6366f1]/10 via-[#1a1a2e] to-[#a855f7]/10 p-8 lg:p-14 text-center overflow-hidden">
            {/* Glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[400px] bg-[#6366f1]/20 rounded-full blur-3xl -z-10" />

            <div className="mb-4 text-4xl">🚀</div>
            <h2 className="mb-4 text-3xl font-bold text-white lg:text-5xl">
              Ready To Trade Smarter?
            </h2>
            <p className="max-w-xl mx-auto mb-8 text-base text-gray-400 lg:text-lg">
              Join traders using JADOTA AI to automate their crypto strategies. Start free — no
              credit card required.
            </p>
            <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                to="/register"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#6366f1] hover:bg-[#4f46e5] text-white font-semibold px-8 py-4 rounded-xl transition shadow-lg shadow-[#6366f1]/25"
              >
                Get Started Free
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto px-8 py-4 bg-transparent hover:bg-[#2a2a4a]/50 border border-[#2a2a4a] text-white font-medium rounded-xl transition"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================ */}
      {/* Footer */}
      {/* ============================================ */}
      <footer className="border-t border-[#2a2a4a]/60 py-12 px-4 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 gap-8 mb-10 md:grid-cols-4">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <img src="/jadota-icon.png" alt="JADOTA AI" className="object-contain w-8 h-8" />
                <span className="text-lg font-bold text-white">
                  JADOTA <span className="text-[#6366f1]">AI</span>
                </span>
              </div>
              <p className="max-w-sm text-sm leading-relaxed text-gray-500">
                AI-powered crypto trading intelligence. Six strategies, live signals, automated
                execution — built for the modern trader.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="mb-3 text-sm font-semibold tracking-wider text-white uppercase">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><button onClick={() => scrollTo('features')} className="text-gray-500 transition hover:text-white">Features</button></li>
                <li><button onClick={() => scrollTo('strategies')} className="text-gray-500 transition hover:text-white">Strategies</button></li>
                <li><button onClick={() => scrollTo('pricing')} className="text-gray-500 transition hover:text-white">Pricing</button></li>
                <li><button onClick={() => scrollTo('faq')} className="text-gray-500 transition hover:text-white">FAQ</button></li>
              </ul>
            </div>

            {/* Account */}
            <div>
              <h4 className="mb-3 text-sm font-semibold tracking-wider text-white uppercase">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="text-gray-500 transition hover:text-white">Sign In</Link></li>
                <li><Link to="/register" className="text-gray-500 transition hover:text-white">Create Account</Link></li>
                <li><Link to="/subscription" className="text-gray-500 transition hover:text-white">Subscription</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-[#2a2a4a] pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-gray-600">
              © {new Date().getFullYear()} JADOTA AI. All rights reserved.
            </p>
            <p className="flex items-center gap-3 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Built for 24/7 markets
              </span>
            </p>
          </div>

          {/* Disclaimer */}
          <p className="text-[11px] text-gray-700 text-center mt-6 max-w-3xl mx-auto leading-relaxed">
            Trading cryptocurrency involves substantial risk of loss. Past performance does not
            guarantee future results. JADOTA AI provides tools and signals — not financial advice.
            Always do your own research.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;