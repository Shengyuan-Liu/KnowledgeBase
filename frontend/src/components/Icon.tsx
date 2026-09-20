import type { CSSProperties } from "react";

const paths = {
  book: "M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4V4Zm16 0h-4a3 3 0 0 0-3 3m0 14a4 4 0 0 1 4-2h3V4Z",
  file: "M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8M8 16h6",
  upload: "M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6",
  search: "m20 20-5-5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z",
  close: "m6 6 12 12M6 18 18 6",
  arrow: "M12 20V4m-6 6 6-6 6 6",
  quote: "M10 6H4v7h5c0 3-2 5-5 5m16-12h-6v7h5c0 3-2 5-5 5",
  trash: "M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7",
};

export function Icon({
  name,
  size = 20,
  style,
}: {
  name: keyof typeof paths;
  size?: number;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={paths[name]} />
    </svg>
  );
}
