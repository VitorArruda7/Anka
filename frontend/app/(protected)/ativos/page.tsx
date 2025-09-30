"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";

import { api } from "@/lib/axios";
import { Asset } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const manualAssetSchema = z.object({
  ticker: z.string().min(1, { message: "Informe o ticker" }),
  name: z.string().min(2, { message: "Informe o nome do ativo" }),
  exchange: z.string().min(2, { message: "Informe a bolsa" }),
  currency: z.string().min(1, { message: "Informe a moeda" }),
});

type ManualAssetFormValues = z.infer<typeof manualAssetSchema>;

async function fetchAssets() {
  const response = await api.get<Asset[]>("/assets", { params: { limit: 200 } });
  return response.data;
}

async function importAsset(ticker: string) {
  const response = await api.post<Asset>(`/assets/fetch/${ticker}`);
  return response.data;
}

async function createAsset(payload: ManualAssetFormValues) {
  const response = await api.post<Asset>("/assets", payload);
  return response.data;
}

export default function AtivosPage() {
  const queryClient = useQueryClient();
  const [tickerSearch, setTickerSearch] = useState("");

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ["ativos"],
    queryFn: fetchAssets,
  });

  const manualForm = useForm<ManualAssetFormValues>({
    resolver: zodResolver(manualAssetSchema),
    defaultValues: { ticker: "", name: "", exchange: "", currency: "BRL" },
  });

  const importMutation = useMutation({
    mutationFn: importAsset,
    onSuccess: (asset) => {
      queryClient.invalidateQueries({ queryKey: ["ativos"] });
      setTickerSearch("");
      toast.success(`Ativo ${asset.ticker} importado`);
    },
    onError: () => toast.error("Não foi possível buscar o ticker informado"),
  });

  const manualMutation = useMutation({
    mutationFn: createAsset,
    onSuccess: (asset) => {
      queryClient.invalidateQueries({ queryKey: ["ativos"] });
      toast.success(`Ativo ${asset.ticker} cadastrado`);
      manualForm.reset({ ticker: "", name: "", exchange: "", currency: "BRL" });
    },
    onError: () => toast.error("Não foi possível cadastrar o ativo"),
  });

  const handleImport = () => {
    if (!tickerSearch.trim()) {
      toast.error("Informe um ticker para buscar");
      return;
    }
    importMutation.mutate(tickerSearch.trim().toUpperCase());
  };

  const onManualSubmit = manualForm.handleSubmit((values) => {
    manualMutation.mutate({
      ticker: values.ticker.toUpperCase(),
      name: values.name,
      exchange: values.exchange,
      currency: values.currency.toUpperCase(),
    });
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Importar ativo pelo ticker</CardTitle>
          <CardDescription>
            Consulte a API do Yahoo Finance para trazer os dados principais do ativo.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Label htmlFor="ticker">Ticker</Label>
            <Input
              id="ticker"
              placeholder="Ex.: PETR4.SA"
              value={tickerSearch}
              onChange={(event) => setTickerSearch(event.target.value.toUpperCase())}
              className="mt-2"
            />
          </div>
          <Button onClick={handleImport} disabled={importMutation.isPending}>
            {importMutation.isPending ? "Buscando..." : "Importar"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cadastro manual</CardTitle>
          <CardDescription>Preencha os campos para registrar um ativo que não esteja disponível via API.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-4" onSubmit={onManualSubmit}>
            <div>
              <Label htmlFor="manual-ticker">Ticker</Label>
              <Input
                id="manual-ticker"
                placeholder="Ticker"
                {...manualForm.register("ticker")}
                className="mt-2"
              />
              {manualForm.formState.errors.ticker && (
                <p className="mt-1 text-sm text-negative">{manualForm.formState.errors.ticker.message}</p>
              )}
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="manual-name">Nome</Label>
              <Input
                id="manual-name"
                placeholder="Nome do ativo"
                {...manualForm.register("name")}
                className="mt-2"
              />
              {manualForm.formState.errors.name && (
                <p className="mt-1 text-sm text-negative">{manualForm.formState.errors.name.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="manual-currency">Moeda</Label>
              <Input
                id="manual-currency"
                placeholder="BRL"
                {...manualForm.register("currency")}
                className="mt-2"
              />
              {manualForm.formState.errors.currency && (
                <p className="mt-1 text-sm text-negative">{manualForm.formState.errors.currency.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="manual-exchange">Bolsa</Label>
              <Input
                id="manual-exchange"
                placeholder="B3"
                {...manualForm.register("exchange")}
                className="mt-2"
              />
              {manualForm.formState.errors.exchange && (
                <p className="mt-1 text-sm text-negative">{manualForm.formState.errors.exchange.message}</p>
              )}
            </div>
            <div className="md:col-span-3 flex items-end">
              <Button type="submit" disabled={manualForm.formState.isSubmitting || manualMutation.isPending}>
                {manualMutation.isPending ? "Salvando..." : "Salvar ativo"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ativos cadastrados</CardTitle>
          <CardDescription>{assets.length} ativo(s) disponíveis para alocação</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticker</TableHead>
                <TableHead>Nome</TableHead>
                <TableHead>Bolsa</TableHead>
                <TableHead>Moeda</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted">
                    Carregando ativos...
                  </TableCell>
                </TableRow>
              ) : assets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted">
                    Nenhum ativo cadastrado até o momento.
                  </TableCell>
                </TableRow>
              ) : (
                assets.map((asset) => (
                  <TableRow key={asset.id}>
                    <TableCell className="font-semibold">{asset.ticker}</TableCell>
                    <TableCell>{asset.name}</TableCell>
                    <TableCell>{asset.exchange}</TableCell>
                    <TableCell>{asset.currency}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
