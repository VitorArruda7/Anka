"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "react-hot-toast";
import { api } from "@/lib/axios";

async function downloadCsv(path: string, filename: string) {
  const response = await api.get(path, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export default function ExportacoesPage() {
  const [loading, setLoading] = useState<"clients" | "allocations" | "movements" | null>(null);

  const handleDownload = async (key: typeof loading, path: string, filename: string, label: string) => {
    try {
      setLoading(key);
      await downloadCsv(path, filename);
      toast.success(`${label} exportado(a) com sucesso`);
    } catch (error) {
      toast.error(`Não foi possível exportar ${label.toLowerCase()}`);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Exportações operacionais</CardTitle>
          <CardDescription>
            Gere relatórios em CSV para analisar clientes, alocações e movimentações fora da plataforma.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Card className="space-y-3">
            <CardHeader>
              <CardTitle>Clientes</CardTitle>
              <CardDescription>Inclui identificação, e-mail, status e data de criação.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => handleDownload("clients", "/export/clients", "clientes.csv", "Clientes")}
                disabled={loading === "clients"}
              >
                {loading === "clients" ? "Gerando..." : "Exportar clientes"}
              </Button>
            </CardContent>
          </Card>

          <Card className="space-y-3">
            <CardHeader>
              <CardTitle>Alocações</CardTitle>
              <CardDescription>Volume investido por cliente e ativo com data de compra.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => handleDownload("allocations", "/export/allocations", "alocacoes.csv", "Alocações")}
                disabled={loading === "allocations"}
              >
                {loading === "allocations" ? "Gerando..." : "Exportar alocações"}
              </Button>
            </CardContent>
          </Card>

          <Card className="space-y-3">
            <CardHeader>
              <CardTitle>Movimentações</CardTitle>
              <CardDescription>Depósitos e resgates, com valor e observações por cliente.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => handleDownload("movements", "/export/movements", "movimentacoes.csv", "Movimentações")}
                disabled={loading === "movements"}
              >
                {loading === "movements" ? "Gerando..." : "Exportar movimentações"}
              </Button>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  );
}
