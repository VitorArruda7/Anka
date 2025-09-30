import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  difference: number;
}

export function KpiCard({ title, value, difference }: KpiCardProps) {
  const isPositive = difference >= 0;

  return (
    <Card className="space-y-4">
      <CardHeader>
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <div className="flex items-center gap-2 text-sm">
        {isPositive ? (
          <ArrowUpRight className="h-4 w-4 text-positive" />
        ) : (
          <ArrowDownRight className="h-4 w-4 text-negative" />
        )}
        <span className={cn(isPositive ? "text-positive" : "text-negative")}>{difference}%</span>
        <span className="text-muted">vs período anterior</span>
      </div>
    </Card>
  );
}
