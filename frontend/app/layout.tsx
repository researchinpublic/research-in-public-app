import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Research In Public - Agentic Support Ecosystem',
  description: 'Multi-agent AI system for PhD students and researchers',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/icon.svg', type: 'image/svg+xml', sizes: 'any' },
    ],
    apple: '/icon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}


