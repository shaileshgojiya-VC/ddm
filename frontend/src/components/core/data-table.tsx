import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import NoDataFound from "@/components/core/no-data-found";

export interface Column<T> {
  /** Column header label */
  header: string;
  /** Function to render cell content */
  cell: (row: T) => ReactNode;
  /** Optional className for header cell */
  headerClassName?: string;
  /** Optional className for body cells in this column */
  cellClassName?: string;
}

export interface DataTableProps<T> {
  /** Array of data objects */
  readonly data: T[];
  /** Column definitions */
  readonly columns: Column<T>[];
  /** Function to get unique key for each row */
  readonly getRowKey: (row: T) => string | number;
  /** Optional className for the Card wrapper */
  readonly cardClassName?: string;
  /** Optional className for the table */
  readonly tableClassName?: string;
  /** Optional function to get custom className for each row */
  readonly getRowClassName?: (row: T) => string;
  /** Whether to show the Card wrapper (default: true) */
  readonly withCard?: boolean;
  /** Optional className for table header */
  readonly headerClassName?: string;
  /** Optional custom empty state message */
  readonly emptyMessage?: string;
}

export default function DataTable<T>({
  data,
  columns,
  getRowKey,
  cardClassName,
  tableClassName,
  getRowClassName,
  withCard = true,
  headerClassName = "bg-slate-100",
  emptyMessage = "No data found",
}: DataTableProps<T>) {
  const tableContent = (
    <Table className={tableClassName}>
      <TableHeader className={headerClassName}>
        <TableRow>
          {columns?.map((column) => (
            <TableHead key={column?.header} className={column?.headerClassName}>
              {column?.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {!data || data?.length === 0 ? (
          <TableRow>
            <TableCell colSpan={columns?.length} className="text-center p-6">
              <NoDataFound title={emptyMessage} />
            </TableCell>
          </TableRow>
        ) : (
          <>
            {data?.map((row) => (
              <TableRow
                key={getRowKey(row)}
                className={cn("hover:bg-muted/50", getRowClassName?.(row))}
              >
                {columns?.map((column) => (
                  <TableCell
                    key={column?.header}
                    className={column?.cellClassName}
                  >
                    {column?.cell(row)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </>
        )}
      </TableBody>
    </Table>
  );

  if (withCard) {
    return (
      <Card className={cn("py-0 overflow-hidden", cardClassName)}>
        {tableContent}
      </Card>
    );
  }

  return tableContent;
}
