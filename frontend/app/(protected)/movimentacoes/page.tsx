"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";

import { api } from "@/lib/axios";
import { Client, Movement, PaginatedResponse, PaginationMeta } from "@/lib/types";
import { formatCurrencyBRL, formatDate } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaginationControls } from "@/components/ui/pagination";

const movementSchema = z.object({
  client_id: z.coerce.number({ invalid_type_error: "Selecione um cliente" }),
  type: z.enum(["deposit", "withdrawal"], {
    required_error: "Selecione o tipo de movimento",
  }),
  amount: z.coerce
    .number({ invalid_type_error: "Informe um valor" })
    .positive({ message: "O valor deve ser maior que zero" }),
  date: z.string().min(1, { message: "Informe a data" }),
  note: z.string().optional(),
});

type MovementFormValues = z.infer<typeof movementSchema>;

const EMPTY_MOVEMENTS: Movement[] = [];

async function fetchClients() {
  const response = await api.get<PaginatedResponse<Client>>("/clients", { params: { page: 1, page_size: 200 } });
  return response.data.items;
}

async function fetchMovements(
  clientId: number | "todos",
  startDate: string,
  endDate: string,
  page: number,
  pageSize: number
) {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  };
  if (clientId !== "todos") {
    params.client_id = clientId;
  }
  if (startDate) {
    params.start_date = startDate;
  }
  if (endDate) {
    params.end_date = endDate;
  }
  const response = await api.get<PaginatedResponse<Movement>>("/movements", { params });
  return response.data;
}

async function createMovement(payload: MovementFormValues) {
  const response = await api.post<Movement>("/movements", payload);
  return response.data;
}

async function deleteMovement(id: number) {
  await api.delete(`/movements/${id}`);
}

export default function MovimentacoesPage() {
  const queryClient = useQueryClient();
  const [clientFilter, setClientFilter] = useState<number | "todos">("todos");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const pageSize = 20;
  const [page, setPage] = useState(1);

  const clientsQuery = useQuery({ queryKey: ["clientes", "select"], queryFn: fetchClients });

  useEffect(() => {
    setPage(1);
  }, [clientFilter, startDate, endDate]);

  const movementsQuery = useQuery({
    queryKey: ["movimentacoes", clientFilter, startDate, endDate, page, pageSize],
    queryFn: () => fetchMovements(clientFilter, startDate, endDate, page, pageSize),
  });

  const movements = movementsQuery.data?.items ?? EMPTY_MOVEMENTS;
  const meta: PaginationMeta = movementsQuery.data?.meta ?? { total: 0, page, page_size: pageSize, pages: 0 };
  const isLoading = movementsQuery.isLoading;
  const isFetching = movementsQuery.isFetching;

  const handlePageChange = (nextPage: number) => {
    if (meta.pages === 0) {
      setPage(1);
      return;
    }
    const normalized = Math.min(Math.max(nextPage, 1), meta.pages);
    setPage(normalized);
  };

  const form = useForm<MovementFormValues>({
    resolver: zodResolver(movementSchema),
    defaultValues: {
      client_id: 0,
      type: "deposit",
      amount: 0,
      date: "",
      note: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: createMovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movimentacoes"] });
      toast.success("Movimentação registrada");
      form.reset({ client_id: 0, type: "deposit", amount: 0, date: "", note: "" });
    },
    onError: () => toast.error("Não foi possível registrar a movimentação"),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movimentacoes"] });
      toast.success("Movimentação removida");
    },
    onError: () => toast.error("Não foi possível remover a movimentação"),
  });

  const onSubmit = form.handleSubmit((values) => {
    if (values.client_id === 0) {
      toast.error("Selecione um cliente válido");
      return;
    }
    createMutation.mutate(values);
  });

  const clients = useMemo(() => clientsQuery.data ?? [], [clientsQuery.data]);
  const clientsMap = useMemo(() => {
    const map = new Map<number, Client>();
    clients.forEach((client) => map.set(client.id, client));
    return map;
  }, [clients]);

  const summary = useMemo(() => {
    return movements.reduce(
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
  }, [movements]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Nova movimentação</CardTitle>
          <CardDescription>Registre entradas e saídas de recursos por cliente.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-6" onSubmit={onSubmit}>
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
            <div>
              <Label htmlFor="tipo">Tipo</Label>
              <select
                id="tipo"
                className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
                {...form.register("type")}
              >
                <option value="deposit">
                  Entrada
                </option>
                <option value="withdrawal">
                  Saída
                </option>
              </select>
            </div>
            <div>
              <Label htmlFor="valor">Valor</Label>
              <Input id="valor" type="number" step="0.01" className="mt-2" {...form.register("amount")} />
              {form.formState.errors.amount && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.amount.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="data">Data</Label>
              <Input id="data" type="date" className="mt-2" {...form.register("date")} />
              {form.formState.errors.date && (
                <p className="mt-1 text-sm text-negative">{form.formState.errors.date.message}</p>
              )}
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="nota">Observação</Label>
              <Input id="nota" placeholder="Opcional" className="mt-2" {...form.register("note")} />
            </div>
            <div className="md:col-span-6 flex items-end">
              <Button type="submit" disabled={form.formState.isSubmitting || createMutation.isPending}>
                {createMutation.isPending ? "Registrando..." : "Registrar movimentação"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Resumo de captação</CardTitle>
          <CardDescription>
            Entradas: {formatCurrencyBRL(summary.deposits)} • Saídas: {formatCurrencyBRL(summary.withdrawals)} • Saldo líquido: {formatCurrencyBRL(summary.net)}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-4">
          <div>
            <Label htmlFor="filtro-cliente">Cliente</Label>
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
          <div>
            <Label htmlFor="inicio">Data inicial</Label>
            <Input
              id="inicio"
              type="date"
              className="mt-2"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="fim">Data final</Label>
            <Input
              id="fim"
              type="date"
              className="mt-2"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setClientFilter("todos");
                setStartDate("");
                setEndDate("");
              }}
            >
              Limpar filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Movimentações registradas</CardTitle>
          <CardDescription>{movements.length} lançamento(s) encontrado(s)</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Valor</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Observação</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted">
                    Carregando movimentações...
                  </TableCell>
                </TableRow>
              ) : movements.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted">
                    Nenhuma movimentação encontrada.
                  </TableCell>
                </TableRow>
              ) : (
                movements.map((movement) => {
                  const amount = Number(movement.amount);
                  const client = clientsMap.get(movement.client_id);
                  return (
                    <TableRow key={movement.id}>
                      <TableCell>{client?.name ?? movement.client_id}</TableCell>
                      <TableCell className={movement.type === "deposit" ? "text-positive" : "text-negative"}>
                        {movement.type === "deposit" ? "Entrada" : "Saída"}
                      </TableCell>
                      <TableCell>{formatCurrencyBRL(amount)}</TableCell>
                      <TableCell>{formatDate(movement.date)}</TableCell>
                      <TableCell>{movement.note ?? "-"}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const confirmed = window.confirm("Deseja remover esta movimentação?");
                            if (confirmed) {
                              deleteMutation.mutate(movement.id);
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
