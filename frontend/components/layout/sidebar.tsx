"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BarChart, Users, Briefcase, Wallet, FileDown, Home } from "lucide-react";

type NavLink = {
  href: string;
  label: string;
  icon: typeof Home;
};

const links: NavLink[] = [
  { href: "/dashboard", label: "Painel", icon: Home },
  { href: "/clientes", label: "Clientes", icon: Users },
  { href: "/ativos", label: "Ativos", icon: Briefcase },
  { href: "/alocacoes", label: "Alocações", icon: BarChart },
  { href: "/movimentacoes", label: "Movimentações", icon: Wallet },
  { href: "/exportacoes", label: "Exportações", icon: FileDown },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-border bg-surface/95 p-6 backdrop-blur lg:flex">
      <div className="mb-8 text-xl font-semibold text-foreground">Anka Investimentos</div>
      <nav className="flex flex-1 flex-col gap-2">
        {links.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition",
                isActive
                  ? "bg-foreground/10 text-foreground"
                  : "text-muted hover:bg-surface-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
