"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  FileText,
  Briefcase,
  BarChart3,
  Settings,
  Plus,
  Home,
} from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Resume Builder", href: "/resume-builder", icon: FileText },
  { name: "Applications", href: "/applications", icon: Briefcase },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-gray-50 border-r">
      <div className="flex h-16 items-center justify-between px-4 border-b">
        <Link href="/" className="flex items-center space-x-2">
          <FileText className="h-6 w-6 text-blue-600" />
          <span className="text-lg font-semibold">ResumeAI</span>
        </Link>
      </div>
      
      <div className="flex-1 p-4">
        <div className="mb-4">
          <Button className="w-full justify-start" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Resume
          </Button>
        </div>
        
        <nav className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
              >
                <item.icon className="mr-3 h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
      
      <div className="p-4 border-t">
        <div className="rounded-lg bg-blue-50 p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-blue-700 font-medium">Pro Plan</span>
            <span className="text-blue-600">Upgrade</span>
          </div>
          <div className="mt-1 text-xs text-blue-600">
            5 of 10 resumes used
          </div>
        </div>
      </div>
    </div>
  )
}