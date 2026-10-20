import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** 合并 className：clsx + tailwind-merge，避免 Tailwind 类冲突。 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
