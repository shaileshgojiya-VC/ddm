export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main>
      <div className="flex items-center justify-center min-h-screen bg-linear-to-tl from-zinc-100 to-slate-100 px-4 py-12">
        {children}
      </div>
    </main>
  );
}
