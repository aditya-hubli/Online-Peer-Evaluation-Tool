# Online Peer Evaluation Tool

A modern web-based platform for managing peer evaluations in educational and team-based project environments. Built with React, FastAPI, and PostgreSQL.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![React 18.3](https://img.shields.io/badge/react-18.3.1-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Security](#security)
- [Performance](#performance)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Online Peer Evaluation Tool is a comprehensive solution for conducting and managing peer assessments in academic and professional settings. The platform streamlines the evaluation process from form creation to report generation, providing real-time analytics and automated workflows.

### Key Benefits

- Automated evaluation workflows reduce administrative overhead
- Anonymous feedback mechanism promotes honest peer assessment
- Real-time dashboards for tracking evaluation progress
- Advanced analytics with weighted scoring and detailed reports
- Bulk operations for efficient user and data management
- Email notifications for deadline reminders
- Version control for evaluation forms

## Features

### Core Functionality

**User Management**
- Role-based access control (Student/Instructor)
- Bulk user import via CSV
- User authentication and authorization

**Project Management**
- Create and manage evaluation projects
- Define project timelines and objectives
- Track project progress and statistics

**Team Organization**
- Create teams with multiple members
- Assign teams to projects
- Real-time team chat functionality

**Evaluation Forms**
- Customizable evaluation criteria
- Weighted scoring system
- Form versioning and rollback capabilities
- Template duplication across projects

**Peer Evaluations**
- Anonymous evaluation submission
- Criterion-based scoring
- Comment and feedback collection
- Performance tracking

**Analytics & Reporting**
- Project-level analytics
- Team performance metrics
- Individual user reports
- Form usage statistics
- Export to PDF and CSV formats

### Advanced Capabilities

**Anonymization**
Student identities are protected during the evaluation process. Only instructors have access to evaluator information.

**Pending Evaluations Dashboard**
Students can view their outstanding evaluations with deadline information. Instructors have visibility into overall completion rates.

**Weighted Scoring**
Evaluation criteria can be assigned percentage weights for sophisticated rubric creation with automatic score calculation.

**Multi-Format Export**
Generate professional reports in PDF or CSV format with comprehensive statistics and breakdowns.

**Form Templates**
Duplicate and reuse successful evaluation forms across different projects to maintain consistency.

**Performance Monitoring**
Built-in performance tracking ensures evaluation submissions complete in under 2 seconds.

**Email Reminders**
Automated deadline notifications via SendGrid with configurable time windows.

**Version History**
Complete audit trail of form changes with ability to restore previous versions.

## Tech Stack

### Frontend

- **React 18.3** - Component-based UI library with hooks and concurrent features
- **Vite 5.4** - Fast build tool and development server
- **TailwindCSS 4.0** - Utility-first CSS framework
- **React Router 6** - Client-side routing
- **Framer Motion** - Animation library for page transitions
- **React Hot Toast** - Toast notification system
- **Axios** - HTTP client for API requests
- **shadcn/ui** - Accessible component library

### Backend

- **FastAPI 0.115** - High-performance Python web framework
- **Python 3.13** - Latest Python with performance improvements
- **Pydantic V2** - Data validation and serialization
- **Supabase** - Managed PostgreSQL database
- **python-jose** - JWT token authentication
- **passlib + bcrypt** - Password hashing
- **SendGrid** - Email delivery service
- **ReportLab** - PDF generation
- **WebSockets** - Real-time communication

### Database & Infrastructure

- **PostgreSQL 16** - Relational database
- **Supabase Cloud** - Database hosting with auto-scaling
- **Row-Level Security** - Database-enforced authorization
- **UUID Primary Keys** - Unique identifiers
- **Triggers & Indexes** - Query optimization
- **Migration System** - Version-controlled schema

### DevOps

- **Vercel** - Frontend deployment
- **Railway/Render** - Backend hosting
- **GitHub** - Version control
- **Environment Management** - Separate configurations for dev/staging/production

## System Architecture

### Component Diagram

```
Client Layer (Browser/Mobile)
          |
          v
    API Gateway (Vite Proxy)
          |
          v
    FastAPI Application
      |           |
      v           v
Authentication  Business Logic
      |           |
      v           v
    Data Access Layer
          |
          v
    PostgreSQL Database
    (Supabase)
```

### Request Flow

1. Client sends HTTP request
2. API Gateway validates and forwards request
3. FastAPI authenticates user via JWT
4. Business logic processes request
5. Data layer executes database queries
6. Response serialized and returned to client

### Security Architecture

- **Frontend**: HTTPS, XSS protection, CSP headers
- **API**: JWT authentication, input validation, rate limiting
- **Database**: Row-level security, prepared statements, encryption
- **Network**: CORS policies, firewall rules

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.13+
- Git
- PostgreSQL database (via Supabase)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/aditya-hubli/Online-Peer-Evaluation-Tool.git
cd Online-Peer-Evaluation-Tool
```

#### 2. Database Setup

Create a Supabase project at [https://supabase.com](https://supabase.com) and note your credentials:
- Project URL
- Anon Key
- Service Role Key

Run the SQL migrations in order:
1. `services/backend/migrations/001_initial_schema.sql`
2. `services/backend/migrations/002_fix_rls_policies.sql`

#### 3. Backend Setup

```bash
cd services/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials
```

Environment variables required in `.env`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

SENDGRID_API_KEY=your_sendgrid_key  # Optional
SENDGRID_FROM_EMAIL=your_email  # Optional

ENV=development
DEBUG=True
```

Start the backend server:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

#### 4. Frontend Setup

```bash
cd services/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

Environment variables required in `.env`:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### First Steps

1. Register an instructor account at `http://localhost:3000/register`
2. Create a project
3. Create teams and add members
4. Create evaluation forms
5. Students can submit evaluations
6. View analytics and generate reports

## Deployment

### Vercel (Frontend)

1. Connect your GitHub repository to Vercel
2. Configure environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL`
3. Deploy automatically on push to main branch

Manual deployment:
```bash
cd services/frontend
npm run build
vercel --prod
```

### Railway/Render (Backend)

**Railway:**
1. Create new project from GitHub repository
2. Add environment variables
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Deploy

**Render:**
1. Create new Web Service
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

### Docker (Optional)

Backend Dockerfile:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Frontend Dockerfile:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
```

## API Documentation

### Interactive Documentation

Visit these URLs when the backend is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login  
- `POST /api/v1/auth/logout` - User logout

#### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users/bulk-upload` - CSV bulk import

#### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

#### Teams
- `GET /api/v1/teams` - List teams
- `POST /api/v1/teams` - Create team
- `PUT /api/v1/teams/{id}` - Update team
- `DELETE /api/v1/teams/{id}` - Delete team

#### Evaluation Forms
- `GET /api/v1/forms` - List forms
- `POST /api/v1/forms` - Create form
- `PUT /api/v1/forms/{id}` - Update form
- `DELETE /api/v1/forms/{id}` - Delete form
- `POST /api/v1/forms/{id}/duplicate` - Duplicate form
- `GET /api/v1/forms/{id}/versions` - Version history
- `POST /api/v1/forms/{id}/rollback/{version_id}` - Restore version

#### Evaluations
- `GET /api/v1/evaluations` - List evaluations
- `POST /api/v1/evaluations` - Submit evaluation
- `GET /api/v1/evaluations/student/{id}` - Student pending evaluations

#### Reports
- `GET /api/v1/reports/project/{id}` - Project report
- `GET /api/v1/reports/team/{id}` - Team report
- `GET /api/v1/reports/user/{id}` - User report
- `GET /api/v1/reports/form/{id}` - Form report
- `GET /api/v1/reports/export/project/{id}?format=csv` - Export project
- `GET /api/v1/reports/export/team/{id}?format=pdf` - Export team

#### Chat
- `WS /api/v1/chat/ws/{team_id}` - WebSocket connection
- `GET /api/v1/chat/history/{team_id}` - Chat history

#### Reminders
- `GET /api/v1/reminders/upcoming` - Upcoming deadlines
- `POST /api/v1/reminders/trigger` - Send reminders
- `POST /api/v1/reminders/test-email` - Test email

---

## Project Structure

```
services/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── config.py
│   ├── database.py
│   ├── migrations/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── utils/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    ├── public/
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── components/
        ├── contexts/
        ├── hooks/
        ├── pages/
        ├── services/
        ├── types/
        └── utils/
```

## Testing

### Backend Tests

```bash
cd services/backend
pytest
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd services/frontend
npm test
npm test -- --coverage
```

## Security

- JWT authentication with token expiration
- bcrypt password hashing (cost factor: 12)
- Role-based access control for students/instructors
- Row-level security policies in Supabase
- HTTPS enforcement in production
- Parameterized queries for SQL injection prevention
- XSS protection via React sanitization
- CSRF protection with SameSite cookies
- Rate limiting on API endpoints

## Performance

- Page load time < 1.5s
- API response time < 500ms (p95)
- Database queries optimized with indexing
- Code splitting for lazy route loading
- Static assets served via CDN
- Gzip/Brotli compression enabled

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/name`)
5. Open a Pull Request

### Guidelines

- Python: Follow PEP 8
- JavaScript: Use Prettier formatting
- Commits: Use conventional commits format

## License

This project is licensed under the MIT License.

## Author

**Aditya Hubli**
- GitHub: [@aditya-hubli](https://github.com/aditya-hubli)
