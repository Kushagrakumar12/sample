# AI-Powered Precise Train Traffic Control System

A comprehensive AI-powered decision-support system for railway section controllers to optimize train movements in real time, maximize throughput, reduce delays, and ensure safe operation while handling dynamic disruptions.

## 🚆 System Overview

This system provides real-time optimization, conflict detection, and automated decision support for railway operations. It combines advanced algorithms with an intuitive interface to help railway controllers manage complex train networks efficiently.

### Key Features

- **Real-time Train Scheduling Optimization** using MILP algorithms
- **Dynamic Conflict Detection and Resolution** with constraint satisfaction
- **Route Optimization** using graph algorithms and NetworkX
- **Safety Compliance Checking** with automated alerts
- **Performance Analytics** and comprehensive reporting
- **WebSocket-based Real-time Updates** for live monitoring
- **Simulation Interface** for "what-if" scenario planning

## 🏗️ Architecture

### Backend Components
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Database ORM with PostgreSQL
- **PuLP/OR-Tools** - Mathematical optimization libraries
- **NetworkX** - Graph algorithms for route optimization
- **WebSockets** - Real-time communication
- **Redis** - Caching and session management

### Frontend Components
- **React** - Modern UI framework
- **Material-UI** - Professional component library
- **D3.js** - Advanced data visualization
- **Recharts** - Statistical charts and graphs
- **Socket.IO** - Real-time client communication

### Database
- **PostgreSQL** - Primary relational database
- **Comprehensive schema** with tracks, trains, schedules, and events
- **Performance indexes** for optimized queries
- **Audit logging** for compliance and debugging

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+ (optional, SQLite used by default)
- Redis 6+ (optional, for production)

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database**:
   ```bash
   cd backend
   python -c "from models.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

3. **Start the backend server**:
   ```bash
   cd backend/app
   python main.py
   ```

   The API will be available at: `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm start
   ```

   The application will be available at: `http://localhost:3000`

## 📊 Core Algorithms

### 1. MILP Train Scheduler (`backend/optimization/milp_scheduler.py`)
- **Mixed Integer Linear Programming** for optimal train scheduling
- **Priority-based optimization** with weighted objectives
- **Capacity constraints** and safety requirements
- **Real-time re-optimization** for dynamic changes

### 2. Conflict Resolver (`backend/optimization/conflict_resolver.py`)
- **Constraint Satisfaction Problem** solving
- **Real-time conflict detection** with predictive analysis
- **Automated resolution suggestions** based on priorities
- **Safety buffer calculations** and validation

### 3. Route Optimizer (`backend/optimization/route_optimizer.py`)
- **NetworkX graph algorithms** for shortest path
- **Multi-objective optimization** (time, distance, cost)
- **Dynamic constraint handling** (weather, maintenance)
- **Network bottleneck identification**

## 🎯 API Endpoints

### Train Management
- `GET /api/trains` - List all trains
- `POST /api/trains` - Create new train
- `GET /api/trains/{id}` - Get specific train
- `PUT /api/trains/{id}` - Update train information
- `GET /api/trains/{id}/status` - Get real-time train status

### Schedule Optimization
- `POST /api/optimization/schedule` - Run MILP optimization
- `POST /api/optimization/conflicts/detect` - Detect conflicts
- `POST /api/optimization/conflicts/resolve` - Resolve conflicts
- `GET /api/optimization/recommendations` - Get AI recommendations

### Real-time Updates
- `WebSocket /ws/{client_id}` - Real-time data stream
- Event types: `train_update`, `conflict_alert`, `optimization_result`

## 🔧 Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/train_control
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key

# Frontend
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=localhost:8000
```

### Database Configuration
For production, update `backend/models/database.py`:
```python
DATABASE_URL = "postgresql://user:password@localhost/train_control"
```

## 📈 Performance Metrics

The system tracks several key performance indicators:

- **On-Time Performance (OTP)** - Percentage of trains arriving within 5 minutes
- **Average Delay** - Mean delay across all completed journeys
- **Conflict Resolution Rate** - Percentage of conflicts automatically resolved
- **System Throughput** - Trains processed per hour
- **Resource Utilization** - Track and platform capacity usage

## 🧪 Testing and Simulation

### Simulation Interface
Access the simulation interface at `/simulation` to:
- **Model disruptions** (weather, breakdowns, delays)
- **Test optimization algorithms** with different scenarios
- **Compare performance** across different strategies
- **Generate reports** for analysis

### Sample Scenarios
1. **Peak Hour Operations** - High traffic with capacity constraints
2. **Weather Disruption** - Reduced speeds and visibility
3. **Equipment Failure** - Single track out of service
4. **Maintenance Windows** - Planned service interruptions

## 🔒 Security Features

- **JWT-based authentication** for API access
- **Role-based access control** (Administrator, Controller, Viewer)
- **Input validation** and SQL injection prevention
- **Audit logging** for all system changes
- **WebSocket connection security** with client validation

## 📚 Documentation

- **API Documentation** - Available at `/docs` when running
- **User Guide** - Detailed operation instructions
- **Algorithm Documentation** - Mathematical models and implementations
- **Database Schema** - Complete table definitions and relationships

## 🛠️ Development

### Project Structure
```
├── backend/
│   ├── app/           # FastAPI application
│   ├── api/           # REST API endpoints
│   ├── models/        # Database models
│   ├── optimization/  # AI algorithms
│   └── utils/         # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom React hooks
│   │   └── services/    # API client services
└── database/
    ├── schemas/       # SQL schema definitions
    └── migrations/    # Database migrations
```

### Adding New Features

1. **Backend**: Add new endpoints in `backend/api/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Database**: Update models in `backend/models/database.py`
4. **Algorithms**: Implement in `backend/optimization/`

## 🚀 Deployment

### Docker Deployment (Recommended)
```bash
# Build and run all services
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Manual Deployment
1. **Set up PostgreSQL** and Redis
2. **Configure environment variables**
3. **Build frontend**: `npm run build`
4. **Deploy backend** with Gunicorn/uWSGI
5. **Set up reverse proxy** (Nginx recommended)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run linting: `black backend/` and `npm run lint`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - Comprehensive guides at `/docs`
- **API Reference** - Interactive docs at `/docs` endpoint

## 🎉 Acknowledgments

- **OR-Tools** - Google's optimization library
- **NetworkX** - Python graph analysis library
- **Material-UI** - React component framework
- **D3.js** - Data visualization library