'use client'

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Nav } from '@/components/nav';
import { CheckCircle, XCircle, Clock, AlertCircle, Server, Database, Cpu, Network, ChevronRight, ChevronDown, GitBranch, Zap, Target, Layers, Trash2, Settings } from 'lucide-react';

interface SystemStatus {
  api: 'healthy' | 'unhealthy' | 'unknown';
  database: 'healthy' | 'unhealthy' | 'unknown';
  redis: 'healthy' | 'unhealthy' | 'unknown';
  kafka: 'healthy' | 'unhealthy' | 'unknown';
}

const StatusIcon = ({ status }: { status: 'healthy' | 'unhealthy' | 'unknown' | 'completed' | 'partial' | 'pending' }) => {
  switch (status) {
    case 'healthy':
    case 'completed':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'partial':
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case 'pending':
      return <Clock className="h-5 w-5 text-blue-500" />;
    case 'unhealthy':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <AlertCircle className="h-5 w-5 text-gray-500" />;
  }
};

const StatusBadge = ({ status }: { status: 'healthy' | 'unhealthy' | 'unknown' | 'completed' | 'partial' | 'pending' }) => {
  const colors = {
    healthy: 'bg-green-100 text-green-800',
    completed: 'bg-green-100 text-green-800',
    partial: 'bg-yellow-100 text-yellow-800',
    pending: 'bg-blue-100 text-blue-800',
    unhealthy: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-800',
  };

  return (
    <Badge className={colors[status]}>
      {status}
    </Badge>
  );
};

interface Task {
  name: string;
  status: 'completed' | 'partial' | 'pending';
  details?: string[];
}

interface Category {
  id: string;
  title: string;
  icon: React.ReactNode;
  status: 'completed' | 'partial' | 'pending';
  description: string;
  tasks: Task[];
}

interface Phase {
  id: string;
  title: string;
  status: 'completed' | 'partial' | 'pending';
  description: string;
  capacity: string;
  progress: number;
  expanded: boolean;
  categories: Category[];
}

// Component for individual phases
const PhaseCard = ({ phase }: { phase: Phase }) => {
  const [isExpanded, setIsExpanded] = useState(phase.expanded);
  
  const getPhaseIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'partial': return <Clock className="h-5 w-5 text-yellow-500" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };
  
  const getPhaseColor = (status: string) => {
    switch (status) {
      case 'completed': return 'border-green-200 bg-green-50';
      case 'partial': return 'border-yellow-200 bg-yellow-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };
  
  return (
    <Card className={`${getPhaseColor(phase.status)} transition-all duration-200`}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-opacity-80 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getPhaseIcon(phase.status)}
                <div>
                  <CardTitle className="text-lg">{phase.title}</CardTitle>
                  <CardDescription className="flex items-center gap-4">
                    <span>{phase.description}</span>
                    <Badge variant="outline">{phase.capacity}</Badge>
                    {phase.status === 'completed' && <Badge className="bg-green-100 text-green-800">Complete</Badge>}
                    {phase.status === 'partial' && <Badge className="bg-yellow-100 text-yellow-800">In Progress</Badge>}
                    {phase.status === 'pending' && <Badge className="bg-gray-100 text-gray-800">Planned</Badge>}
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {phase.progress > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full">
                      <div 
                        className="h-full bg-blue-500 rounded-full transition-all duration-300" 
                        style={{ width: `${phase.progress}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{phase.progress}%</span>
                  </div>
                )}
                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-4">
              {phase.categories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

// Component for categories within phases
const CategoryCard = ({ category }: { category: Category }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getCategoryStatus = () => {
    const completed = category.tasks.filter((task) => task.status === 'completed').length;
    const partial = category.tasks.filter((task) => task.status === 'partial').length;
    const total = category.tasks.length;
    
    if (completed === total) return 'completed';
    if (completed + partial > 0) return 'partial';
    return 'pending';
  };
  
  const status = getCategoryStatus();
  const completed = category.tasks.filter((task) => task.status === 'completed').length;
  const total = category.tasks.length;
  
  return (
    <div className="border rounded-lg">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              {category.icon}
              <div>
                <h4 className="font-semibold text-gray-900">{category.title}</h4>
                <p className="text-sm text-gray-600">{category.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status={status} />
              <span className="text-sm text-gray-500">{completed}/{total}</span>
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </div>
          </div>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-3 border-t bg-gray-50">
            {category.tasks.map((task) => (
              <TaskCard key={task.name} task={task} />
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
};

// Component for individual tasks
const TaskCard = ({ task }: { task: Task }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="bg-white rounded-md border">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <div className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-2">
              <StatusIcon status={task.status} />
              <span className="font-medium text-sm">{task.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={task.status} />
              {task.details && task.details.length > 0 && (
                <span className="text-xs text-gray-400">
                  {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                </span>
              )}
            </div>
          </div>
        </CollapsibleTrigger>
        
        {task.details && task.details.length > 0 && (
          <CollapsibleContent>
            <div className="px-3 pb-3 border-t bg-gray-50">
              <ul className="mt-2 space-y-1">
                {task.details.map((detail: string, index: number) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start gap-1">
                    <span className="text-gray-400 mt-1">•</span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CollapsibleContent>
        )}
      </Collapsible>
    </div>
  );
};

export default function StatusPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    api: 'unknown',
    database: 'unknown',
    redis: 'unknown',
    kafka: 'unknown',
  });
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteMessage, setDeleteMessage] = useState<{type: 'success' | 'error' | 'info', text: string} | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiClient.healthCheck();
        if (response.data) {
          const health = response.data;
          setSystemStatus({
            api: health.status === 'healthy' ? 'healthy' : 'unhealthy',
            database: health.services.database === 'healthy' ? 'healthy' : 'unhealthy',
            redis: health.services.redis === 'healthy' ? 'healthy' : 'unhealthy',
            kafka: health.services.kafka === 'healthy' ? 'healthy' : 'unhealthy',
          });
        } else {
          setSystemStatus({
            api: 'unhealthy',
            database: 'unknown',
            redis: 'unknown',
            kafka: 'unknown',
          });
        }
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const roadmapData: { phases: Phase[] } = {
    phases: [
      {
        id: 'phase1',
        title: 'Phase 1: Event-Driven Cell Architecture',
        status: 'completed' as const,
        description: 'Single cell foundation with event-driven patterns',
        capacity: '100 users',
        progress: 100,
        expanded: true, // Current phase should be expanded
        categories: [
          {
            id: 'infrastructure',
            title: 'Core Infrastructure',
            icon: <Server className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'Foundation services and data layer',
            tasks: [
              { name: 'FastAPI Backend', status: 'completed' as const, details: ['Async request handling', 'Auto-generated OpenAPI docs', 'Dependency injection system', 'CORS middleware configuration'] },
              { name: 'PostgreSQL Database', status: 'completed' as const, details: ['Multi-tenant schema design', 'Async SQLAlchemy integration', 'Connection pooling', 'Migration system with Alembic'] },
              { name: 'Redis Cache', status: 'completed' as const, details: ['Session storage', 'Rate limiting support', 'Async client configuration', 'Health monitoring'] },
              { name: 'Kafka Event Streaming', status: 'completed' as const, details: ['Event producer setup', 'Topic configuration', 'Schema registry integration', 'Error handling and retries'] },
              { name: 'Database Migrations', status: 'completed' as const, details: ['Alembic configuration', 'User and application tables', 'Indexes for performance', 'Foreign key constraints'] },
            ]
          },
          {
            id: 'auth',
            title: 'Authentication & Security',
            icon: <Layers className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'User management and access control',
            tasks: [
              { name: 'JWT Authentication', status: 'completed' as const, details: ['Bearer token implementation', 'Token expiration handling', 'Secure secret management', 'Middleware integration'] },
              { name: 'User Registration', status: 'completed' as const, details: ['Email validation', 'Password hashing with bcrypt', 'User profile creation', 'Error handling'] },
              { name: 'Multi-tenant Support', status: 'completed' as const, details: ['User data isolation', 'Query filtering by user_id', 'Relationship management', 'Data access patterns'] },
              { name: 'Subscription Tiers', status: 'completed' as const, details: ['Free tier (10 applications)', 'Starter tier (50 applications)', 'Professional tier (200 applications)', 'Enterprise tier (unlimited)'] },
              { name: 'Usage Limits', status: 'completed' as const, details: ['API rate limiting', 'Tier-based restrictions', 'Usage tracking', 'Limit enforcement'] },
            ]
          },
          {
            id: 'job-management',
            title: 'Job Management',
            icon: <Target className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'Application lifecycle and tracking',
            tasks: [
              { name: 'Job Application CRUD', status: 'completed' as const, details: ['Create applications', 'List with pagination', 'Update status and details', 'Soft delete functionality'] },
              { name: 'Application Status Tracking', status: 'completed' as const, details: ['Status workflow (applied → interviewed → offered)', 'Timestamp tracking', 'History logging', 'Progress analytics'] },
              { name: 'Notes & Comments', status: 'completed' as const, details: ['Rich text notes', 'Application annotations', 'Timeline tracking', 'Search functionality'] },
              { name: 'Statistics Dashboard', status: 'completed' as const, details: ['Application count by status', 'Success rate analytics', 'Time-based trends', 'User activity metrics'] },
            ]
          },
          {
            id: 'ai-generation',
            title: 'AI & Resume Generation',
            icon: <Zap className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'AI-powered resume customization',
            tasks: [
              { name: 'Multi-LLM Support', status: 'completed' as const, details: ['OpenAI GPT integration', 'Anthropic Claude integration', 'Provider abstraction layer', 'Fallback logic implementation'] },
              { name: 'Job Analysis', status: 'completed' as const, details: ['Requirement extraction', 'Skill identification', 'Company analysis', 'Match scoring algorithm'] },
              { name: 'Resume Generation API', status: 'completed' as const, details: ['Template-based generation', 'AI customization engine', 'Job-specific optimization', 'Error handling and validation'] },
              { name: 'LaTeX Templates', status: 'completed' as const, details: ['Modern professional template', 'Jinja2 templating system', 'Special character escaping', 'Layout optimization'] },
              { name: 'PDF Generation', status: 'completed' as const, details: ['LaTeX compilation pipeline', 'Cross-platform compatibility', 'Error handling', 'Output validation'] },
            ]
          },
          {
            id: 'events',
            title: 'Event-Driven Architecture',
            icon: <GitBranch className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'Event streaming and workflow orchestration',
            tasks: [
              { name: 'Event Schema', status: 'completed' as const, details: ['Typed event definitions', 'Schema validation', 'Event versioning', 'Backward compatibility'] },
              { name: 'Kafka Producer', status: 'completed' as const, details: ['Async event publishing', 'Batch processing', 'Error handling', 'Monitoring integration'] },
              { name: 'Event Consumer', status: 'completed' as const, details: ['Consumer group setup', 'Message processing', 'Dead letter queue', 'Retry mechanisms'] },
              { name: 'Workflow Agents', status: 'completed' as const, details: ['ScraperAgent (job discovery)', 'AnalyzerAgent (requirement extraction)', 'GeneratorAgent (resume creation)', 'OptimizerAgent (success optimization)'] },
            ]
          },
          {
            id: 'frontend',
            title: 'Frontend & UI',
            icon: <Layers className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'User interface and experience',
            tasks: [
              { name: 'Next.js 15 Frontend', status: 'completed' as const, details: ['App router setup', 'TypeScript configuration', 'Tailwind CSS integration', 'Build optimization'] },
              { name: 'Landing Page', status: 'completed' as const, details: ['Professional design', 'Responsive layout', 'Feature showcase', 'Call-to-action sections'] },
              { name: 'Status Dashboard', status: 'completed' as const, details: ['Real-time system health', 'Feature progress tracking', 'Service monitoring', 'Development roadmap'] },
              { name: 'API Integration', status: 'completed' as const, details: ['TypeScript API client', 'Request/response handling', 'Error management', 'Authentication flow'] },
              { name: 'Authentication UI', status: 'completed' as const, details: ['Complete login form with API integration', 'Full registration flow with validation', 'Email verification system', 'JWT token management', 'Password visibility toggle'] },
              { name: 'Email System', status: 'completed' as const, details: ['SMTP configuration support', 'Email verification flow', 'Professional HTML templates', 'Async email sending', 'Graceful fallback for unconfigured state'] },
              { name: 'Dashboard UI', status: 'completed' as const, details: ['User application management interface', 'Professional stats display', 'Profile management system', 'GitHub-style navigation with user dropdown'] },
            ]
          },
          {
            id: 'deployment',
            title: 'Development & DevOps',
            icon: <Server className="h-4 w-4" />,
            status: 'completed' as const,
            description: 'Development workflow and deployment',
            tasks: [
              { name: 'Docker Compose', status: 'completed' as const, details: ['Multi-service orchestration', 'PostgreSQL container', 'Redis container', 'Kafka + Zookeeper setup'] },
              { name: 'Environment Config', status: 'completed' as const, details: ['Comprehensive .env.example', 'Configuration validation', 'Development vs production', 'Secret management'] },
              { name: 'Integration Tests', status: 'completed' as const, details: ['API endpoint testing', 'Resume generation tests', 'LaTeX escaping validation', 'Event publishing tests'] },
              { name: 'Code Quality', status: 'completed' as const, details: ['Ruff linting configuration', 'Type checking', 'Import sorting', 'Code formatting'] },
              { name: 'Development Tools', status: 'completed' as const, details: ['Test user deletion endpoint', 'Interactive status page', 'Development utilities UI', 'Quick cleanup functionality'] },
            ]
          }
        ]
      },
      {
        id: 'phase2',
        title: 'Phase 2: Enhanced Cell + Gateway',
        status: 'pending' as const,
        description: 'High-performance gateway and worker separation',
        capacity: '1,000 users',
        progress: 0,
        expanded: false,
        categories: [
          {
            id: 'gateway',
            title: 'Go API Gateway',
            icon: <Network className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'High-performance request routing and rate limiting',
            tasks: [
              { name: 'Gateway Implementation', status: 'pending' as const, details: ['Go fiber framework', 'Request routing', 'Load balancing', 'Circuit breaker pattern'] },
              { name: 'Rate Limiting', status: 'pending' as const, details: ['Redis-based rate limiting', 'Tier-based limits', 'DDoS protection', 'Monitoring integration'] },
              { name: 'Authentication Proxy', status: 'pending' as const, details: ['JWT validation', 'Session management', 'User context passing', 'Security headers'] },
              { name: 'Monitoring Integration', status: 'pending' as const, details: ['Prometheus metrics', 'Request tracing', 'Performance monitoring', 'Error tracking'] },
            ]
          },
          {
            id: 'workers',
            title: 'Worker Process Separation',
            icon: <Cpu className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'Dedicated processes for background tasks',
            tasks: [
              { name: 'Agent Workers', status: 'pending' as const, details: ['Separate scraper processes', 'Analyzer worker pools', 'Generator scaling', 'Optimizer background tasks'] },
              { name: 'Queue Management', status: 'pending' as const, details: ['Task prioritization', 'Retry mechanisms', 'Dead letter handling', 'Monitoring dashboards'] },
              { name: 'Resource Management', status: 'pending' as const, details: ['CPU/memory limits', 'Auto-scaling policies', 'Health checks', 'Graceful shutdowns'] },
            ]
          },
          {
            id: 'monitoring',
            title: 'Enhanced Monitoring',
            icon: <AlertCircle className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'Comprehensive observability stack',
            tasks: [
              { name: 'Prometheus Stack', status: 'pending' as const, details: ['Metrics collection', 'Grafana dashboards', 'Alert manager', 'Custom metrics'] },
              { name: 'Distributed Tracing', status: 'pending' as const, details: ['Jaeger integration', 'Request tracing', 'Performance bottlenecks', 'Error tracking'] },
              { name: 'Log Aggregation', status: 'pending' as const, details: ['Centralized logging', 'Log parsing', 'Search capabilities', 'Log retention'] },
            ]
          },
          {
            id: 'ui-enhancement',
            title: 'UI Enhancement',
            icon: <Layers className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'Complete user experience',
            tasks: [
              { name: 'Authentication Forms', status: 'pending' as const, details: ['Login page implementation', 'Registration flow', 'Password reset', 'Email verification'] },
              { name: 'User Dashboard', status: 'pending' as const, details: ['Application management', 'Resume builder', 'Analytics view', 'Profile settings'] },
              { name: 'Real-time Updates', status: 'pending' as const, details: ['WebSocket integration', 'Live notifications', 'Progress tracking', 'Status updates'] },
            ]
          }
        ]
      },
      {
        id: 'phase3',
        title: 'Phase 3: Multi-Cell Architecture',
        status: 'pending' as const,
        description: 'Horizontal scaling with multiple cells',
        capacity: '10,000 users',
        progress: 0,
        expanded: false,
        categories: [
          {
            id: 'scaling',
            title: 'Horizontal Scaling',
            icon: <Network className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'Multi-cell coordination and load distribution',
            tasks: [
              { name: 'Cell Coordination', status: 'pending' as const, details: ['Service discovery', 'Load balancing', 'Health monitoring', 'Failover mechanisms'] },
              { name: 'Data Sharding', status: 'pending' as const, details: ['User-based sharding', 'Cross-shard queries', 'Data migration', 'Consistency management'] },
              { name: 'Global Load Balancer', status: 'pending' as const, details: ['Geographic routing', 'Health-based routing', 'Circuit breakers', 'Performance monitoring'] },
            ]
          }
        ]
      },
      {
        id: 'phase4',
        title: 'Phase 4: Global Scale',
        status: 'pending' as const,
        description: 'Multi-region deployment for global users',
        capacity: '30,000+ users',
        progress: 0,
        expanded: false,
        categories: [
          {
            id: 'global',
            title: 'Global Infrastructure',
            icon: <Network className="h-4 w-4" />,
            status: 'pending' as const,
            description: 'Multi-region deployment and coordination',
            tasks: [
              { name: 'Multi-Region Deployment', status: 'pending' as const, details: ['Regional data centers', 'Global DNS', 'CDN integration', 'Regional failover'] },
              { name: 'Advanced Analytics', status: 'pending' as const, details: ['Machine learning insights', 'Success prediction', 'Market analysis', 'User behavior tracking'] },
            ]
          }
        ]
      }
    ]
  };

  const getOverallStatus = () => {
    const phase1 = roadmapData.phases.find(p => p.id === 'phase1');
    if (!phase1) return { total: 0, completed: 0, partial: 0, pending: 0, percentage: 0 };
    
    const total = phase1.categories.reduce((acc, cat) => acc + cat.tasks.length, 0);
    const completed = phase1.categories.reduce((acc, cat) => 
      acc + cat.tasks.filter(task => task.status === 'completed').length, 0
    );
    const partial = phase1.categories.reduce((acc, cat) => 
      acc + cat.tasks.filter(task => task.status === 'partial').length, 0
    );
    
    return {
      total,
      completed,
      partial,
      pending: total - completed - partial,
      percentage: Math.round(((completed + partial * 0.5) / total) * 100)
    };
  };

  const stats = getOverallStatus();

  const handleDeleteTestUser = async () => {
    if (!confirm('Are you sure you want to delete the test user yodalives@gmail.com?\n\nThis action cannot be undone.')) {
      return;
    }
    
    setDeleteLoading(true);
    setDeleteMessage(null);
    
    try {
      const response = await apiClient.deleteTestUser('yodalives@gmail.com');
      if (response.error) {
        // Check if it's a "not found" error to provide clearer feedback
        if (response.error.includes('not found')) {
          setDeleteMessage({ type: 'error', text: 'Test user does not exist' });
        } else {
          setDeleteMessage({ type: 'error', text: response.error });
        }
      } else {
        setDeleteMessage({ type: 'success', text: response.data?.message || 'User deleted successfully' });
        // Clear success message after 5 seconds
        setTimeout(() => setDeleteMessage(null), 5000);
      }
    } catch (error) {
      console.error('Delete user error:', error);
      setDeleteMessage({ type: 'error', text: 'Failed to delete user. Please try again.' });
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Nav user={null} />
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Resume Automation Platform - Phase 1 Complete</h1>
          <p className="text-lg text-gray-600">Interactive roadmap with detailed implementation progress and scaling phases</p>
        </div>

        {/* Overall Progress */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Overall Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{stats.percentage}%</div>
              <div className="text-sm text-gray-500">{stats.completed + stats.partial}/{stats.total} features</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{stats.completed}</div>
              <div className="text-sm text-gray-500">Fully implemented</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">In Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">{stats.partial}</div>
              <div className="text-sm text-gray-500">Partially complete</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Pending</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-600">{stats.pending}</div>
              <div className="text-sm text-gray-500">Not started</div>
            </CardContent>
          </Card>
        </div>

        {/* System Health */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              System Health
            </CardTitle>
            <CardDescription>Real-time status of core services</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4" />
                  <span className="font-medium">API Server</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusIcon status={systemStatus.api} />
                  <StatusBadge status={systemStatus.api} />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  <span className="font-medium">PostgreSQL</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusIcon status={systemStatus.database} />
                  <StatusBadge status={systemStatus.database} />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  <span className="font-medium">Redis</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusIcon status={systemStatus.redis} />
                  <StatusBadge status={systemStatus.redis} />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4" />
                  <span className="font-medium">Kafka</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusIcon status={systemStatus.kafka} />
                  <StatusBadge status={systemStatus.kafka} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Development Tools */}
        <Card className="mb-8 border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <Settings className="h-5 w-5" />
              Development Tools
            </CardTitle>
            <CardDescription className="text-orange-700">
              Quick actions for testing and development
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between p-3 border border-orange-200 rounded-lg bg-white">
                <div className="flex items-start gap-3">
                  <Trash2 className="h-5 w-5 text-gray-500 mt-0.5" />
                  <div>
                    <span className="font-medium text-gray-900">Delete Test User</span>
                    <p className="text-sm text-gray-600">Remove yodalives@gmail.com for clean testing</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {deleteMessage && (
                    <span className={`text-sm font-medium ${
                      deleteMessage.type === 'success' ? 'text-green-600' : 
                      deleteMessage.type === 'error' ? 'text-red-600' : 
                      'text-blue-600'
                    }`}>
                      {deleteMessage.type === 'success' ? '✓' : 
                       deleteMessage.type === 'error' ? '✗' : 
                       'ℹ'} {deleteMessage.text}
                    </span>
                  )}
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={handleDeleteTestUser}
                    disabled={deleteLoading}
                    aria-label="Delete test user yodalives@gmail.com"
                    className="min-w-[140px]"
                  >
                    {deleteLoading ? (
                      <>
                        <span className="animate-spin mr-2">⟳</span>
                        Deleting...
                      </>
                    ) : (
                      "Delete Test User"
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Interactive Roadmap */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900">Development Roadmap</h2>
          <p className="text-gray-600">Click on phases and categories to explore detailed implementation progress</p>
          
          {roadmapData.phases.map((phase) => (
            <PhaseCard key={phase.id} phase={phase} />
          ))}
        </div>


      </div>
    </div>
  );
}