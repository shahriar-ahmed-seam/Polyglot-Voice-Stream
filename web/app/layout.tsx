import "./globals.css";

export const metadata = {
  title: "Polyglot Voice Stream",
  description: "Real-time speech translation that keeps your own voice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
