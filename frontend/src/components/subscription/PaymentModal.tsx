import React, { useEffect, useState } from 'react';
import {
  X, Copy, Check, Loader2, Clock, AlertCircle, ExternalLink,
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { toast } from 'react-hot-toast';
import { paymentsApi, type Payment } from '@/api/payments';

interface PaymentModalProps {
  payment: Payment;
  onClose: () => void;
  onSuccess: () => void;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ payment, onClose, onSuccess }) => {
  const [copied, setCopied] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number>(0);
  const [current, setCurrent] = useState<Payment>(payment);

  // Countdown timer
  useEffect(() => {
    if (!current.expires_at) return;
    const expiry = new Date(current.expires_at).getTime();
    const tick = () => {
      const diff = Math.max(0, Math.floor((expiry - Date.now()) / 1000));
      setSecondsLeft(diff);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [current.expires_at]);

  // Auto-verify every 30s while pending (up to 5 times)
  useEffect(() => {
    if (current.status !== 'pending') return;
    let attempts = 0;
    const id = setInterval(async () => {
      attempts++;
      if (attempts > 10) return; // stop after 5 min
      try {
        const res = await paymentsApi.verify(current.id);
        if (res.success) {
          toast.success(res.message);
          onSuccess();
        }
      } catch {
        /* silent */
      }
    }, 30000);
    return () => clearInterval(id);
  }, [current.id, current.status, onSuccess]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(current.wallet_address);
      setCopied(true);
      toast.success('Wallet address copied');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await paymentsApi.verify(current.id);
      if (res.success) {
        toast.success(res.message);
        onSuccess();
      } else {
        toast.error(res.message);
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const handleCancel = async () => {
    try {
      await paymentsApi.cancel(current.id);
      toast.success('Payment cancelled');
      onClose();
    } catch {
      toast.error('Failed to cancel');
    }
  };

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const expired = secondsLeft === 0;
  const completed = current.status === 'completed';

  const qrData = `ethereum:${current.wallet_address}?value=${current.amount_usdt}&token=USDT`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#2a2a4a]">
          <div>
            <h2 className="text-lg font-bold text-white">
              {completed ? '✅ Payment Complete' : 'Complete Payment'}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {current.plan} · {current.months} month{current.months > 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-[#2a2a4a] transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {completed ? (
          <div className="p-6 text-center">
            <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 border rounded-full bg-green-500/20 border-green-500/40">
              <Check className="w-8 h-8 text-green-400" />
            </div>
            <p className="mb-1 font-semibold text-white">Subscription Activated</p>
            <p className="mb-6 text-sm text-gray-400">
              Your {current.plan} plan is now active.
            </p>
            <button
              onClick={onSuccess}
              className="w-full py-3 bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-lg font-medium transition"
            >
              Continue
            </button>
          </div>
        ) : (
          <div className="p-5 space-y-5">
            {/* Amount */}
            <div className="text-center">
              <div className="mb-1 text-xs text-gray-500 uppercase">Send exactly</div>
              <div className="text-3xl font-bold text-[#6366f1]">
                ${current.amount_usdt.toFixed(2)}
              </div>
              <div className="mt-1 text-xs text-gray-500">USDT on {current.network}</div>
            </div>

            {/* QR Code */}
            <div className="p-4 mx-auto bg-white rounded-xl w-fit">
              <QRCodeSVG value={qrData} size={180} level="M" />
            </div>

            {/* Wallet Address */}
            <div>
              <label className="text-xs uppercase text-gray-500 mb-1.5 block">
                To This Wallet
              </label>
              <div className="flex items-center gap-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg p-3">
                <code className="flex-1 font-mono text-xs text-gray-300 truncate">
                  {current.wallet_address}
                </code>
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-[#2a2a4a] transition flex-shrink-0"
                  aria-label="Copy address"
                >
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Timer */}
            <div className="flex items-center justify-center gap-2 text-sm">
              <Clock className={`w-4 h-4 ${expired ? 'text-red-400' : 'text-gray-400'}`} />
              {expired ? (
                <span className="font-medium text-red-400">Payment window expired</span>
              ) : (
                <span className="text-gray-400">
                  Expires in{' '}
                  <span className="font-mono text-white">
                    {minutes}:{String(seconds).padStart(2, '0')}
                  </span>
                </span>
              )}
            </div>

            {/* Warning */}
            <div className="p-3 border rounded-lg bg-yellow-500/10 border-yellow-500/30">
              <div className="flex items-start gap-2 text-xs text-yellow-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>
                  Send the exact amount from a wallet you control. Wrong amount or wrong
                  network → funds lost.
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={handleVerify}
                disabled={verifying || expired}
                className="w-full py-3 bg-[#6366f1] hover:bg-[#4f46e5] text-white rounded-lg font-medium transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {verifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {verifying ? 'Checking blockchain...' : "I've Sent The Payment"}
              </button>
              <button
                onClick={handleCancel}
                className="w-full py-2 text-xs text-gray-500 transition hover:text-gray-300"
              >
                Cancel
              </button>
            </div>

            {/* Explorer link */}
            <div className="text-center pt-2 border-t border-[#2a2a4a]">
              <a
                href={`https://bscscan.com/address/${current.wallet_address}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-500 hover:text-[#6366f1] inline-flex items-center gap-1"
              >
                View on BscScan
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentModal;