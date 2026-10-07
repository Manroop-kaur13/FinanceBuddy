import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'FinanceBuddy — Personal finance, made clear', description: 'Your complete personal finance workspace.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
