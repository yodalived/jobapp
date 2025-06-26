"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Plus, TrendingUp, Briefcase, Eye, Download, Mail } from "lucide-react"
import { apiClient, User } from "@/lib/api"

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null)
  const [showVerificationBanner, setShowVerificationBanner] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch user data to check verification status
    const fetchUser = async () => {
      try {
        const response = await apiClient.getCurrentUser()
        if (response.data) {
          setUser(response.data)
          setShowVerificationBanner(!response.data.email_verified)
        }
      } catch (error) {
        console.error('Failed to fetch user:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchUser()
  }, [])

  const stats = [
    { title: "Resumes Created", value: "12", icon: FileText, change: "+2 this month" },
    { title: "Applications Sent", value: "34", icon: Briefcase, change: "+8 this week" },
    { title: "Profile Views", value: "156", icon: Eye, change: "+12% this month" },
    { title: "Response Rate", value: "18%", icon: TrendingUp, change: "+3% improvement" },
  ]

  const recentResumes = [
    { name: "Software Engineer - Google", lastModified: "2 hours ago", status: "Active" },
    { name: "Full Stack Developer - Stripe", lastModified: "1 day ago", status: "Draft" },
    { name: "Frontend Engineer - Airbnb", lastModified: "3 days ago", status: "Active" },
  ]

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!user) {
    return <div className="flex items-center justify-center min-h-screen">Failed to load user data</div>
  }

  return (
    <MainLayout user={user}>
      {/* Email Verification Banner */}
      {showVerificationBanner && (
        <div className="bg-green-50 border-b border-green-200 -m-6 mb-6 p-4">
          <div className="flex items-center">
            <Mail className="h-5 w-5 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-green-800">
                Verify your email to unlock all features
              </p>
              <p className="text-xs text-green-600 mt-1">
                Check your inbox for a verification email. Without verification, you can only create 2 resumes and cannot apply to jobs.
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Welcome back! Here&apos;s an overview of your job search progress.
            </p>
          </div>
          <Button className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create Resume
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <p className="text-xs text-green-600 mt-1">{stat.change}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Resumes */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Resumes</CardTitle>
                <CardDescription>
                  Your latest resume versions and their status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentResumes.map((resume, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-blue-600" />
                        <div>
                          <p className="font-medium text-gray-900">{resume.name}</p>
                          <p className="text-sm text-gray-500">Modified {resume.lastModified}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            resume.status === "Active"
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {resume.status}
                        </span>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t">
                  <Button variant="outline" className="w-full">
                    View All Resumes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Create New Resume
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Briefcase className="mr-2 h-4 w-4" />
                  Track Application
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  View Analytics
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900">Optimize Keywords</p>
                    <p className="text-xs text-blue-700">
                      Use industry-specific keywords to improve ATS compatibility
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-900">Track Applications</p>
                    <p className="text-xs text-green-700">
                      Keep detailed records of your job applications for better follow-up
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}