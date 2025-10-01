"use client";

import { Button } from "@/components/ui/button";
import type { PaginationMeta } from "@/lib/types";

type PaginationControlsProps = {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
};

export function PaginationControls({ meta, onPageChange, isLoading }: PaginationControlsProps) {
  const { page, pages, total } = meta;
  const hasPrev = page > 1;
  const hasNext = pages === 0 ? false : page < pages;

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-muted">
        {pages > 0
          ? `Pagina ${page} de ${pages} (total ${total})`
          : total === 0
          ? "Nenhum registro encontrado"
          : `Exibindo ${total} registro${total > 1 ? "s" : ""}`}
      </p>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={!hasPrev || isLoading}
        >
          Anterior
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext || isLoading}
        >
          Proxima
        </Button>
      </div>
    </div>
  );
}
