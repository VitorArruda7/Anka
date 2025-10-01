"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";

import { api } from "@/lib/axios";
import { Client, PaginatedResponse, PaginationMeta } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PaginationControls } from "@/components/ui/pagination";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const clientFormSchema = z.object({
  name: z.string().min(2, { message: "Informe pelo menos 2 caracteres" }),
  email: z.string().email({ message: "Informe um e-mail válido" }),
  is_active: z.boolean(),
});

type ClientFormValues = z.infer<typeof clientFormSchema>;
type StatusFilter = "todos" | "ativos" | "inativos";

async function fetchClients(search: string, status: StatusFilter, page: number, pageSize: number) {
  const params: Record<string, string | number | boolean> = {
    page,
    page_size: pageSize,
  };
  if (search) {
    params.search = search;
  }
  if (status !== "todos") {
    params.is_active = status === "ativos";
  }
  const response = await api.get<PaginatedResponse<Client>>("/clients", { params });
  return response.data;
}

async function createClient(payload: ClientFormValues) {
  const response = await api.post<Client>("/clients", payload);
  return response.data;
}

async function updateClient(id: number, payload: ClientFormValues) {
  const response = await api.put<Client>(`/clients/${id}`, payload);
  return response.data;
}

async function deleteClient(id: number) {
  await api.delete(`/clients/${id}`);
}

export default function ClientesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("todos");
  const [editingClient, setEditingClient] = useState<Client | null>(null);

  const pageSize = 20;
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter]);

  const clientsQuery = useQuery({
    queryKey: ["clientes", search, statusFilter, page, pageSize],
    queryFn: () => fetchClients(search, statusFilter, page, pageSize),
  });

  const activeCountQuery = useQuery({
    queryKey: ["clientes", "ativos-total", search],
    queryFn: () => fetchClients(search, "ativos", 1, 1),
    enabled: statusFilter === "todos",
  });

  const clients = clientsQuery.data?.items ?? [];
  const meta: PaginationMeta = clientsQuery.data?.meta ?? { total: 0, page, page_size: pageSize, pages: 0 };
  const isLoading = clientsQuery.isLoading;
  const isFetching = clientsQuery.isFetching;

  const {
    control,
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ClientFormValues>({
    resolver: zodResolver(clientFormSchema),
    defaultValues: { name: "", email: "", is_active: true },
  });

  useEffect(() => {
    if (editingClient) {
      setValue("name", editingClient.name);
      setValue("email", editingClient.email);
      setValue("is_active", editingClient.is_active);
    } else {
      reset({ name: "", email: "", is_active: true });
    }
  }, [editingClient, reset, setValue]);

  const createMutation = useMutation({
    mutationFn: createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clientes"] });
      toast.success("Cliente criado com sucesso");
      setEditingClient(null);
      reset({ name: "", email: "", is_active: true });
    },
    onError: () => toast.error("Não foi possível criar o cliente"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ClientFormValues }) => updateClient(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clientes"] });
      toast.success("Cliente atualizado com sucesso");
      setEditingClient(null);
      reset({ name: "", email: "", is_active: true });
    },
    onError: () => toast.error("Não foi possível atualizar o cliente"),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clientes"] });
      toast.success("Cliente removido");
    },
    onError: () => toast.error("Não foi possível remover o cliente"),
  });

  const onSubmit = async (values: ClientFormValues) => {
    if (editingClient) {
      await updateMutation.mutateAsync({ id: editingClient.id, payload: values });
    } else {
      await createMutation.mutateAsync(values);
    }
  };

  const totalAtivos = useMemo(() => {
    if (statusFilter === "inativos") {
      return 0;
    }
    if (statusFilter === "ativos") {
      return meta.total;
    }
    return activeCountQuery.data?.meta.total ?? 0;
  }, [statusFilter, meta.total, activeCountQuery.data?.meta.total]);

  const handlePageChange = (nextPage: number) => {
    if (meta.pages === 0) {
      setPage(1);
      return;
    }
    const normalized = Math.min(Math.max(nextPage, 1), meta.pages);
    setPage(normalized);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{editingClient ? "Editar cliente" : "Novo cliente"}</CardTitle>
          <CardDescription>
            {editingClient
              ? "Atualize os dados do cliente selecionado."
              : "Cadastre um novo cliente para iniciar o relacionamento."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
            <div className="md:col-span-1">
              <Label htmlFor="name">Nome</Label>
              <Input id="name" placeholder="Nome completo" {...register("name")}
                className="mt-2" />
              {errors.name && <p className="mt-1 text-sm text-negative">{errors.name.message}</p>}
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="email">E-mail</Label>
              <Input id="email" type="email" placeholder="contato@empresa.com" {...register("email")} className="mt-2" />
              {errors.email && <p className="mt-1 text-sm text-negative">{errors.email.message}</p>}
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="status">Status</Label>
              <Controller
                control={control}
                name="is_active"
                render={({ field }) => (
                  <select
                    id="status"
                    className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
                    value={field.value ? "true" : "false"}
                    onChange={(event) => field.onChange(event.target.value === "true")}
                  >
                    <option value="true">
                      Ativo
                    </option>
                    <option value="false">
                      Inativo
                    </option>
                  </select>
                )}
              />
            </div>
            <div className="flex items-end gap-2 md:col-span-1">
              <Button type="submit" disabled={isSubmitting || createMutation.isPending || updateMutation.isPending}>
                {editingClient ? "Salvar alterações" : "Cadastrar"}
              </Button>
              {editingClient && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditingClient(null)}
                  disabled={isSubmitting}
                >
                  Cancelar
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Clientes cadastrados</CardTitle>
          <CardDescription>
            {clients.length} cliente(s) encontrados • {totalAtivos} ativos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="md:col-span-1">
              <Label htmlFor="busca">Busca</Label>
              <Input
                id="busca"
                placeholder="Pesquisar por nome ou e-mail"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="mt-2"
              />
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="filtro-status">Filtrar status</Label>
              <select
                id="filtro-status"
                className="mt-2 h-10 w-full rounded-md border border-border bg-surface px-3 text-sm text-foreground"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              >
                <option value="todos">
                  Todos
                </option>
                <option value="ativos">
                  Apenas ativos
                </option>
                <option value="inativos">
                  Apenas inativos
                </option>
              </select>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Criado em</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted">
                    Carregando clientes...
                  </TableCell>
                </TableRow>
              ) : clients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted">
                    Nenhum cliente encontrado.
                  </TableCell>
                </TableRow>
              ) : (
                clients.map((client) => (
                  <TableRow key={client.id}>
                    <TableCell>{client.name}</TableCell>
                    <TableCell className="text-muted">{client.email}</TableCell>
                    <TableCell>
                      <Badge variant={client.is_active ? "success" : "danger"}>
                        {client.is_active ? "Ativo" : "Inativo"}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(client.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm" onClick={() => setEditingClient(client)}>
                          Editar
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const confirmed = window.confirm("Deseja remover este cliente?");
                            if (confirmed) {
                              deleteMutation.mutate(client.id);
                            }
                          }}
                        >
                          Remover
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
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
