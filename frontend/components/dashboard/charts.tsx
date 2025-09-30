"use client";

import {
  ResponsiveContainer,
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

type CustodyPoint = {
  label: string;
  value: number;
};

type FlowPoint = {
  label: string;
  inflow: number;
  outflow: number;
};

type AllocationSlice = {
  name: string;
  value: number;
};

const fallbackCustody: CustodyPoint[] = [
  { label: "Jan", value: 0 },
  { label: "Fev", value: 0 },
  { label: "Mar", value: 0 },
];

const fallbackFlow: FlowPoint[] = [
  { label: "Jan", inflow: 0, outflow: 0 },
  { label: "Fev", inflow: 0, outflow: 0 },
  { label: "Mar", inflow: 0, outflow: 0 },
];

const fallbackAllocation: AllocationSlice[] = [
  { name: "Sem dados", value: 1 },
];

export function CustodyChart({ data }: { data: CustodyPoint[] }) {
  const chartData = data.length ? data : fallbackCustody;
  return (
    <Card className="h-80">
      <CardHeader>
        <CardTitle>Evolução de custódia</CardTitle>
      </CardHeader>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="custody" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b" }} />
            <Area type="monotone" dataKey="value" stroke="#22c55e" fillOpacity={1} fill="url(#custody)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function FlowChart({ data }: { data: FlowPoint[] }) {
  const chartData = data.length ? data : fallbackFlow;
  return (
    <Card className="h-80">
      <CardHeader>
        <CardTitle>Captação mensal</CardTitle>
      </CardHeader>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b" }} />
            <Legend />
            <Bar dataKey="inflow" name="Entradas" fill="#22c55e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="outflow" name="Saídas" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function AllocationChart({ data }: { data: AllocationSlice[] }) {
  const chartData = data.length ? data : fallbackAllocation;
  return (
    <Card className="h-80">
      <CardHeader>
        <CardTitle>Mix de alocação</CardTitle>
      </CardHeader>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b" }} />
            <Legend />
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#22c55e"
              label
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
