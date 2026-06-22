import type { Metadata } from "next";import "./globals.css";import { Sidebar } from "@/components/sidebar";import { Header } from "@/components/header";
import { AuthGate } from "@/components/auth-gate";
export const metadata:Metadata={title:"AI Project Idea Collector",description:"Collect and discover inspiring AI projects"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><body><AuthGate><Sidebar/><div className="lg:pl-64"><Header/><main className="mx-auto max-w-[1600px] p-4 pb-24 lg:p-8">{children}</main></div></AuthGate></body></html>}
