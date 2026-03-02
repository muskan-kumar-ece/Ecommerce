"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegisterPage() {
  return (
    <div className="mx-auto mt-12 max-w-md px-4">
      <Card>
        <CardHeader>
          <CardTitle>Create account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-600">
            Signup is not exposed in the current API contract. Please create users via backend admin and use login with
            JWT token endpoints.
          </p>
          <Button type="button" className="w-full" disabled>
            Registration unavailable
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
