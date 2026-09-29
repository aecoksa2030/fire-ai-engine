"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/** Plain native <select>, styled — simpler and perfectly accessible for
 * short option lists (provider, report type, role). Reach for the
 * installed @radix-ui/react-select primitive instead if a screen later
 * needs a searchable/custom-rendered dropdown. */
export const SelectNative = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-9 w-full rounded-[var(--radius-sm)] border border-border bg-bg-elevated-2 px-2.5 text-sm text-text-primary",
        "focus-visible:outline-none focus-visible:border-accent focus-visible:ring-1 focus-visible:ring-accent",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
);
SelectNative.displayName = "SelectNative";
