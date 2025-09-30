"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAuth } from "@/hooks/use-auth";
import { useMemo } from "react";

const monthOptions = [
  { label: "Período completo", value: "all" },
  { label: "Jan", value: "01" },
  { label: "Fev", value: "02" },
  { label: "Mar", value: "03" },
  { label: "Abr", value: "04" },
  { label: "Mai", value: "05" },
  { label: "Jun", value: "06" },
  { label: "Jul", value: "07" },
  { label: "Ago", value: "08" },
  { label: "Set", value: "09" },
  { label: "Out", value: "10" },
  { label: "Nov", value: "11" },
  { label: "Dez", value: "12" },
];

export function DashboardHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { logout } = useAuth();

  const currentMonth = searchParams.get("month") ?? "all";

  const monthSelectOptions = useMemo(() => monthOptions, []);

  const updateMonth = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "all") {
      params.delete("month");
    } else {
      params.set("month", value);
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  return (
    <header className="flex items-center justify-end gap-3">
      <select
        aria-label="Filtrar mês de referência"
        className="h-10 rounded-md border border-border bg-surface px-3 text-sm text-foreground"
        value={currentMonth}
        onChange={(event) => updateMonth(event.target.value)}
      >
        {monthSelectOptions.map((option) => (
          <option key={option.value} value={option.value} className="text-foreground">
            {option.label}
          </option>
        ))}
      </select>
      <ThemeToggle />
      <Button
        variant="outline"
        onClick={() => {
          logout();
          router.push("/login");
        }}
      >
        Sair
      </Button>
    </header>
  );
}
