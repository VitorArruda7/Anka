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
  Cell,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PieLabelRenderProps } from "recharts";
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
const allocationColors = [
  "#06b6d4",
  "#22c55e",
  "#f97316",
  "#a855f7",
  "#ef4444",
  "#14b8a6",
  "#eab308",
  "#3b82f6",
  "#facc15",
  "#fb7185",
];

const RADIAN = Math.PI / 180;

function renderAllocationLabel({
  cx = 0,
  cy = 0,
  midAngle = 0,
  innerRadius = 0,
  outerRadius = 0,
  percent = 0,
}: PieLabelRenderProps) {
  const centerX = typeof cx === "number" ? cx : Number(cx) || 0;
  const centerY = typeof cy === "number" ? cy : Number(cy) || 0;
  const inner = typeof innerRadius === "number" ? innerRadius : Number(innerRadius) || 0;
  const outer = typeof outerRadius === "number" ? outerRadius : Number(outerRadius) || inner;
  const valuePercent = typeof percent === "number" ? percent : Number(percent) || 0;
  const radius = inner + (outer - inner) * 0.5;
  const angle = -midAngle * RADIAN;
  const x = centerX + radius * Math.cos(angle);
  const y = centerY + radius * Math.sin(angle);

  return (
    <text
      x={x}
      y={y}
      textAnchor={x > centerX ? "start" : "end"}
      dominantBaseline="central"
      className="fill-foreground text-xs font-medium"
    >
      {`${Math.round(valuePercent * 100)}%`}
    </text>
  );
}


export function CustodyChart({ data }: { data: CustodyPoint[] }) {
  const chartData = data.length ? data : fallbackCustody;
  return (
    <Card className="h-80">
      <CardHeader>
        <CardTitle>Evolução de custódia</CardTitle>
      </CardHeader>
      <div className="h-72">
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
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 16, right: 16, bottom: 32, left: 16 }}>
            <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b" }} />
            <Legend layout="horizontal" verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ fontSize: "0.75rem" }} />
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={85}
              paddingAngle={2}
              labelLine={false}
              label={renderAllocationLabel}
            >
              {chartData.map((slice, index) => (
                <Cell key={slice.name} fill={allocationColors[index % allocationColors.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
