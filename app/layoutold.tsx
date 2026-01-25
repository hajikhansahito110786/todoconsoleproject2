export const metadata = {
  title: 'Login System',
  description: 'Simple login system with Neon PostgreSQL',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}