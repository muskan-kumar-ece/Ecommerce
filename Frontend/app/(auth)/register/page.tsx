"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { register } from "@/lib/api/auth";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await register({ name, email, password });
      setMessage("Registration successful. Please login.");
    } catch {
      setMessage("Registration failed.");
    }
  };

  return (
    <div className="mx-auto mt-12 max-w-md px-4">
      <Card>
        <CardHeader>
          <CardTitle>Create account</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" required />
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
            />
            <Button type="submit" className="w-full">
              Register
            </Button>
            {message && <p className="text-sm text-slate-600">{message}</p>}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
