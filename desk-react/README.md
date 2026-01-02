# Helpdesk React Frontend

A modern, professional React-based frontend for the Helpdesk application, built with industry-standard UI/UX patterns.

## 🎨 Design Philosophy

This frontend is built with clean, professional design principles:

- **Modern & Minimalist**: Clean interfaces inspired by industry leaders like Linear, Zendesk, and Notion
- **Neutral Color Palette**: Professional grays and whites with subtle accent colors
- **Excellent UX**: Proper loading states, error handling, and responsive design
- **Accessibility First**: Built on Radix UI primitives for full accessibility support
- **No Template Feel**: Custom-designed components with industry-standard patterns

## 🛠️ Tech Stack

### Core
- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Full type safety across the application
- **Vite** - Lightning-fast build tool and dev server
- **React Router 6** - Client-side routing

### State Management
- **Zustand** - Lightweight, modern state management
- **TanStack Query** - Server state management and caching

### UI Components
- **Shadcn/UI** - High-quality, accessible components built on Radix UI
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide Icons** - Modern, consistent icon set

### API Integration
- **Axios** - HTTP client for Frappe backend
- **Socket.io Client** - Real-time updates

## 📦 Project Structure

```
desk-react/
├── src/
│   ├── components/
│   │   ├── ui/              # Shadcn/UI components
│   │   └── layouts/         # Layout components (Agent/Customer)
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   ├── TicketList.tsx
│   │   ├── TicketDetail.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── CustomerTickets.tsx
│   │   └── CustomerTicketDetail.tsx
│   ├── stores/             # Zustand stores
│   │   ├── authStore.ts
│   │   └── ticketStore.ts
│   ├── lib/                # Utilities
│   │   ├── api.ts          # Frappe API client
│   │   └── utils.ts        # Helper functions
│   ├── types/              # TypeScript types
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Running Frappe backend (existing Helpdesk Python app)

### Installation

1. Navigate to the React frontend directory:
```bash
cd desk-react
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:8080`

### Development

The dev server proxies API requests to the Frappe backend at `http://localhost:8000`. Make sure your Frappe backend is running.

### Build for Production

```bash
npm run build
```

This builds the app and outputs to `../helpdesk/public/desk/`, ready to be served by the Frappe backend.

## 🎯 Features

### Agent Portal
- **Dashboard**: Key metrics, recent activity, quick actions
- **Ticket Management**: List view, detailed ticket view, assignments
- **Knowledge Base**: Browse articles, categories, and documentation
- **Real-time Updates**: Live ticket updates via WebSocket

### Customer Portal
- **My Tickets**: View all support tickets
- **Ticket Details**: Track ticket progress and communicate with support
- **Clean Self-Service**: Simple, focused customer experience

## 🔌 API Integration

### Frappe Backend Integration

The app integrates with the existing Frappe backend using:

1. **REST API**: Standard Frappe DocType CRUD operations
2. **RPC Calls**: Custom methods via `helpdesk.api.*`
3. **Authentication**: Session-based auth with CSRF tokens
4. **Real-time**: Socket.io for live updates

### API Client (`src/lib/api.ts`)

```typescript
import { call, getList, getDoc, createDoc, updateDoc } from '@/lib/api';

// RPC call
const data = await call('helpdesk.api.dashboard.get_dashboard_data');

// Get list
const tickets = await getList('HD Ticket', {
  filters: { status: 'Open' },
  limit_page_length: 20
});

// Get single document
const ticket = await getDoc('HD Ticket', 'TICKET-001');
```

## 🎨 Design System

### Colors
- **Primary**: Blue (`hsl(221.2 83.2% 53.3%)`) - CTAs and important actions
- **Muted**: Gray tones for backgrounds and subtle elements
- **Destructive**: Red for warnings and errors
- **Success**: Green for positive states

### Typography
- System font stack for native feel
- Clear hierarchy with font weights
- Proper line heights and spacing

### Components
All UI components follow consistent patterns:
- Proper hover/focus states
- Loading skeletons
- Error states
- Responsive design

## 🔧 Configuration

### Vite Config
- Proxy setup for API requests
- Build output to Frappe public directory
- Path aliases (`@/` → `./src/`)

### Tailwind Config
- Custom color scheme
- Extended utilities
- Animation support

## 📝 Development Guidelines

### Code Style
- Use TypeScript for all new files
- Follow React hooks best practices
- Use functional components
- Proper error handling

### State Management
- Use Zustand for client state
- Use TanStack Query for server state
- Keep stores focused and small

### Styling
- Use Tailwind utility classes
- Use `cn()` helper for conditional classes
- Follow mobile-first responsive design

## 🚢 Deployment

### Production Build
1. Build the React app: `npm run build`
2. The output goes to `../helpdesk/public/desk/`
3. Frappe serves these static files

### Environment Variables
No environment variables needed - configuration is inferred from the running environment.

## 🤝 Backend Compatibility

This frontend is designed to work with the existing Frappe Helpdesk backend **without any changes**:

- ✅ Uses existing API endpoints
- ✅ Compatible with Frappe authentication
- ✅ Works with existing DocTypes
- ✅ Supports all existing features

## 📄 License

Same as the parent Helpdesk project.
