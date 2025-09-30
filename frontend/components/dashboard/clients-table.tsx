import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface ClientRow {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  total_allocation: string;
}

interface ClientsTableProps {
  data: ClientRow[];
}

export function ClientsTable({ data }: ClientsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Cliente</TableHead>
          <TableHead>E-mail</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Total alocado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((client) => (
          <TableRow key={client.id}>
            <TableCell>{client.name}</TableCell>
            <TableCell className="text-muted">{client.email}</TableCell>
            <TableCell>
              <Badge variant={client.is_active ? "success" : "danger"}>
                {client.is_active ? "Ativo" : "Inativo"}
              </Badge>
            </TableCell>
            <TableCell>{client.total_allocation}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
