"use client";

import { useMemo, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { Maximize2, Minimize2, Search, Download, ArrowUpDown } from "lucide-react";
import { BoqComponent } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const columnHelper = createColumnHelper<BoqComponent>();

const columns = [
  columnHelper.accessor("name", { header: "Device / Component Name" }),
  columnHelper.accessor("count", { header: "Quantity" }),
  columnHelper.accessor("confidence", { header: "Confidence Level" }),
  columnHelper.accessor("supplier_type", { header: "Supplier Type" }),
  columnHelper.accessor("unit_cost_sar", {
    header: "Unit Cost (SAR)",
    cell: (info) => (info.getValue() != null ? `${info.getValue()!.toFixed(2)} SAR` : "—"),
  }),
  columnHelper.accessor("total_cost_sar", {
    header: "Total Cost (SAR)",
    cell: (info) => (info.getValue() != null ? `${info.getValue()!.toFixed(2)} SAR` : "—"),
  }),
  columnHelper.accessor("erp_item_code", { header: "ERP Item Code" }),
  columnHelper.accessor("erp_item_name", { header: "ERP Item Name" }),
  columnHelper.accessor("erp_moving_avg_cost", {
    header: "Moving Avg / TCO (SAR)",
    cell: (info) => (info.getValue() != null ? `${info.getValue()!.toFixed(2)} SAR` : "—"),
  }),
  columnHelper.accessor("erp_selling_price", {
    header: "Selling Price (SAR)",
    cell: (info) => (info.getValue() != null ? `${info.getValue()!.toFixed(2)} SAR` : "—"),
  }),
];

/** Real replacement for st.dataframe()'s built-in toolbar — sort, search,
 * CSV export, and fullscreen, all real DOM/React state we fully own, so
 * none of the Streamlit-session archaeology this session spent hours on
 * (canvas cells that can't be restyled, a toolbar clipped by our own
 * overflow:hidden, a fullscreen backdrop baked from config.toml) applies
 * here — every pixel of this table is normal, themeable HTML. */
export function BoqTable({ data }: { data: BoqComponent[] }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [fullscreen, setFullscreen] = useState(false);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "includesString",
  });

  function downloadCsv() {
    // Built straight from the filtered/sorted row model's own cells
    // (not by re-deriving accessor keys from the column defs) so this
    // always matches exactly what's on screen, search filter included.
    const headerRow = table.getFlatHeaders().map((h) => String(h.column.columnDef.header));
    const bodyRows = table.getFilteredRowModel().rows.map((row) =>
      row.getVisibleCells().map((cell) => {
        const v = cell.getValue();
        return v == null ? "" : String(v);
      })
    );
    const csv = [headerRow, ...bodyRows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "boq_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div
      className={cn(
        "rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated overflow-hidden",
        fullscreen && "fixed inset-4 z-50 flex flex-col shadow-2xl"
      )}
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border-subtle">
        <div className="relative w-56">
          <Search className="absolute start-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <Input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Search…"
            className="ps-7 h-8 text-xs"
          />
        </div>
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" onClick={downloadCsv} title="Download as CSV">
            <Download className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" onClick={() => setFullscreen((f) => !f)} title="Fullscreen">
            {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <div className={cn("overflow-auto", fullscreen ? "flex-1" : "max-h-[420px]")}>
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-bg-elevated-3 text-text-secondary">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="text-start px-3 py-2 font-medium whitespace-nowrap cursor-pointer select-none"
                  >
                    <span className="inline-flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <ArrowUpDown className="h-3 w-3 opacity-50" />
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-t border-border-subtle hover:bg-bg-elevated-2">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 whitespace-nowrap text-text-primary">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length === 0 && (
          <div className="p-6 text-center text-sm text-text-muted">No components detected.</div>
        )}
      </div>
    </div>
  );
}
