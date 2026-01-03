# Testing Documentation

## Overview

This project has a comprehensive test suite covering all backend functionality with **80% code coverage threshold** for:
- Lines
- Functions
- Branches
- Statements

## Test Structure

```
tests/
├── setup.ts                          # Global test configuration
├── factories/                        # Test data factories
│   ├── userFactory.ts               # User creation helpers
│   ├── ticketFactory.ts             # Ticket creation helpers
│   └── articleFactory.ts            # Article creation helpers
├── services/                         # Service layer tests
│   ├── authService.test.ts          # Authentication tests
│   ├── ticketService.test.ts        # Ticket management tests
│   ├── dashboardService.test.ts     # Dashboard metrics tests
│   ├── knowledgeBaseService.test.ts # KB tests
│   └── searchService.test.ts        # Search functionality tests
├── controllers/                      # API endpoint tests
│   ├── authController.test.ts       # Auth endpoints
│   └── ticketController.test.ts     # Ticket endpoints
├── middleware/                       # Middleware tests
│   └── auth.test.ts                 # Auth middleware tests
└── utils/                           # Utility function tests
    ├── jwt.test.ts                  # JWT generation/verification
    ├── errors.test.ts               # Custom error classes
    └── emailTemplates.test.ts       # Email template generation
```

## Prerequisites

### Required Services

1. **PostgreSQL 15+**
   - Test database: `helpdesk_test`
   - User: `test` / Password: `test`

2. **Redis 7+** (optional, for background job tests)
   - Default: `localhost:6379`

### Installation

```bash
npm install
```

## Quick Start

### Option 1: Using Docker (Recommended)

Start test services:
```bash
npm run test:setup
```

Run tests:
```bash
npm test
```

Run tests with coverage:
```bash
npm run test:coverage
```

Stop test services:
```bash
npm run test:teardown
```

Run everything (CI mode):
```bash
npm run test:ci
```

### Option 2: Manual Setup

1. **Start PostgreSQL:**
   ```bash
   # Using Docker
   docker run -d \
     --name helpdesk-test-db \
     -e POSTGRES_USER=test \
     -e POSTGRES_PASSWORD=test \
     -e POSTGRES_DB=helpdesk_test \
     -p 5432:5432 \
     postgres:15-alpine
   ```

2. **Run migrations:**
   ```bash
   dotenv -e .env.test -- npx prisma migrate deploy
   ```

3. **Run tests:**
   ```bash
   npm test
   ```

## Test Commands

| Command | Description |
|---------|-------------|
| `npm test` | Run all tests once |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run test:setup` | Start test database (Docker) |
| `npm run test:teardown` | Stop test database (Docker) |
| `npm run test:ci` | Full CI pipeline |

## Test Coverage

The test suite covers:

### Services (100% coverage target)
- ✅ Authentication (register, login, logout, refresh token)
- ✅ Ticket Management (CRUD, assignment, comments)
- ✅ Dashboard Metrics (agent/customer dashboards)
- ✅ Knowledge Base (articles, categories, search)
- ✅ Global Search (tickets, articles, customers)

### Controllers (API Endpoints)
- ✅ Auth endpoints (POST /auth/register, /login, /logout)
- ✅ Ticket endpoints (GET, POST, PATCH, DELETE /tickets)
- ✅ Comment endpoints (POST /tickets/:id/comments)
- ✅ Assignment endpoints (PATCH /tickets/:id/assign)

### Middleware
- ✅ Authentication middleware (JWT verification)
- ✅ Authorization middleware (role-based access)
- ✅ Error handling middleware

### Utilities
- ✅ JWT token generation and verification
- ✅ Custom error classes
- ✅ Email template generation

## Writing Tests

### Using Factories

```typescript
import { createUser, createAgent, createCustomer } from '../factories/userFactory';
import { createTicket } from '../factories/ticketFactory';

// Create test data
const { user, password } = await createUser();
const { user: agentUser } = await createAgent();
const ticket = await createTicket({ customerId: customer.id });
```

### Testing Services

```typescript
import { describe, it, expect } from 'vitest';
import { authService } from '../../src/services/authService';

describe('AuthService', () => {
  it('should register a new user', async () => {
    const result = await authService.register({
      email: 'test@example.com',
      password: 'password123',
      fullName: 'Test User',
      userType: 'CUSTOMER'
    });

    expect(result.user).toBeDefined();
    expect(result.accessToken).toBeDefined();
  });
});
```

### Testing Controllers

```typescript
import request from 'supertest';
import { app } from '../../src/server';

describe('AuthController', () => {
  it('POST /auth/register should create user', async () => {
    const response = await request(app)
      .post('/auth/register')
      .send({
        email: 'new@example.com',
        password: 'Password123!',
        fullName: 'New User',
        userType: 'CUSTOMER'
      });

    expect(response.status).toBe(201);
    expect(response.body.user.email).toBe('new@example.com');
  });
});
```

## Test Environment Variables

Tests use `.env.test` for configuration:

```env
NODE_ENV=test
DATABASE_URL="postgresql://test:test@localhost:5432/helpdesk_test"
JWT_SECRET="test-secret-key"
```

## Coverage Reports

After running `npm run test:coverage`, view reports:

- **Terminal**: Summary displayed in console
- **HTML**: Open `coverage/index.html` in browser
- **LCOV**: `coverage/lcov.info` for CI integration

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: helpdesk_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - run: npm ci

      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/helpdesk_test

      - run: npm run test:coverage

      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

## Troubleshooting

### Database Connection Errors

```bash
Error: Can't reach database server at `localhost:5432`
```

**Solution**: Ensure PostgreSQL is running:
```bash
docker ps | grep postgres
# or
pg_isready -h localhost -p 5432
```

### Migration Errors

```bash
Error: Database schema is not up to date
```

**Solution**: Run migrations:
```bash
dotenv -e .env.test -- npx prisma migrate deploy
```

### Port Already in Use

```bash
Error: Port 5432 is already in use
```

**Solution**: Stop existing PostgreSQL:
```bash
docker stop helpdesk-test-db
# or change port in .env.test
```

### Clean Test Data

The test suite automatically cleans up data after each test using `afterEach` hooks. If you need to manually reset:

```bash
dotenv -e .env.test -- npx prisma migrate reset
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Factories**: Use factories for test data creation
3. **Cleanup**: Tests auto-cleanup via `afterEach`
4. **Descriptive names**: Use clear test descriptions
5. **Arrange-Act-Assert**: Follow AAA pattern
6. **Edge cases**: Test both success and failure paths
7. **Permissions**: Test role-based access control

## Performance

- Average test runtime: ~5-10 seconds
- Database cleanup per test: ~50ms
- Total tests: 180+
- Coverage: 80%+

## Future Enhancements

- [ ] Integration tests for Socket.io real-time features
- [ ] Load tests for API endpoints
- [ ] E2E tests with Playwright
- [ ] Snapshot tests for email templates
- [ ] Performance regression tests
