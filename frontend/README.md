# Voice-of-Customer Platform Frontend

This is the frontend application for the Voice-of-Customer & Brand-Intel Platform. It provides a responsive, modern interface for interacting with all platform features.

## Features

- **Dashboard:** Real-time visualization of key metrics and insights
- **Data Sources:** Manage and monitor data collection sources
- **Insights:** View AI-generated insights from customer feedback
- **Entity Graph:** Explore relationships between entities in a visual graph
- **Documents:** Search and browse raw collected documents
- **Settings:** Configure tenant-specific settings

## Technologies Used

- **React:** Frontend UI library
- **TypeScript:** Type-safe JavaScript
- **Material UI:** Component library for consistent design
- **Nivo:** Data visualization library for charts
- **React Query:** Data fetching and caching
- **Axios:** API client
- **React Router:** Client-side routing

## Architecture

The frontend application follows a modern React architecture with:

- **Context API** for state management (auth, preferences)
- **React Query** for server state management
- **TypeScript** for type safety
- **Material UI** for design system
- **Component-based design** with clear separation of concerns

## Environment Setup

Copy the `.env.example` file to `.env` and set these values:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:3000/api

# Authentication 
REACT_APP_AUTH_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH_CLIENT_ID=your-client-id

# Feature Flags
REACT_APP_ENABLE_GRAPH_VISUALIZATION=true
REACT_APP_ENABLE_REALTIME_UPDATES=true
```

## Available Scripts

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Docker Deployment

The frontend can be built and deployed using Docker:

```bash
# Build the Docker image
docker build -t voc-platform-frontend .

# Run the container
docker run -p 80:80 voc-platform-frontend
```

## Integration with Platform

The frontend integrates with the platform via:

1. **MCP Server API:** Primary data access through REST endpoints
2. **Observability Tools:** Links to Grafana, Langfuse, and Jaeger
3. **Authentication:** JWT-based authentication system

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
![Entity Graph](docs/screenshots/entity-graph.png)
![Insights](docs/screenshots/insights.png)
