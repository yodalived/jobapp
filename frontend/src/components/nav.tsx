"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { FileText, LayoutDashboard, FileCheck, Briefcase, LogOut, User as UserIcon, ChevronDown } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { apiClient, User } from "@/lib/api"
import { useRouter } from "next/navigation"

interface NavProps {
  user: User | null
}

export function Nav({ user }: NavProps) {
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await apiClient.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
    // Force a full page reload to clear all state
    window.location.href = '/'
  }

  return (
    <nav className="border-b bg-white/80 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between items-center">
          <div className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <Link href="/" className="text-xl font-bold text-gray-900">ResumeAI</Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/status">
              <Button variant="ghost">Status</Button>
            </Link>
            {user ? (
              <>
                {/* Professional Stats in Nav */}
                <div className="hidden sm:flex items-center space-x-4 text-sm">
                  <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-lg">
                    <FileCheck className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-blue-900">{user.resumes_generated_count || 0}</span>
                    <span className="text-blue-600">resumes</span>
                  </div>
                  <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-lg">
                    <Briefcase className="h-4 w-4 text-green-600" />
                    <span className="font-medium text-green-900">{user.applications_count || 0}</span>
                    <span className="text-green-600">applications</span>
                  </div>
                </div>
                <Link href="/dashboard">
                  <Button variant="ghost" className="flex items-center gap-2">
                    <LayoutDashboard className="h-4 w-4" />
                    Dashboard
                  </Button>
                </Link>
                {/* User Profile Dropdown - Far Right */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
                      <span className="hidden md:inline">Welcome back, {user.email ? user.email.split('@')[0] : 'User'}!</span>
                      <span className="md:hidden">
                        <UserIcon className="h-4 w-4" />
                      </span>
                      <ChevronDown className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <div className="px-2 py-1.5 text-sm font-medium">
                      {user.email}
                    </div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <Link href="/profile" className="cursor-pointer">
                        <UserIcon className="mr-2 h-4 w-4" />
                        Profile
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600">
                      <LogOut className="mr-2 h-4 w-4" />
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link href="/login?redirect=/">
                  <Button variant="ghost">Sign in</Button>
                </Link>
                <Link href="/register?redirect=/">
                  <Button>Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}