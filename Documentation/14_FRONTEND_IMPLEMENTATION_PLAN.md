# Frontend Implementation Plan - AgentHub Multi-Agent Chatbot

**Document Version**: 1.0
**Created**: 2025-11-03
**Status**: Planning Phase
**Target Stack**: React 18 + TypeScript + Vite + Tailwind CSS

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pre-Implementation Checklist](#pre-implementation-checklist)
3. [Phase 1: Foundation Setup](#phase-1-foundation-setup)
4. [Phase 2: Core Chat Widget](#phase-2-core-chat-widget)
5. [Phase 3: Iframe Embedding](#phase-3-iframe-embedding)
6. [Phase 4: Admin Panel](#phase-4-admin-panel)
7. [Phase 5: Production Deployment](#phase-5-production-deployment)
8. [Testing Strategy](#testing-strategy)
9. [Performance Benchmarks](#performance-benchmarks)
10. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

### Current State
- ✅ **Backend**: Production-ready FastAPI with 7+ endpoints
- ✅ **Database**: 13 tables with multi-tenant architecture
- ✅ **APIs**: Fully documented (Swagger + ReDoc)
- ❌ **Frontend**: Does not exist - needs full implementation

### Target State
- 🎯 **Chat Widget**: Embeddable iframe widget for tenants
- 🎯 **Admin Panel**: Tenant/agent/tool management UI
- 🎯 **Monitoring**: Real-time dashboard for metrics
- 🎯 **Deployment**: Dockerized frontend + NGINX reverse proxy

### Timeline Estimate
| Phase | Duration | Priority |
|-------|----------|----------|
| Phase 1: Foundation | 3-5 days | P0 (Critical) |
| Phase 2: Chat Widget | 5-7 days | P0 (Critical) |
| Phase 3: Iframe Embedding | 3-4 days | P0 (Critical) |
| Phase 4: Admin Panel | 7-10 days | P1 (High) |
| Phase 5: Production Deployment | 2-3 days | P0 (Critical) |
| **Total** | **20-29 days** | |

---

## Pre-Implementation Checklist

### ✅ Prerequisites Verification

#### Backend Readiness
- [ ] Backend running on http://localhost:8000
- [ ] Health check endpoint responding: `GET /health`
- [ ] Swagger UI accessible: http://localhost:8000/docs
- [ ] PostgreSQL database initialized (check `docker-compose ps`)
- [ ] Redis cache running (check `docker-compose ps`)
- [ ] ChromaDB running on port 8001 (check `docker-compose ps`)

#### Authentication Setup
- [ ] JWT public key configured in `.env` (`JWT_PUBLIC_KEY`)
- [ ] Test JWT token available for development
- [ ] Understand JWT payload structure:
  ```json
  {
    "sub": "user-123",
    "tenant_id": "uuid",
    "email": "user@example.com",
    "roles": ["user"],
    "exp": 1699999999
  }
  ```

#### API Endpoints Verification
Test these endpoints manually:
- [ ] `POST /api/{tenant_id}/chat` - Returns ChatResponse
- [ ] `GET /api/{tenant_id}/sessions` - Returns session list
- [ ] `POST /api/admin/agents` - Admin agent creation works
- [ ] `POST /api/admin/tenants` - Tenant creation works

#### Development Environment
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm or pnpm installed (`npm --version`)
- [ ] Git configured
- [ ] Code editor (VSCode recommended)
- [ ] Docker Desktop running (for deployment testing)

#### Documentation Review
- [ ] Read: [01_CHATBOT_SPECIFICATION.md](01_CHATBOT_SPECIFICATION.md)
- [ ] Read: [02_SYSTEM_ARCHITECTURE.md](02_SYSTEM_ARCHITECTURE.md)
- [ ] Read: [05_API_REFERENCE_AND_GUIDES.md](05_API_REFERENCE_AND_GUIDES.md)
- [ ] Understand: Multi-tenant architecture
- [ ] Understand: Agent routing flow (SupervisorAgent → DomainAgent)

---

## Phase 1: Foundation Setup (3-5 days)

### 1.1 Project Initialization

#### Create Frontend Directory Structure
```bash
mkdir -p frontend/{src,public,tests}
cd frontend
```

#### Initialize Package Manager
- [ ] Run: `npm init -y` or `pnpm init`
- [ ] Create `.nvmrc` file with Node version: `18.18.0`
- [ ] Create `.gitignore` for frontend:
  ```
  node_modules/
  dist/
  .env.local
  .DS_Store
  *.log
  coverage/
  .vite/
  ```

#### Install Core Dependencies
```bash
# Framework
npm install react@18.2.0 react-dom@18.2.0

# Build Tool
npm install -D vite@5.0.0 @vitejs/plugin-react@4.2.0

# TypeScript
npm install -D typescript@5.3.0 @types/react@18.2.0 @types/react-dom@18.2.0

# Tailwind CSS
npm install -D tailwindcss@3.4.0 postcss@8.4.0 autoprefixer@10.4.0

# State Management
npm install zustand@4.4.0 @tanstack/react-query@5.0.0

# HTTP Client
npm install axios@1.6.0

# Utilities
npm install clsx@2.0.0 date-fns@3.0.0
```

**Checklist**:
- [ ] `package.json` created with all dependencies
- [ ] Versions locked (no `^` or `~` for stability)
- [ ] Run `npm install` successfully
- [ ] No dependency conflicts

---

### 1.2 TypeScript Configuration

#### Create `tsconfig.json`
- [ ] File created at `frontend/tsconfig.json`
- [ ] Includes strict mode enabled
- [ ] Path aliases configured (`@/` → `./src/`)
- [ ] JSX set to `react-jsx`

**Sample Configuration**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Validation**:
- [ ] TypeScript compiler doesn't error on empty project
- [ ] Path aliases work in import statements

---

### 1.3 Vite Configuration

#### Create `vite.config.ts`
- [ ] File created at `frontend/vite.config.ts`
- [ ] React plugin configured
- [ ] Path aliases match `tsconfig.json`
- [ ] Proxy configured for backend API
- [ ] Environment variable handling setup

**Key Configuration**:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'query-vendor': ['@tanstack/react-query'],
        },
      },
    },
  },
})
```

**Validation**:
- [ ] Dev server starts: `npm run dev`
- [ ] Builds successfully: `npm run build`
- [ ] Preview works: `npm run preview`

---

### 1.4 Tailwind CSS Setup

#### Initialize Tailwind
```bash
npx tailwindcss init -p
```

#### Configure `tailwind.config.js`
- [ ] Content paths include all React files
- [ ] Custom theme colors defined (primary, secondary)
- [ ] Dark mode configured (class-based)

**Sample Configuration**:
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
    },
  },
  plugins: [],
}
```

#### Create Global CSS
- [ ] File created: `src/index.css`
- [ ] Tailwind directives added
- [ ] Custom CSS variables defined

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --primary: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }
}
```

**Validation**:
- [ ] Tailwind classes apply correctly
- [ ] Dark mode toggle works
- [ ] Custom colors accessible

---

### 1.5 Environment Configuration

#### Create `.env.example`
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=10000

# Widget Configuration
VITE_WIDGET_CDN_URL=http://localhost:3000
VITE_ENABLE_DEBUG_MODE=true

# Feature Flags
VITE_ENABLE_VOICE_INPUT=false
VITE_ENABLE_FILE_UPLOAD=false
```

#### Create `.env.local` (gitignored)
- [ ] Copy from `.env.example`
- [ ] Add development-specific values
- [ ] Never commit to git

**Validation**:
- [ ] Environment variables accessible via `import.meta.env.VITE_*`
- [ ] `.env.local` in `.gitignore`

---

### 1.6 Directory Structure Creation

```
frontend/
├── public/
│   ├── widget.html          # Iframe host page
│   └── favicon.ico
├── src/
│   ├── assets/              # Images, fonts
│   ├── components/          # React components
│   │   ├── chat/           # Chat-specific components
│   │   ├── admin/          # Admin panel components
│   │   ├── common/         # Shared components (Button, Input)
│   │   └── layout/         # Layout components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API clients
│   ├── stores/             # Zustand stores
│   ├── types/              # TypeScript types
│   ├── utils/              # Helper functions
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

**Checklist**:
- [ ] All directories created
- [ ] `.gitkeep` files in empty directories
- [ ] README.md with setup instructions

---

### 1.7 Type Definitions

#### Create Core Types
File: `src/types/api.ts`

```typescript
// Message Types
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agent?: string
  format?: MessageFormat
  data?: any
  renderer_hint?: RendererHint
  timestamp: Date
}

export type MessageFormat =
  | 'text'
  | 'structured_json'
  | 'markdown_table'
  | 'chart_data'

export interface RendererHint {
  type: 'table' | 'chart' | 'json' | 'text'
  fields?: string[]
  sortable?: boolean
  filterable?: boolean
  chart_type?: 'line' | 'bar' | 'pie'
}

// Chat API Types
export interface ChatRequest {
  message: string
  session_id?: string
  user_id: string
  metadata?: Record<string, any>
}

export interface ChatResponse {
  session_id: string
  message_id: string
  response: string
  agent: string
  intent: string
  format: MessageFormat
  renderer_hint: RendererHint
  metadata: ChatMetadata
}

export interface ChatMetadata {
  agent_id: string
  tenant_id: string
  duration_ms: number
  status: 'success' | 'error'
  llm_model: string
  tool_calls: string[]
  extracted_entities: Record<string, any>
}

// Session Types
export interface ChatSession {
  session_id: string
  tenant_id: string
  user_id: string
  agent_name?: string
  created_at: string
  last_message_at?: string
  message_count: number
  metadata?: Record<string, any>
}

// Tenant Types
export interface Tenant {
  tenant_id: string
  name: string
  domain: string
  status: 'active' | 'inactive'
}

// Widget Config Types
export interface WidgetConfig {
  tenant_id: string
  widget_key: string
  theme: 'light' | 'dark' | 'auto'
  primary_color: string
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  auto_open: boolean
  welcome_message?: string
  allowed_domains: string[]
}
```

**Validation**:
- [ ] All types compile without errors
- [ ] Types match backend API schemas
- [ ] Export/import works correctly

---

### 1.8 API Service Layer

#### Create Base API Client
File: `src/services/api.ts`

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 10000

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor - inject JWT
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle token expiration
          this.handleAuthError()
        }
        return Promise.reject(error)
      }
    )
  }

  private getAuthToken(): string | null {
    // TODO: Implement token retrieval from secure storage
    return localStorage.getItem('auth_token')
  }

  private handleAuthError(): void {
    // TODO: Implement token refresh or redirect to login
    localStorage.removeItem('auth_token')
    window.dispatchEvent(new Event('auth:expired'))
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new APIClient()
```

**Validation**:
- [ ] API client instantiates without errors
- [ ] Interceptors configured correctly
- [ ] TypeScript types enforced

---

### 1.9 Phase 1 Validation

#### Build Verification
- [ ] `npm run build` completes successfully
- [ ] No TypeScript errors
- [ ] No ESLint errors (if configured)
- [ ] Bundle size <500KB (initial)

#### Development Server
- [ ] `npm run dev` starts on port 3000
- [ ] Hot Module Replacement (HMR) works
- [ ] Tailwind classes apply
- [ ] API proxy works (test with `/api/health`)

#### Git Commit
- [ ] All files committed
- [ ] Commit message: `feat: Phase 1 - Frontend foundation setup`
- [ ] Branch: `feature/frontend-foundation`

---

## Phase 2: Core Chat Widget (5-7 days)

### 2.1 Chat Store (Zustand)

#### Create Chat Store
File: `src/stores/useChatStore.ts`

```typescript
import { create } from 'zustand'
import { Message, ChatSession } from '@/types/api'

interface ChatState {
  // State
  messages: Message[]
  currentSession: ChatSession | null
  isLoading: boolean
  error: string | null

  // Actions
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  setSession: (session: ChatSession) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearChat: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentSession: null,
  isLoading: false,
  error: null,

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  setMessages: (messages) => set({ messages }),

  setSession: (session) => set({ currentSession: session }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearChat: () => set({ messages: [], currentSession: null, error: null }),
}))
```

**Checklist**:
- [ ] Store created with TypeScript
- [ ] All actions implemented
- [ ] No memory leaks (Zustand handles cleanup)

---

### 2.2 Chat API Service

#### Create Chat Service
File: `src/services/chatService.ts`

```typescript
import { apiClient } from './api'
import { ChatRequest, ChatResponse, ChatSession } from '@/types/api'

export class ChatService {
  async sendMessage(
    tenantId: string,
    request: ChatRequest
  ): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>(
      `/api/${tenantId}/chat`,
      request
    )
  }

  async getSessions(
    tenantId: string,
    userId: string,
    limit = 50,
    offset = 0
  ): Promise<{ sessions: ChatSession[], total: number }> {
    return apiClient.get(
      `/api/${tenantId}/sessions`,
      { user_id: userId, limit, offset }
    )
  }

  async getSessionMessages(
    tenantId: string,
    sessionId: string
  ): Promise<Message[]> {
    // TODO: Implement when backend endpoint exists
    return []
  }
}

export const chatService = new ChatService()
```

**Validation**:
- [ ] Service methods typed correctly
- [ ] Error handling in place
- [ ] Can be mocked for testing

---

### 2.3 useChat Hook

#### Create Custom Hook
File: `src/hooks/useChat.ts`

```typescript
import { useState, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useChatStore } from '@/stores/useChatStore'
import { chatService } from '@/services/chatService'
import { Message } from '@/types/api'
import { v4 as uuidv4 } from 'uuid'

interface UseChatOptions {
  tenantId: string
  userId: string
  sessionId?: string
}

export function useChat({ tenantId, userId, sessionId }: UseChatOptions) {
  const { messages, addMessage, setLoading, setError } = useChatStore()
  const [currentSessionId, setCurrentSessionId] = useState(sessionId)

  const sendMessage = useMutation({
    mutationFn: async (text: string) => {
      // Add user message immediately
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      }
      addMessage(userMessage)
      setLoading(true)

      // Call backend
      const response = await chatService.sendMessage(tenantId, {
        message: text,
        session_id: currentSessionId,
        user_id: userId,
      })

      // Update session ID if new
      if (response.session_id !== currentSessionId) {
        setCurrentSessionId(response.session_id)
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        agent: response.agent,
        format: response.format,
        data: response.metadata,
        renderer_hint: response.renderer_hint,
        timestamp: new Date(),
      }
      addMessage(assistantMessage)
      setLoading(false)

      return response
    },
    onError: (error: Error) => {
      setError(error.message)
      setLoading(false)
    },
  })

  const loadSessions = useQuery({
    queryKey: ['sessions', tenantId, userId],
    queryFn: () => chatService.getSessions(tenantId, userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  return {
    messages,
    sendMessage: useCallback(
      (text: string) => sendMessage.mutate(text),
      [sendMessage]
    ),
    isLoading: sendMessage.isPending,
    error: sendMessage.error?.message,
    sessions: loadSessions.data?.sessions || [],
  }
}
```

**Validation**:
- [ ] Hook works with React Query
- [ ] State updates correctly
- [ ] Error handling functional

---

### 2.4 Chat UI Components

#### MessageBubble Component
File: `src/components/chat/MessageBubble.tsx`

```typescript
import { Message } from '@/types/api'
import { formatDistanceToNow } from 'date-fns'
import { MessageRenderer } from './MessageRenderer'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-primary-500 text-white'
            : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
        }`}
      >
        {!isUser && message.agent && (
          <div className="text-xs opacity-70 mb-1">
            Agent: {message.agent}
          </div>
        )}

        <MessageRenderer message={message} />

        <div className="text-xs opacity-70 mt-1">
          {formatDistanceToNow(message.timestamp, { addSuffix: true })}
        </div>
      </div>
    </div>
  )
}
```

**Checklist**:
- [ ] Component renders correctly
- [ ] Styling works for both roles
- [ ] Dark mode supported

---

#### MessageList Component
File: `src/components/chat/MessageList.tsx`

```typescript
import { useEffect, useRef } from 'react'
import { Message } from '@/types/api'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
            <div className="flex items-center space-x-2">
              <div className="animate-pulse">●</div>
              <span className="text-sm text-gray-500">Thinking...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
```

**Validation**:
- [ ] Auto-scroll works
- [ ] Loading indicator shows
- [ ] Performance good with 100+ messages

---

#### InputBox Component
File: `src/components/chat/InputBox.tsx`

```typescript
import { useState, KeyboardEvent } from 'react'

interface InputBoxProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function InputBox({
  onSend,
  disabled = false,
  placeholder = 'Type your message...'
}: InputBoxProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t dark:border-gray-700 p-4">
      <div className="flex items-end space-x-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="bg-primary-500 text-white rounded-lg px-6 py-2 hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}
```

**Validation**:
- [ ] Enter key sends message
- [ ] Shift+Enter adds new line
- [ ] Disabled state works

---

#### ChatContainer Component
File: `src/components/chat/ChatContainer.tsx`

```typescript
import { useChat } from '@/hooks/useChat'
import { MessageList } from './MessageList'
import { InputBox } from './InputBox'

interface ChatContainerProps {
  tenantId: string
  userId: string
  sessionId?: string
  welcomeMessage?: string
}

export function ChatContainer({
  tenantId,
  userId,
  sessionId,
  welcomeMessage
}: ChatContainerProps) {
  const { messages, sendMessage, isLoading, error } = useChat({
    tenantId,
    userId,
    sessionId,
  })

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="border-b dark:border-gray-700 p-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          AgentHub Chat
        </h2>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input */}
      <InputBox onSend={sendMessage} disabled={isLoading} />
    </div>
  )
}
```

**Validation**:
- [ ] Full chat flow works
- [ ] Error display functional
- [ ] Responsive layout

---

### 2.5 MessageRenderer (Format Support)

File: `src/components/chat/MessageRenderer.tsx`

```typescript
import { Message } from '@/types/api'
import { JSONViewer } from './renderers/JSONViewer'
import { MarkdownTable } from './renderers/MarkdownTable'
import { ChartRenderer } from './renderers/ChartRenderer'

interface MessageRendererProps {
  message: Message
}

export function MessageRenderer({ message }: MessageRendererProps) {
  switch (message.format) {
    case 'structured_json':
      return <JSONViewer data={message.data} />

    case 'markdown_table':
      return <MarkdownTable markdown={message.content} />

    case 'chart_data':
      return <ChartRenderer data={message.data} hints={message.renderer_hint} />

    case 'text':
    default:
      return (
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
      )
  }
}
```

**Checklist**:
- [ ] All format types handled
- [ ] Graceful fallback to text
- [ ] Renderers lazy-loaded

---

### 2.6 Phase 2 Validation

#### Component Testing
- [ ] All chat components render
- [ ] Message sending works end-to-end
- [ ] Loading states display correctly
- [ ] Error handling works
- [ ] Dark mode toggles properly

#### Integration Testing
- [ ] Chat flow: user message → backend → assistant response
- [ ] Session persistence works
- [ ] Multiple messages in conversation
- [ ] Rate limiting handled gracefully

#### Performance
- [ ] Initial load <2 seconds
- [ ] Message send <2.5 seconds (backend SLA)
- [ ] Smooth scrolling with 100+ messages
- [ ] No memory leaks

#### Git Commit
- [ ] Commit: `feat: Phase 2 - Core chat widget implementation`
- [ ] Branch: `feature/chat-widget`

---

## Phase 3: Iframe Embedding (3-4 days)

### 3.1 Widget Loader Script

#### Create Embed Script
File: `public/embed.js`

```javascript
(function () {
  'use strict';

  // Configuration from script tag attributes or container data attributes
  const script = document.currentScript;
  const container = document.querySelector('#agenthub-chat');

  if (!container) {
    console.error('[AgentHub] Container #agenthub-chat not found');
    return;
  }

  // Extract configuration
  const config = {
    tenantId: container.dataset.tenantId || script.dataset.tenantId,
    widgetKey: container.dataset.widgetKey || script.dataset.widgetKey,
    theme: container.dataset.theme || 'light',
    position: container.dataset.position || 'bottom-right',
    autoOpen: container.dataset.autoOpen === 'true',
  };

  // Validate required config
  if (!config.tenantId || !config.widgetKey) {
    console.error('[AgentHub] Missing required attributes: data-tenant-id, data-widget-key');
    return;
  }

  // Create iframe
  const iframe = document.createElement('iframe');
  const widgetUrl = new URL(script.src);
  widgetUrl.pathname = '/widget.html';
  widgetUrl.search = new URLSearchParams({
    tenant: config.tenantId,
    key: config.widgetKey,
    theme: config.theme,
    autoOpen: config.autoOpen,
  }).toString();

  iframe.src = widgetUrl.toString();
  iframe.style.cssText = `
    position: fixed;
    ${config.position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
    ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
    width: 400px;
    height: 600px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    transition: all 0.3s ease;
  `;
  iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
  iframe.setAttribute('title', 'AgentHub Chat Widget');

  container.appendChild(iframe);

  // PostMessage communication
  window.addEventListener('message', (event) => {
    // Validate origin
    if (event.origin !== widgetUrl.origin) return;

    if (event.data.type === 'RESIZE') {
      iframe.style.height = event.data.height + 'px';
    }

    if (event.data.type === 'CLOSE') {
      iframe.style.display = 'none';
    }

    if (event.data.type === 'OPEN') {
      iframe.style.display = 'block';
    }
  });
})();
```

**Checklist**:
- [ ] Script creates iframe dynamically
- [ ] Configuration passed via URL params
- [ ] Sandbox attributes set correctly
- [ ] PostMessage handler registered

---

### 3.2 Widget Host Page

#### Create Widget HTML
File: `public/widget.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AgentHub Widget</title>
</head>
<body>
  <div id="widget-root"></div>
  <script type="module" src="/src/widget.tsx"></script>
</body>
</html>
```

---

#### Create Widget Entry Point
File: `src/widget.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { WidgetApp } from './WidgetApp'
import './index.css'

// Parse URL params
const params = new URLSearchParams(window.location.search)
const config = {
  tenantId: params.get('tenant') || '',
  widgetKey: params.get('key') || '',
  theme: params.get('theme') || 'light',
  autoOpen: params.get('autoOpen') === 'true',
}

ReactDOM.createRoot(document.getElementById('widget-root')!).render(
  <React.StrictMode>
    <WidgetApp config={config} />
  </React.StrictMode>
)
```

---

#### Create Widget App Component
File: `src/WidgetApp.tsx`

```typescript
import { useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatContainer } from './components/chat/ChatContainer'

interface WidgetAppProps {
  config: {
    tenantId: string
    widgetKey: string
    theme: string
    autoOpen: boolean
  }
}

const queryClient = new QueryClient()

export function WidgetApp({ config }: WidgetAppProps) {
  const [userId] = useState(() => getUserId()) // Get from JWT or cookie
  const [isMinimized, setIsMinimized] = useState(!config.autoOpen)

  // Apply theme
  useEffect(() => {
    document.documentElement.classList.toggle('dark', config.theme === 'dark')
  }, [config.theme])

  // PostMessage to parent for resize
  useEffect(() => {
    const height = isMinimized ? 80 : 600
    window.parent.postMessage({ type: 'RESIZE', height }, '*')
  }, [isMinimized])

  if (isMinimized) {
    return (
      <button
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-4 right-4 bg-primary-500 text-white rounded-full p-4 shadow-lg hover:bg-primary-600 transition-colors"
      >
        💬 Chat
      </button>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen flex flex-col">
        <ChatContainer
          tenantId={config.tenantId}
          userId={userId}
          welcomeMessage="Hello! How can I help you today?"
        />
        <button
          onClick={() => setIsMinimized(true)}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
    </QueryClientProvider>
  )
}

function getUserId(): string {
  // TODO: Extract from JWT or generate anonymous ID
  return 'user-' + Math.random().toString(36).substr(2, 9)
}
```

**Validation**:
- [ ] Widget loads in iframe
- [ ] Minimize/maximize works
- [ ] PostMessage communication works
- [ ] Theme applies correctly

---

### 3.3 Backend Widget Config API

#### Create Widget Config Endpoint
File: `backend/src/api/admin/widget.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.tenant_widget_config import TenantWidgetConfig
from ...schemas.admin import WidgetConfigCreate, WidgetConfigResponse
from ...middleware.auth import require_admin
from ...utils.encryption import encrypt_fernet, decrypt_fernet
import secrets

router = APIRouter(prefix="/admin/widget", tags=["admin-widget"])

@router.post("/", response_model=WidgetConfigResponse)
async def create_widget_config(
    config: WidgetConfigCreate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Create widget configuration for tenant."""

    # Generate widget key and secret
    widget_key = f"wk_{secrets.token_urlsafe(32)}"
    widget_secret = secrets.token_urlsafe(64)

    # Create config
    widget_config = TenantWidgetConfig(
        tenant_id=config.tenant_id,
        widget_key=widget_key,
        widget_secret=encrypt_fernet(widget_secret),
        theme=config.theme,
        primary_color=config.primary_color,
        position=config.position,
        allowed_domains=config.allowed_domains,
        embed_script_url=f"{config.cdn_base_url}/embed.js",
        embed_code_snippet=generate_embed_snippet(widget_key, config.cdn_base_url)
    )

    db.add(widget_config)
    db.commit()
    db.refresh(widget_config)

    return widget_config

def generate_embed_snippet(widget_key: str, cdn_url: str) -> str:
    """Generate ready-to-copy embed code."""
    return f'''<!-- AgentHub Chat Widget -->
<div id="agenthub-chat"
     data-widget-key="{widget_key}"></div>
<script src="{cdn_url}/embed.js" async></script>
'''

@router.get("/{tenant_id}", response_model=WidgetConfigResponse)
async def get_widget_config(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get widget configuration by tenant ID."""
    config = db.query(TenantWidgetConfig).filter_by(tenant_id=tenant_id).first()
    if not config:
        raise HTTPException(404, "Widget config not found")
    return config
```

**Checklist**:
- [ ] Endpoint creates widget config
- [ ] Widget key generated securely
- [ ] Embed snippet returned
- [ ] API tested with Swagger

---

### 3.4 Phase 3 Validation

#### Embedding Testing
- [ ] Copy embed snippet to test HTML page
- [ ] Widget loads in iframe
- [ ] Configuration applies (theme, position)
- [ ] PostMessage communication works
- [ ] CORS configured correctly

#### Security Testing
- [ ] Iframe sandbox prevents malicious scripts
- [ ] PostMessage origin validation works
- [ ] Widget key validated on backend
- [ ] No XSS vulnerabilities

#### Cross-Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

#### Git Commit
- [ ] Commit: `feat: Phase 3 - Iframe embedding implementation`
- [ ] Branch: `feature/iframe-widget`

---

## Phase 4: Admin Panel (7-10 days)

### 4.1 Admin Routes

#### Create Admin Layout
File: `src/components/admin/AdminLayout.tsx`

```typescript
import { Outlet, NavLink } from 'react-router-dom'

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <NavLink to="/admin/tenants" className="nav-link">
                Tenants
              </NavLink>
              <NavLink to="/admin/agents" className="nav-link">
                Agents
              </NavLink>
              <NavLink to="/admin/tools" className="nav-link">
                Tools
              </NavLink>
              <NavLink to="/admin/widget" className="nav-link">
                Widget Config
              </NavLink>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
```

---

### 4.2 Tenant Management

#### Tenant List Component
File: `src/components/admin/TenantList.tsx`

```typescript
import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { Tenant } from '@/types/api'

export function TenantList() {
  const { data, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => adminService.getTenants(),
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Tenants</h1>
        <button className="btn-primary">Add Tenant</button>
      </div>

      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th>Name</th>
            <th>Domain</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.tenants.map((tenant: Tenant) => (
            <tr key={tenant.tenant_id}>
              <td>{tenant.name}</td>
              <td>{tenant.domain}</td>
              <td>
                <span className={`badge ${tenant.status === 'active' ? 'badge-success' : 'badge-inactive'}`}>
                  {tenant.status}
                </span>
              </td>
              <td>{new Date(tenant.created_at).toLocaleDateString()}</td>
              <td>
                <button className="text-primary-500">Edit</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

**Checklist**:
- [ ] Tenant list displays
- [ ] Add tenant form works
- [ ] Edit tenant updates correctly
- [ ] Status toggle functional

---

### 4.3 Agent Management

#### Agent List Component
File: `src/components/admin/AgentList.tsx`

*(Similar structure to TenantList)*

**Checklist**:
- [ ] Agent list displays
- [ ] Create agent form works
- [ ] Prompt editor functional
- [ ] Tool assignment works

---

### 4.4 Widget Configuration UI

#### Widget Config Component
File: `src/components/admin/WidgetConfig.tsx`

```typescript
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'

export function WidgetConfig({ tenantId }: { tenantId: string }) {
  const [theme, setTheme] = useState('light')
  const [primaryColor, setPrimaryColor] = useState('#3B82F6')
  const [position, setPosition] = useState('bottom-right')

  const createConfig = useMutation({
    mutationFn: (config) => adminService.createWidgetConfig(tenantId, config),
  })

  const handleSubmit = () => {
    createConfig.mutate({
      theme,
      primary_color: primaryColor,
      position,
      allowed_domains: ['*'], // TODO: Make configurable
    })
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Widget Configuration</h2>

      {/* Theme Selector */}
      <div>
        <label className="block text-sm font-medium mb-2">Theme</label>
        <select value={theme} onChange={(e) => setTheme(e.target.value)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="auto">Auto</option>
        </select>
      </div>

      {/* Color Picker */}
      <div>
        <label className="block text-sm font-medium mb-2">Primary Color</label>
        <input
          type="color"
          value={primaryColor}
          onChange={(e) => setPrimaryColor(e.target.value)}
        />
      </div>

      {/* Position Selector */}
      <div>
        <label className="block text-sm font-medium mb-2">Position</label>
        <select value={position} onChange={(e) => setPosition(e.target.value)}>
          <option value="bottom-right">Bottom Right</option>
          <option value="bottom-left">Bottom Left</option>
          <option value="top-right">Top Right</option>
          <option value="top-left">Top Left</option>
        </select>
      </div>

      {/* Embed Code Display */}
      {createConfig.data && (
        <div>
          <label className="block text-sm font-medium mb-2">Embed Code</label>
          <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
            {createConfig.data.embed_code_snippet}
          </pre>
        </div>
      )}

      <button onClick={handleSubmit} className="btn-primary">
        Generate Widget Code
      </button>
    </div>
  )
}
```

**Validation**:
- [ ] Widget config form submits
- [ ] Embed code displays after creation
- [ ] Copy-to-clipboard works
- [ ] Preview shows configuration

---

### 4.5 Phase 4 Validation

#### Admin Panel Testing
- [ ] All CRUD operations work
- [ ] Forms validate input
- [ ] Tables paginate correctly
- [ ] Search/filter functional

#### Git Commit
- [ ] Commit: `feat: Phase 4 - Admin panel implementation`
- [ ] Branch: `feature/admin-panel`

---

## Phase 5: Production Deployment (2-3 days)

### 5.1 Docker Configuration

#### Create Dockerfile
File: `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

#### Create nginx.conf
File: `frontend/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Proxy API requests to backend
        location /api {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
```

**Checklist**:
- [ ] Dockerfile builds successfully
- [ ] NGINX config valid
- [ ] Static assets served correctly
- [ ] API proxy works

---

### 5.2 Docker Compose Integration

#### Update docker-compose.yml
File: `docker-compose.yml` (project root)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agenthub
      POSTGRES_USER: agenthub
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://agenthub:${POSTGRES_PASSWORD}@postgres:5432/agenthub
      REDIS_URL: redis://redis:6379
      CHROMADB_URL: http://chromadb:8000
    depends_on:
      - postgres
      - redis
      - chromadb
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "3000:80"

volumes:
  postgres_data:
```

**Validation**:
- [ ] All services start: `docker-compose up`
- [ ] Frontend accessible on port 3000
- [ ] Backend accessible on port 8000
- [ ] Services communicate correctly

---

### 5.3 Environment Configuration

#### Create .env.production
File: `frontend/.env.production`

```env
VITE_API_BASE_URL=https://api.agenthub.com
VITE_WIDGET_CDN_URL=https://widget.agenthub.com
VITE_ENABLE_DEBUG_MODE=false
```

**Checklist**:
- [ ] Production URLs configured
- [ ] Debug mode disabled
- [ ] API keys not hardcoded

---

### 5.4 Phase 5 Validation

#### Deployment Testing
- [ ] Docker build succeeds
- [ ] Docker Compose starts all services
- [ ] Frontend loads in production mode
- [ ] API calls work through NGINX proxy
- [ ] Static assets served with correct headers
- [ ] SSL/TLS configured (if applicable)

#### Performance Testing
- [ ] Lighthouse score >90
- [ ] Bundle size <500KB (gzipped)
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s

#### Git Commit
- [ ] Commit: `feat: Phase 5 - Production deployment configuration`
- [ ] Branch: `feature/deployment`
- [ ] Merge to `main`

---

## Testing Strategy

### Unit Testing

#### Setup Vitest
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

#### Example Test
File: `tests/unit/MessageBubble.test.tsx`

```typescript
import { render, screen } from '@testing-library/react'
import { MessageBubble } from '@/components/chat/MessageBubble'

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date(),
    }

    render(<MessageBubble message={message} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

**Checklist**:
- [ ] All components have tests
- [ ] Coverage >80%
- [ ] Tests run in CI

---

### Integration Testing

#### Test Chat Flow
File: `tests/integration/chat.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatContainer } from '@/components/chat/ChatContainer'

describe('Chat Integration', () => {
  it('sends message and receives response', async () => {
    render(<ChatContainer tenantId="test" userId="user1" />)

    const input = screen.getByPlaceholderText('Type your message...')
    await userEvent.type(input, 'Hello')
    await userEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText(/Hello/)).toBeInTheDocument()
    })
  })
})
```

**Checklist**:
- [ ] End-to-end flows tested
- [ ] API mocking works
- [ ] Error scenarios covered

---

### E2E Testing (Playwright)

```bash
npm install -D @playwright/test
```

File: `tests/e2e/widget.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test('widget embeds and works', async ({ page }) => {
  await page.goto('http://localhost:3000/widget.html')
  await page.fill('textarea', 'What is the debt for MST 0123456789?')
  await page.click('button:has-text("Send")')

  await expect(page.locator('.message-bubble')).toContainText('debt')
})
```

**Checklist**:
- [ ] Widget embedding tested
- [ ] Cross-browser tests pass
- [ ] Mobile responsive tested

---

## Performance Benchmarks

### Target Metrics
| Metric | Target | Critical |
|--------|--------|----------|
| Bundle size (gzipped) | <300KB | <500KB |
| First Contentful Paint | <1.5s | <2.5s |
| Time to Interactive | <3s | <5s |
| Lighthouse Performance | >90 | >80 |
| API response time | <2.5s | <5s |

### Optimization Checklist
- [ ] Code splitting implemented
- [ ] Lazy loading for heavy components
- [ ] Image optimization (WebP, lazy load)
- [ ] Tree shaking enabled
- [ ] Minification enabled
- [ ] Gzip compression on server
- [ ] CDN for static assets (production)

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **CORS issues** | High | Configure backend CORS correctly, test cross-origin |
| **JWT token expiration** | Medium | Implement token refresh, handle 401 gracefully |
| **Iframe sandbox limitations** | Medium | Test PostMessage, document sandbox attributes |
| **Bundle size bloat** | Low | Monitor bundle analyzer, lazy load |
| **Browser compatibility** | Medium | Test on all major browsers, use polyfills |

---

## Completion Criteria

### Definition of Done
- [ ] All phases completed (1-5)
- [ ] All validation checklists passed
- [ ] Tests passing (unit, integration, e2e)
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Code reviewed and merged
- [ ] Deployed to production successfully

### Deliverables
- [ ] Chat widget (embeddable iframe)
- [ ] Admin panel (tenant/agent/tool management)
- [ ] Widget configuration API
- [ ] Embed script for tenants
- [ ] Docker deployment setup
- [ ] Test suite (>80% coverage)
- [ ] Developer documentation
- [ ] User guide for admins

---

## Next Steps After Completion

### Phase 6: Enhancements (Future)
- [ ] Voice input (Web Speech API)
- [ ] File upload support
- [ ] Conversation export
- [ ] Advanced RAG features
- [ ] Real-time streaming (SSE/WebSocket)
- [ ] Mobile native apps
- [ ] Multi-language UI support
- [ ] Custom theming per tenant

---

**Document Status**: ✅ Ready for Implementation
**Review Date**: 2025-11-03
**Next Review**: After Phase 2 completion

---

## Quick Reference

### Key Commands
```bash
# Development
npm run dev              # Start dev server (port 3000)
npm run build            # Production build
npm run preview          # Preview production build

# Testing
npm run test             # Run unit tests
npm run test:integration # Run integration tests
npm run test:e2e         # Run E2E tests

# Deployment
docker-compose up        # Start all services
docker-compose build     # Rebuild containers
```

### Key Files
| File | Purpose |
|------|---------|
| `src/main.tsx` | App entry point |
| `src/widget.tsx` | Widget entry point |
| `public/embed.js` | Embed script for tenants |
| `vite.config.ts` | Build configuration |
| `docker-compose.yml` | Production deployment |

### Helpful Links
- Backend API Docs: http://localhost:8000/docs
- Frontend Dev Server: http://localhost:3000
- Widget Demo: http://localhost:3000/widget.html

---

**End of Frontend Implementation Plan**
