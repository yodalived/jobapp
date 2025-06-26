import { ReactNode } from "react"
import { Navbar } from "./navbar"
import { Sidebar } from "./sidebar"
import { User } from "@/lib/api"

interface MainLayoutProps {
  children: ReactNode
  user: User | null
  showSidebar?: boolean
}

export function MainLayout({ children, user, showSidebar = true }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} />
      <div className="flex h-[calc(100vh-4rem)]">
        {showSidebar && <Sidebar />}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}