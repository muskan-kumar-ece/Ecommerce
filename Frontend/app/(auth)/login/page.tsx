"use client";

import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await login(email, password);
      setMessage("Login successful.");
    } catch {
      setMessage("Login failed. Check your credentials.");
    }
  };

  return (
    <div className="mx-auto mt-12 max-w-md px-4">
      <Card>
        <CardHeader>
          <CardTitle>Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
            />
            <Button type="submit" className="w-full">
              Sign In
            </Button>
            {message && <p className="text-sm text-slate-600">{message}</p>}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
