import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Standard shadcn-style classname combinator: clsx for conditional
 * classes, tailwind-merge to resolve conflicting Tailwind utility
 * classes (e.g. "p-2 p-4" -> "p-4") instead of shipping both. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
