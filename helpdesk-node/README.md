# Helpdesk Node.js Backend

Modern, production-ready Node.js backend for the Helpdesk application, built with Express, TypeScript, Prisma, and PostgreSQL/MySQL.

## 🚀 Features

### Core Functionality
- ✅ **User Authentication** - JWT-based auth with refresh tokens
- ✅ **Ticket Management** - Full CRUD operations with status tracking
- ✅ **Comments & Activity** - Ticket comments and audit trail
- ✅ **Dashboard Analytics** - Metrics and performance tracking
- ✅ **Knowledge Base** - Articles and categories management
- ✅ **Role-Based Access** - Agent, Customer, and Admin roles
- ✅ **File Attachments** - Support for ticket/comment attachments

### Technical Features
- 🔒 **Security** - Helmet, CORS, rate limiting
- 📝 **Validation** - Zod schema validation
- 🗄️ **Database** - Prisma ORM with PostgreSQL/MySQL
- 🔄 **Real-time** - Socket.io support (ready to implement)
- 📧 **Email** - Nodemailer integration (ready to implement)
- 🏃 **Background Jobs** - Bull queue with Redis (ready to implement)
- 📊 **Logging** - Winston logger with file rotation
- ⚡ **Performance** - Compression and caching

## 📋 Prerequisites

- Node.js >= 18.0.0
- PostgreSQL 14+ or MySQL 8+
- Redis (for caching and jobs)
- npm/yarn/pnpm

## 🛠️ Installation

### 1. Clone and Install

```bash
cd helpdesk-node
npm install
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/helpdesk"
JWT_SECRET="your-secret-key-change-this"
REDIS_HOST="localhost"
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

### 3. Database Setup

```bash
# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate

# (Optional) Open Prisma Studio
npm run prisma:studio
```

### 4. Start Development Server

```bash
npm run dev
```

Server runs at: **http://localhost:3000**

## 📁 Project Structure

```
helpdesk-node/
├── src/
│   ├── config/          # Configuration files
│   ├── controllers/     # Request handlers
│   ├── services/        # Business logic
│   ├── routes/          # API routes
│   ├── middleware/      # Auth, validation, error handling
│   ├── utils/           # Utilities (logger, prisma, errors, jwt)
│   ├── types/           # TypeScript type definitions
│   └── server.ts        # Express server setup
├── prisma/
│   └── schema.prisma    # Database schema
├── tests/               # Test files
├── logs/                # Application logs
├── uploads/             # File uploads
├── package.json
├── tsconfig.json
└── .env
```

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register      # Register new user
POST   /api/auth/login         # Login user
GET    /api/auth/me            # Get current user
POST   /api/auth/logout        # Logout user
```

### Tickets
```
POST   /api/tickets            # Create ticket
GET    /api/tickets            # List tickets (with filters)
GET    /api/tickets/:id        # Get ticket by ID
PATCH  /api/tickets/:id        # Update ticket
DELETE /api/tickets/:id        # Delete ticket (admin only)
POST   /api/tickets/:id/comments   # Add comment
POST   /api/tickets/:id/assign    # Assign ticket to agent
```

### Dashboard
```
GET    /api/dashboard/metrics  # Get dashboard metrics
```

### Knowledge Base
```
POST   /api/kb/articles        # Create article (agents only)
GET    /api/kb/articles        # List articles
GET    /api/kb/articles/:id    # Get article by ID
PATCH  /api/kb/articles/:id    # Update article
DELETE /api/kb/articles/:id    # Delete article
POST   /api/kb/categories      # Create category
GET    /api/kb/categories      # List categories
GET    /api/kb/categories/:id  # Get category with articles
```

## 🔐 Authentication

All protected endpoints require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:3000/api/tickets
```

### Example: Login & Use Token

```bash
# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Response includes accessToken
# Use it in subsequent requests:
curl -H "Authorization: Bearer eyJhbGc..." \
     http://localhost:3000/api/auth/me
```

## 👥 User Roles

### Customer
- Create and view own tickets
- Add comments to own tickets
- Limited to customer-facing fields

### Agent
- View assigned/team tickets
- Assign tickets
- Add internal comments
- Manage knowledge base

### Admin
- Full access to all features
- Delete tickets
- Manage users and settings

## 🗄️ Database Schema

### Core Models
- **User** - Authentication and user data
- **Agent** - Agent profiles and team assignments
- **Customer** - Customer profiles and metadata
- **Team** - Agent team grouping
- **Ticket** - Support tickets with SLA tracking
- **Comment** - Ticket comments (public/internal)
- **Activity** - Audit trail of changes
- **Attachment** - File uploads
- **Article** - Knowledge base articles
- **Category** - Article categorization
- **Notification** - In-app notifications
- **SLA** - Service level agreements
- **RefreshToken** - JWT refresh token management

## 📊 Prisma Commands

```bash
# Generate Prisma Client
npm run prisma:generate

# Create migration
npm run prisma:migrate

# Open Prisma Studio
npm run prisma:studio

# Reset database (WARNING: deletes all data)
npx prisma migrate reset
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## 📦 Building for Production

```bash
# Build TypeScript
npm run build

# Start production server
npm start
```

## 🚀 Deployment

### Environment Variables

Ensure these are set in production:

```env
NODE_ENV=production
DATABASE_URL=<production-database-url>
JWT_SECRET=<strong-secret-key>
REDIS_HOST=<redis-host>
SMTP_HOST=<smtp-server>
```

### Docker Deployment (Optional)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Use environment variables
2. **Use strong JWT secrets** - Generate random, long secrets
3. **Enable HTTPS** - Use SSL/TLS in production
4. **Rate limiting** - Already configured, adjust as needed
5. **Input validation** - Zod validation on all endpoints
6. **SQL injection** - Prisma prevents this automatically
7. **XSS protection** - Helmet middleware enabled

## 📈 Performance Optimization

- **Database indexing** - Defined in Prisma schema
- **Response compression** - Enabled via compression middleware
- **Redis caching** - Ready to implement for frequent queries
- **Connection pooling** - Prisma handles automatically

## 🐛 Debugging

```bash
# Enable debug logs
LOG_LEVEL=debug npm run dev

# Check logs
tail -f logs/combined.log
tail -f logs/error.log
```

## 🤝 Integration with React Frontend

This backend is designed to work seamlessly with the React frontend in `/desk-react`:

1. **Update React API client** (`desk-react/src/lib/api.ts`):
```typescript
const api = axios.create({
  baseURL: 'http://localhost:3000/api',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
  },
});
```

2. **Update authentication flow** to use JWT instead of Frappe sessions

3. **WebSocket connection** (when implemented):
```typescript
import io from 'socket.io-client';
const socket = io('http://localhost:3000', {
  auth: { token: localStorage.getItem('token') }
});
```

## 📝 Next Steps

### Ready to Implement:
- [ ] Socket.io real-time updates
- [ ] Email notifications (Nodemailer configured)
- [ ] Background jobs with Bull
- [ ] SLA automation
- [ ] File upload handling
- [ ] Full-text search (Elasticsearch/Meilisearch)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Unit & integration tests

## 📄 License

Same as parent Helpdesk project

## 🙋 Support

For issues or questions, please refer to the main Helpdesk documentation or create an issue in the repository.

---

**Built with ❤️ using Node.js, TypeScript, Express, and Prisma**
