// app/layout.tsx
"use client"; // Add this at the top

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "./Navigation.tsx";
import { UserProvider } from "./context/UserContext";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"; // Add this

const inter = Inter({ subsets: ["latin"] });

// Create a client
const queryClient = new QueryClient();

// Remove the metadata export since we're using "use client"
// export const metadata: Metadata = {
//   title: "Student Management System",
//   description: "Manage students and todos",
// };

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <title>Student Management System</title>
        <meta name="description" content="Manage students and todos" />
      </head>
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}> {/* Add this */}
          <UserProvider>
            <Navigation />
            <main className="min-h-screen bg-gray-50">
              {children}
            </main>
          </UserProvider>
        </QueryClientProvider> {/* Add this */}
      </body>
    </html>
  );
}