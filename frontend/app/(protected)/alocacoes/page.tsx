"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";

import { api } from "@/lib/axios";
import { Allocation, Asset, Client, PaginatedResponse, PaginationMeta } from "@/lib/types";
import { formatCurrencyBRL, formatDate } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaginationControls } from "@/components/ui/pagination";

const allocationSchema = z.object({
  client_id: z.coerce.number({ invalid_type_error: "Selecione um cliente" }),
  asset_id: z.coerce.number({ invalid_type_error: "Selecione um ativo" }),
  quantity: z.coerce
    .number({ invalid_type_error: "Informe uma quantidade" })
    .positive({ message: "Quantidade deve ser maior que zero" }),
  buy_price: z.coerce
    .number({ invalid_type_error: "Informe o preço" })
    .positive({ message: "Preço deve ser maior que zero" }),
  buy_date: z.string().min(1, { message: "Informe a data de compra" }),
});

type AllocationFormValues = z.infer<typeof allocationSchema>;

const EMPTY_ALLOCATIONS: Allocation[] = [];

async function fetchClients() {
  const response = await api.get<PaginatedResponse<Client>>("/clients", { params: { page: 1, page_size: 200 } });
  return response.data.items;
}

async function fetchAssets() {
  const response = await api.get<PaginatedResponse<Asset>>("/assets", { params: { page: 1, page_size: 200 } });
  return response.data.items;
}

async function fetchAllocations(clientId: number | null, page: number, pageSize: number) {
  const params: Record<string, number> = {
    page,
    page_size: pageSize,
  };
  if (clientId) {
    params.client_id = clientId;
  }
  const response = await api.get<PaginatedResponse<Allocation>>("/allocations", { params });
  return response.data;
}

async function createAllocation(payload: AllocationFormValues) {
  const response = await api.post<Allocation>("/allocations", payload);
  return response.data;
}

async function deleteAllocation(id: number) {
  await api.delete(`/allocations/${id}`);
}

export default function AlocacoesPage() {
  const queryClient = useQueryClient();
  const [clientFilter, setClientFilter] = useState<number | "todos">("todos");

  const clientsQuery = useQuery({ queryKey: ["clientes", "select"], queryFn: fetchClients });
  const assetsQuery = useQuery({ queryKey: ["ativos", "select"], queryFn: fetchAssets });

  const pageSize = 20;
  const [page, setPage] = useState(1);

  const selectedClientId = clientFilter === "todos" ? null : Number(clientFilter);

  const allocationsQuery = useQuery({
    queryKey: ["alocacoes", selectedClientId, page, pageSize],
    queryFn: () => fetchAllocations(selectedClientId, page, pageSize),
  });

  const allocations = allocationsQuery.data?.items ?? EMPTY_ALLOCATIONS;
  const meta: PaginationMeta = allocationsQuery.data?.meta ?? { total: 0, page, page_size: pageSize, pages: 0 };
  const isLoading = allocationsQuery.isLoading;
  const isFetching = allocationsQuery.isFetching;

  const handlePageChange = (nextPage: number) => {
    if (meta.pages === 0) {
      setPage(1);
      return;
    }
    const normalized = Math.min(Math.max(nextPage, 1), meta.pages);
    setPage(normalized);
  };

  const form = useForm<AllocationFormValues>({
    resolver: zodResolver(allocationSchema),
    defaultValues: {
      client_id: 0,
      asset_id: 0,
      quantity: 0,
      buy_price: 0,
      buy_date: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: createAllocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alocacoes"] });
      queryClient.invalidateQueries({ queryKey: ["clientes"] });
      toast.success("Alocação registrada");
      form.reset({ client_id: 0, asset_id: 0, quantity: 0, buy_price: 0, buy_date: "" });
    },
    onError: () => toast.error("Não foi possível registrar a alocação"),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAllocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alocacoes"] });
      toast.success("Alocação removida");
    },
    onError: () => toast.error("Não foi possível remover a alocação"),
  });

  const onSubmit = form.handleSubmit((values) => {
    if (values.client_id === 0 || values.asset_id === 0) {
      toast.error("Selecione cliente e ativo válidos");
      return;
    }
    createMutation.mutate(values);
  });

  const clients = useMemo(() => clientsQuery.data ?? [], [clientsQuery.data]);
  const assets = useMemo(() => assetsQuery.data ?? [], [assetsQuery.data]);

  const clientsMap = useMemo(() => {
    const map = new Map<number, Client>();
    clients.forEach((client) => map.set(client.id, client));
    return map;
  }, [clients]);

  const assetsMap = useMemo(() => {
    const map = new Map<number, Asset>();
    assets.forEach((asset) => map.set(asset.id, asset));
    return map;
  }, [assets]);

  const totalInvested = useMemo(() => {
    return allocations.reduce((acc, allocation) => {
      const quantity = Number(allocation.quantity);
      const price = Number(allocation.buy_price);
      if (Number.isNaN(quantity) || Number.isNaN(price)) {
        return acc;
      }
      return acc + quantity * price;
    }, 0);
  }, [allocations]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Nova alocação</CardTitle>
          <CardDescription>Defina o ativo, o cliente e os detalhes da posição comprada.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-5" onSubmit={onSubmit}>
            <div className="md:col-span-2">
              <Label htmlFor="cliente">Cliente</Label>
              <select
                id="cliente"
                className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
                {...form.register("client_id")}
              >
                <option value={0}>
                  Selecione
                </option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
              {form.formState.errors.client_id && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.client_id.message}</p>
              )}
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="ativo">Ativo</Label>
              <select
                id="ativo"
                className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
                {...form.register("asset_id")}
              >
                <option value={0}>
                  Selecione
                </option>
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.ticker} • {asset.name}
                  </option>
                ))}
              </select>
              {form.formState.errors.asset_id && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.asset_id.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="data">Data</Label>
              <Input id="data" type="date" className="mt-2" {...form.register("buy_date")} />
              {form.formState.errors.buy_date && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.buy_date.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="quantidade">Quantidade</Label>
              <Input id="quantidade" type="number" step="0.01" className="mt-2" {...form.register("quantity")} />
              {form.formState.errors.quantity && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.quantity.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="preco">Preço de compra</Label>
              <Input id="preco" type="number" step="0.01" className="mt-2" {...form.register("buy_price")} />
              {form.formState.errors.buy_price && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.buy_price.message}</p>
              )}
            </div>
            <div className="md:col-span-5 flex items-end">
              <Button type="submit" disabled={form.formState.isSubmitting || createMutation.isPending}>
                {createMutation.isPending ? "Salvando..." : "Salvar alocação"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Alocações registradas</CardTitle>
          <CardDescription>
            Total investido: {formatCurrencyBRL(totalInvested)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="md:w-72">
            <Label htmlFor="filtro-cliente">Filtrar por cliente</Label>
            <select
              id="filtro-cliente"
              className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
              value={clientFilter}
              onChange={(event) => {
                const value = event.target.value;
                setClientFilter(value === "todos" ? "todos" : Number(value));
              }}
            >
              <option value="todos">
                Todos os clientes
              </option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Ativo</TableHead>
                <TableHead>Quantidade</TableHead>
                <TableHead>Preço</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Valor investido</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted">
                    Carregando alocações...
                  </TableCell>
                </TableRow>
              ) : allocations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted">
                    Nenhuma alocação registrada.
                  </TableCell>
                </TableRow>
              ) : (
                allocations.map((allocation) => {
                  const client = clientsMap.get(allocation.client_id);
                  const asset = assetsMap.get(allocation.asset_id);
                  const quantity = Number(allocation.quantity);
                  const price = Number(allocation.buy_price);
                  const invested = Number.isNaN(quantity) || Number.isNaN(price) ? 0 : quantity * price;

                  return (
                    <TableRow key={allocation.id}>
                      <TableCell>{client?.name ?? allocation.client_id}</TableCell>
                      <TableCell>{asset ? `${asset.ticker} • ${asset.name}` : allocation.asset_id}</TableCell>
                      <TableCell>{quantity}</TableCell>
                      <TableCell>{formatCurrencyBRL(price)}</TableCell>
                      <TableCell>{formatDate(allocation.buy_date)}</TableCell>
                      <TableCell>{formatCurrencyBRL(invested)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const confirmed = window.confirm("Deseja remover esta alocação?");
                            if (confirmed) {
                              deleteMutation.mutate(allocation.id);
                            }
                          }}
                        >
                          Remover
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
          <div className="pt-2">
            <PaginationControls meta={meta} onPageChange={handlePageChange} isLoading={isFetching} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
