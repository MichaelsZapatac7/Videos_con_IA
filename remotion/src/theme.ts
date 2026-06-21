export type RGB = [number, number, number];

export interface Segment {
  kind: 'welcome' | 'topic' | 'item' | 'outro';
  title: string;
  number?: string;
  tagline?: string;
  code?: boolean;      // si tagline es una línea de código (SQL)
  text: string;        // narración -> subtítulos
  audio?: string | null;
  durationInFrames: number;
  images: string[];
  accent: RGB;
}

export interface VideoProps {
  fps: number;
  channel: string;
  music?: string | null;
  segments: Segment[];
}

export const rgb = (c: RGB, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

export const FONT =
  "'DejaVu Sans', 'Arial', 'Helvetica Neue', system-ui, sans-serif";

// Palabras clave SQL que se resaltan en la tarjeta de código
export const SQL_KEYWORDS = new Set([
  'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'JOIN', 'ON', 'INNER',
  'LEFT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'OVER', 'PARTITION', 'AS',
  'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'QUALIFY', 'ROW_NUMBER',
  'RANK', 'DATE_TRUNC', 'EXTRACT', 'DESC', 'ASC', 'AND', 'OR', 'NOT', 'IN',
]);
