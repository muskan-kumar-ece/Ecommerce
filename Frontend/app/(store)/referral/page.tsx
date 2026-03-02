"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchReferralSummary } from "@/lib/api/referral";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
});

function toNumber(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function ReferralPage() {
  const [copied, setCopied] = useState(false);
  const { data, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ["referral-summary"],
    queryFn: fetchReferralSummary,
  });

  async function copyReferralLink() {
    if (!data?.referral_link) return;
    await navigator.clipboard.writeText(data.referral_link);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Referral Dashboard</h1>
        <p className="text-sm text-slate-500">Invite friends and track your referral rewards.</p>
      </header>

      {isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Loading referral summary...</CardTitle>
          </CardHeader>
        </Card>
      ) : null}

      {isError ? (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-base text-red-700">Could not load referral dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? "Retrying..." : "Retry"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Earned Rewards</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">
                {currencyFormatter.format(toNumber(data.earned_rewards))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Successful Referrals</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">{data.successful_referrals}</CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Pending Rewards</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-semibold text-slate-900">{data.pending_rewards}</CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Share your referral link</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="break-all rounded-md bg-slate-100 p-3 text-sm text-slate-700">{data.referral_link}</p>
              <Button onClick={copyReferralLink}>{copied ? "Copied!" : "Copy referral link"}</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Reward Coupons Earned</CardTitle>
            </CardHeader>
            <CardContent>
              {data.reward_coupon_codes.length ? (
                <div className="flex flex-wrap gap-2">
                  {data.reward_coupon_codes.map((code) => (
                    <span key={code} className="rounded-full border border-slate-300 px-3 py-1 text-sm text-slate-700">
                      {code}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No reward coupons earned yet.</p>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </section>
  );
}
