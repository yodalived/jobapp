"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useState, useEffect, Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Briefcase, BarChart3, CheckCircle, Mail, X, LayoutDashboard } from "lucide-react"
import { Nav } from "@/components/nav"
import { apiClient, User } from "@/lib/api"

function LandingPageContent() {
  const searchParams = useSearchParams()
  const [showVerificationMessage, setShowVerificationMessage] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (searchParams.get('registered') === 'true') {
      setShowVerificationMessage(true)
    }
  }, [searchParams])

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        const response = await apiClient.getCurrentUser()
        if (response.data) {
          setUser(response.data)
        } else if (response.error) {
          // API returned an error, user not authenticated
          console.log('User not authenticated:', response.error)
        }
      } catch (error) {
        // Network or other error, user not logged in
        console.log('Auth check failed:', error)
      } finally {
        setLoading(false)
      }
    }
    checkAuth()
  }, [])
  const features = [
    {
      icon: FileText,
      title: "AI-Powered Resume Builder",
      description: "Create professional resumes with AI assistance tailored to your industry and role."
    },
    {
      icon: Briefcase,
      title: "Application Tracking",
      description: "Track all your job applications in one place with status updates and notes."
    },
    {
      icon: BarChart3,
      title: "Performance Analytics",
      description: "Get insights on your application success rate and optimize your job search."
    },
    {
      icon: CheckCircle,
      title: "Industry Templates",
      description: "Choose from professionally designed templates optimized for different industries."
    }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Nav user={user} />

      {/* Email Verification Banner */}
      {showVerificationMessage && (
        <div className="bg-green-50 border-b border-green-200">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center">
                <Mail className="h-5 w-5 text-green-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-green-800">
                    Registration successful! Please check your email.
                  </p>
                  <p className="text-xs text-green-600">
                    We&apos;ve sent you a verification link. Click it to activate your account and start building your resume.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowVerificationMessage(false)}
                className="text-green-600 hover:text-green-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <main className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Build Professional Resumes with{" "}
              <span className="text-blue-600">AI Assistance</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
              Create tailored resumes, track applications, and land your dream job with our 
              AI-powered platform. Stand out from the competition with professional templates 
              and intelligent optimization.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {user ? (
                <Link href="/dashboard">
                  <Button size="lg" className="px-8">
                    Go to Dashboard
                  </Button>
                </Link>
              ) : (
                <Link href="/register">
                  <Button size="lg" className="px-8">
                    Start Building Free
                  </Button>
                </Link>
              )}
              <Link href="/demo">
                <Button variant="outline" size="lg">
                  View Demo
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Everything you need to succeed
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Powerful tools to streamline your job search and application process
            </p>
          </div>
          
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="text-center pb-4">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
                    <feature.icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-center">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-blue-600">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-white sm:text-4xl">
                Ready to land your dream job?
              </h2>
              <p className="mt-4 text-lg text-blue-100">
                Join thousands of professionals who have successfully upgraded their careers
              </p>
              <div className="mt-8">
                <Link href="/register">
                  <Button size="lg" variant="secondary" className="px-8">
                    Get Started Today
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default function LandingPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LandingPageContent />
    </Suspense>
  )
}
