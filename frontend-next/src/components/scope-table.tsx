"use client";

import { Trash2 } from "lucide-react";
import { useT } from "@/lib/i18n";
import type { ScopeRow } from "@/lib/api";
import { Button } from "@/components/ui/button";

/** The PTS scope table, laid out like the estimation engineer's reference
 * sheet (SL # / Area / Type of system required as per PTS). Every cell is
 * editable so the engineer can correct the model's output before saving
 * and approving it into the reference library. */
export function ScopeTable({
  rows,
  onChange,
}: {
  rows: ScopeRow[];
  onChange: (rows: ScopeRow[]) => void;
}) {
  const t = useT();

  function updateCell(index: number, field: keyof ScopeRow, value: string) {
    onChange(rows.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  function deleteRow(index: number) {
    onChange(rows.filter((_, i) => i !== index));
  }

  function addRow() {
    onChange([...rows, { area: "", system: "" }]);
  }

  const cell = "border border-border px-2 py-1 align-top";
  const input =
    "w-full bg-transparent text-sm text-text-primary outline-none focus:bg-bg-elevated-2 rounded-[var(--radius-sm)] px-1 py-0.5";

  return (
    <div className="space-y-2">
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse" dir="ltr">
          <thead>
            <tr className="bg-info/15">
              <th className={`${cell} text-start font-normal text-text-primary w-14`}>{t.projects_col_sl}</th>
              <th className={`${cell} text-start font-normal text-text-primary`}>{t.projects_col_area}</th>
              <th className={`${cell} text-start font-normal text-text-primary`}>{t.projects_col_system}</th>
              <th className="w-10" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <td className={`${cell} text-text-secondary`}>{i + 1}</td>
                <td className={cell}>
                  <input
                    className={input}
                    value={row.area}
                    onChange={(e) => updateCell(i, "area", e.target.value)}
                  />
                </td>
                <td className={cell}>
                  <input
                    className={input}
                    value={row.system}
                    onChange={(e) => updateCell(i, "system", e.target.value)}
                  />
                </td>
                <td className="px-1 align-top">
                  <button
                    type="button"
                    onClick={() => deleteRow(i)}
                    title={t.projects_delete_row}
                    className="p-1 text-text-muted hover:text-danger"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <p className="text-sm text-text-muted">{t.projects_scope_empty}</p>}
      <Button size="sm" variant="ghost" onClick={addRow}>
        {t.projects_add_row}
      </Button>
    </div>
  );
}
