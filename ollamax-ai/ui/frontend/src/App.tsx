import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronRightIcon, PlayIcon, CpuChipIcon, ShieldCheckIcon, CodeBracketIcon } from '@heroicons/react/24/outline'

const API_BASE = 'http://localhost:12000'

interface SystemStatus {
  status: string
  agents_active: number
  tasks_completed: number
  uptime: number
}

interface TaskResult {
  task_id: string
  status: string
  result?: any
  error?: string
}

function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [currentTask, setCurrentTask] = useState('')
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    fetchSystemStatus()
    fetchLogs()
    
    // Setup WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:12000/ws')
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'logs_update') {
        setLogs(data.logs)
      }
    }
    
    return () => ws.close()
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/system/status`)
      setSystemStatus(response.data)
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    }
  }

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/logs/recent?limit=50`)
      setLogs(response.data.logs)
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    }
  }

  const submitTask = async () => {
    if (!currentTask.trim()) return
    
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/tasks/submit`, {
        task: currentTask,
        context: {}
      })
      setTaskResult(response.data)
      setCurrentTask('')
      fetchSystemStatus()
      fetchLogs()
    } catch (error) {
      console.error('Failed to submit task:', error)
      setTaskResult({
        task_id: 'error',
        status: 'failed',
        error: 'Failed to submit task'
      })
    } finally {
      setLoading(false)
    }
  }

  const quickTasks = [
    {
      title: "Vulnerability Scan",
      description: "Scan a target for security vulnerabilities",
      task: "Perform a comprehensive vulnerability scan on localhost",
      icon: ShieldCheckIcon,
      color: "text-red-500"
    },
    {
      title: "Generate Code",
      description: "Generate Python code for a specific task",
      task: "Generate a Python function to calculate fibonacci numbers with memoization",
      icon: CodeBracketIcon,
      color: "text-blue-500"
    },
    {
      title: "System Analysis",
      description: "Analyze system performance and security",
      task: "Analyze the current system for performance bottlenecks and security issues",
      icon: CpuChipIcon,
      color: "text-green-500"
    }
  ]

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
                OllamaX-AI
              </h1>
              <span className="ml-3 px-2 py-1 text-xs bg-green-500 text-black rounded-full font-semibold">
                {systemStatus?.status || 'Loading...'}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-300">
                Agents: {systemStatus?.agents_active || 0}
              </div>
              <div className="text-sm text-gray-300">
                Tasks: {systemStatus?.tasks_completed || 0}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['dashboard', 'tasks', 'agents', 'logs'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            {/* Quick Tasks */}
            <div>
              <h2 className="text-2xl font-bold mb-6">Quick Tasks</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {quickTasks.map((task, index) => (
                  <div
                    key={index}
                    className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 cursor-pointer transition-colors"
                    onClick={() => setCurrentTask(task.task)}
                  >
                    <div className="flex items-center mb-4">
                      <task.icon className={`h-8 w-8 ${task.color}`} />
                      <h3 className="ml-3 text-lg font-semibold">{task.title}</h3>
                    </div>
                    <p className="text-gray-300 text-sm mb-4">{task.description}</p>
                    <div className="flex items-center text-purple-400 text-sm">
                      <span>Try this task</span>
                      <ChevronRightIcon className="h-4 w-4 ml-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Task Input */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-xl font-bold mb-4">Submit Task</h2>
              <div className="space-y-4">
                <textarea
                  value={currentTask}
                  onChange={(e) => setCurrentTask(e.target.value)}
                  placeholder="Describe your task here... (e.g., 'Generate a secure login function in Python' or 'Scan for SQL injection vulnerabilities')"
                  className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={submitTask}
                  disabled={loading || !currentTask.trim()}
                  className="flex items-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <PlayIcon className="h-5 w-5 mr-2" />
                  {loading ? 'Processing...' : 'Execute Task'}
                </button>
              </div>
            </div>

            {/* Task Result */}
            {taskResult && (
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h2 className="text-xl font-bold mb-4">Task Result</h2>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <span className="text-sm text-gray-300">Status:</span>
                    <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                      taskResult.status === 'completed' 
                        ? 'bg-green-500 text-black' 
                        : 'bg-red-500 text-white'
                    }`}>
                      {taskResult.status}
                    </span>
                  </div>
                  {taskResult.error && (
                    <div className="bg-red-900 border border-red-700 rounded-lg p-4">
                      <p className="text-red-200">{taskResult.error}</p>
                    </div>
                  )}
                  {taskResult.result && (
                    <div className="bg-gray-700 rounded-lg p-4">
                      <pre className="text-sm text-gray-200 whitespace-pre-wrap overflow-x-auto">
                        {JSON.stringify(taskResult.result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-4">System Logs</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index} className="text-sm font-mono">
                  <span className="text-gray-400">{log.timestamp}</span>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    log.level === 'ERROR' ? 'bg-red-900 text-red-200' :
                    log.level === 'WARNING' ? 'bg-yellow-900 text-yellow-200' :
                    'bg-gray-700 text-gray-200'
                  }`}>
                    {log.level}
                  </span>
                  <span className="ml-2 text-purple-400">{log.agent_type}</span>
                  <span className="ml-2 text-gray-300">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-4">Agent Status</h2>
            <p className="text-gray-300">Agent management interface coming soon...</p>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold mb-4">Task History</h2>
            <p className="text-gray-300">Task history and management coming soon...</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App