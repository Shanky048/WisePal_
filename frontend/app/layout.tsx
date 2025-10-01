import type { Metadata } from "next";
import "./globals.css";
// Correcting the path to be relative from the current 'app' directory
// and assuming the folder name is 'Context' with a capital 'C' as shown in your screenshot.
import AuthProvider from "./context/AuthContext"; 

export const metadata: Metadata = {
  title: "WisePal AI",
  description: "Your intelligent AI companion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {/* Wrap the entire application in the AuthProvider */}
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

