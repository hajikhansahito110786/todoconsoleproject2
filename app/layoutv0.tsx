import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from './providers';
import Navbar from '@/components/Navbar'; // Import the Navbar

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Student Todo App',
  description: 'A simple app to manage students and their classes.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <Navbar /> {/* Add the Navbar here */}
          <main className="container mx-auto p-4">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}