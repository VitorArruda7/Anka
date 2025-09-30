"use client";

import { Suspense, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { AllocationChart, CustodyChart, FlowChart } from "@/components/dashboard/charts";
import { ClientsTable } from "@/components/dashboard/clients-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/axios";
import { Allocation, Asset, Client, Movement } from "@/lib/types";
import { formatCurrencyBRL } from "@/lib/utils";
import { toast } from "react-hot-toast";

async function fetchClients() {
  const response = await api.get<Client[]>("/clients", { params: { limit: 200 } });
  return response.data;
}

async function fetchAssets() {
  const response = await api.get<Asset[]>("/assets", { params: { limit: 200 } });
  return response.data;
}

async function fetchAllocations() {
  const response = await api.get<Allocation[]>("/allocations");
  return response.data;
}

async function fetchMovements() {
  const response = await api.get<Movement[]>("/movements");
  return response.data;
}

function monthKey(dateString: string) {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

const monthLabels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function formatMonthLabel(key: string) {
  const [year, month] = key.split("-");
  const index = Number(month) - 1;
  const label = monthLabels[index] ?? month;
  return `${label}/${year.slice(-2)}`;
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const monthParam = searchParams.get("month") ?? "all";
  const monthFilter = monthParam !== "all" ? monthParam : null;

  const { data: clients = [] } = useQuery({ queryKey: ["dashboard", "clients"], queryFn: fetchClients });
  const { data: assets = [] } = useQuery({ queryKey: ["dashboard", "assets"], queryFn: fetchAssets });
  const { data: allocations = [] } = useQuery({ queryKey: ["dashboard", "allocations"], queryFn: fetchAllocations });
  const { data: movements = [] } = useQuery({ queryKey: ["dashboard", "movements"], queryFn: fetchMovements });

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"todos" | "ativos" | "inativos">("todos");

  const filteredAllocations = useMemo(() => {
    if (!monthFilter) return allocations;
    return allocations.filter((allocation) => {
      const key = monthKey(allocation.buy_date);
      return key ? key.split("-")[1] === monthFilter : false;
    });
  }, [allocations, monthFilter]);

  const filteredMovements = useMemo(() => {
    if (!monthFilter) return movements;
    return movements.filter((movement) => {
      const key = monthKey(movement.date);
      return key ? key.split("-")[1] === monthFilter : false;
    });
  }, [movements, monthFilter]);

  const assetsMap = useMemo(() => {
    const map = new Map<number, Asset>();
    assets.forEach((asset) => map.set(asset.id, asset));
    return map;
  }, [assets]);

  const allocationTotalsByClient = useMemo(() => {
    const map = new Map<number, number>();
    filteredAllocations.forEach((allocation) => {
      const quantity = Number(allocation.quantity);
      const price = Number(allocation.buy_price);
      if (Number.isNaN(quantity) || Number.isNaN(price)) {
        return;
      }
      const current = map.get(allocation.client_id) ?? 0;
      map.set(allocation.client_id, current + quantity * price);
    });
    return map;
  }, [filteredAllocations]);

  const filteredClients = useMemo(() => {
    return clients.filter((client) => {
      const matchesSearch = search
        ? client.name.toLowerCase().includes(search.toLowerCase()) ||
          client.email.toLowerCase().includes(search.toLowerCase())
        : true;
      const matchesStatus =
        statusFilter === "todos" ||
        (statusFilter === "ativos" && client.is_active) ||
        (statusFilter === "inativos" && !client.is_active);
      return matchesSearch && matchesStatus;
    });
  }, [clients, search, statusFilter]);

  const clientRows = filteredClients.map((client) => ({
    id: client.id,
    name: client.name,
    email: client.email,
    is_active: client.is_active,
    total_allocation: formatCurrencyBRL(allocationTotalsByClient.get(client.id) ?? 0),
  }));

  const totalClients = clients.length;
  const totalActive = clients.filter((client) => client.is_active).length;

  const custodyData = useMemo(() => {
    const monthly = new Map<string, number>();
    filteredAllocations.forEach((allocation) => {
      const key = monthKey(allocation.buy_date);
      if (!key) return;
      const quantity = Number(allocation.quantity);
      const price = Number(allocation.buy_price);
      if (Number.isNaN(quantity) || Number.isNaN(price)) {
        return;
      }
      monthly.set(key, (monthly.get(key) ?? 0) + quantity * price);
    });
    const sortedKeys = Array.from(monthly.keys()).sort();
    let running = 0;
    return sortedKeys.map((key) => {
      running += monthly.get(key) ?? 0;
      return { label: formatMonthLabel(key), value: Number(running.toFixed(2)) };
    });
  }, [filteredAllocations]);

  const flowData = useMemo(() => {
    const monthly = new Map<string, { inflow: number; outflow: number }>();
    filteredMovements.forEach((movement) => {
      const key = monthKey(movement.date);
      if (!key) return;
      const amount = Number(movement.amount);
      if (Number.isNaN(amount)) {
        return;
      }
      const entry = monthly.get(key) ?? { inflow: 0, outflow: 0 };
      if (movement.type === "deposit") {
        entry.inflow += amount;
      } else {
        entry.outflow += amount;
      }
      monthly.set(key, entry);
    });
    const sortedKeys = Array.from(monthly.keys()).sort();
    return sortedKeys.map((key) => {
      const entry = monthly.get(key)!;
      return {
        label: formatMonthLabel(key),
        inflow: Number(entry.inflow.toFixed(2)),
        outflow: Number(entry.outflow.toFixed(2)),
      };
    });
  }, [filteredMovements]);

  const allocationMix = useMemo(() => {
    const byAsset = new Map<number, number>();
    filteredAllocations.forEach((allocation) => {
      const quantity = Number(allocation.quantity);
      const price = Number(allocation.buy_price);
      if (Number.isNaN(quantity) || Number.isNaN(price)) {
        return;
      }
      byAsset.set(allocation.asset_id, (byAsset.get(allocation.asset_id) ?? 0) + quantity * price);
    });
    return Array.from(byAsset.entries()).map(([assetId, value]) => {
      const asset = assetsMap.get(assetId);
      const label = asset ? `${asset.ticker} • ${asset.name}` : `Ativo ${assetId}`;
      return { name: label, value: Number(value.toFixed(2)) };
    });
  }, [filteredAllocations, assetsMap]);

  const totalInvested = useMemo(() => {
    return Array.from(allocationTotalsByClient.values()).reduce((acc, value) => acc + value, 0);
  }, [allocationTotalsByClient]);

  const movementSummary = useMemo(() => {
    return filteredMovements.reduce(
      (acc, movement) => {
        const amount = Number(movement.amount);
        if (Number.isNaN(amount)) {
          return acc;
        }
        if (movement.type === "deposit") {
          acc.deposits += amount;
          acc.net += amount;
        } else {
          acc.withdrawals += amount;
          acc.net -= amount;
        }
        return acc;
      },
      { deposits: 0, withdrawals: 0, net: 0 }
    );
  }, [filteredMovements]);

  const diffEnabled = !monthFilter;

  const lastCustody = custodyData[custodyData.length - 1]?.value ?? 0;
  const prevCustody = custodyData[custodyData.length - 2]?.value ?? lastCustody;
  const custodyDiff = diffEnabled && prevCustody > 0 ? ((lastCustody - prevCustody) / prevCustody) * 100 : 0;

  const lastFlow = flowData[flowData.length - 1];
  const prevFlow = flowData[flowData.length - 2];
  const lastInflow = diffEnabled ? lastFlow?.inflow ?? 0 : movementSummary.deposits;
  const prevInflow = diffEnabled ? prevFlow?.inflow ?? lastInflow : 0;
  const inflowDiff = diffEnabled && prevInflow > 0 ? ((lastInflow - prevInflow) / prevInflow) * 100 : 0;

  const lastNet = diffEnabled ? (lastFlow ? lastFlow.inflow - lastFlow.outflow : 0) : movementSummary.net;
  const prevNet = diffEnabled && prevFlow ? prevFlow.inflow - prevFlow.outflow : lastNet;
  const netDiff = diffEnabled && prevNet !== 0 ? ((lastNet - prevNet) / Math.abs(prevNet)) * 100 : 0;

  const kpis = [
    {
      title: "Clientes ativos",
      value: `${totalActive}/${totalClients}`,
      difference: totalClients ? (totalActive / totalClients) * 100 : 0,
    },
    {
      title: "Total investido",
      value: formatCurrencyBRL(totalInvested),
      difference: custodyDiff,
    },
    {
      title: diffEnabled ? "Entradas do mês" : "Entradas no período",
      value: formatCurrencyBRL(lastInflow),
      difference: inflowDiff,
    },
    {
      title: diffEnabled ? "Saldo líquido" : "Saldo líquido do período",
      value: formatCurrencyBRL(movementSummary.net),
      difference: netDiff,
    },
  ];

  const handleExportClients = async () => {
    try {
      const response = await api.get("/export/clients", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "clientes.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Exportação de clientes gerada");
    } catch (error) {
      toast.error("Falha ao exportar clientes");
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((metric) => (
          <KpiCard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            difference={Math.round(metric.difference)}
          />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <CustodyChart data={custodyData} />
        <FlowChart data={flowData} />
        <AllocationChart data={allocationMix} />
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle>Clientes</CardTitle>
            <CardDescription>
              Base completa com filtros rápidos para localizar clientes e analisar alocação total.
            </CardDescription>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="Buscar por nome ou e-mail"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <select
              className="h-10 rounded-md border border-border bg-surface px-3 text-sm text-foreground"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
            >
              <option value="todos">Todos</option>
              <option value="ativos">Ativos</option>
              <option value="inativos">Inativos</option>
            </select>
            <Button variant="outline" onClick={handleExportClients}>
              Exportar CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ClientsTable data={clientRows} />
        </CardContent>
      </Card>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="space-y-6">Carregando dados...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
