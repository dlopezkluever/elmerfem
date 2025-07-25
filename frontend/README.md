# ElmerFEM Educational Platform - Frontend

## Overview

This is the React-based frontend for the ElmerFEM Educational Platform, designed to provide high school students with an intuitive interface for learning Finite Element Analysis (FEA).

## Features

### Core Pages
- **Home Page**: Template selection with large, student-friendly buttons for Heat Transfer and Structural Mechanics simulations
- **Parameter Form**: Dynamic form with real-time validation for simulation parameters
- **Progress Page**: Real-time simulation monitoring with WebSocket updates and polling fallback
- **Result Page**: View simulation results, download files, and access visualization
- **Material Library**: Browse available materials with their properties
- **Help Page**: Educational content about FEA with FAQs and quickstart guides
- **Settings**: Local preferences management

### Technical Features
- **Neumorphic Design**: Clean, modern UI with soft shadows and depth
- **Form Validation**: Zod-based validation with clear error messages
- **Local Storage**: Recent simulations history and user preferences
- **API Integration**: Axios client with error handling and interceptors
- **Responsive Design**: Works on tablets and desktops

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** with daisyUI for styling
- **React Router v6** for navigation
- **React Hook Form** with Zod for form handling
- **Axios** for API communication
- **React Use WebSocket** for real-time updates

## Development Setup

### Prerequisites
- Node.js 18+
- npm or pnpm

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env.local` file:

```env
VITE_BACKEND_URL=http://localhost:8000
```

### Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Production Build

```bash
npm run build
```

Build artifacts will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and services
│   ├── components/    # Reusable components
│   ├── hooks/         # Custom React hooks
│   ├── pages/         # Page components
│   ├── types/         # TypeScript types
│   ├── utils/         # Utility functions
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── public/            # Static assets
└── package.json       # Dependencies
```

## Key Components

### API Integration
- `api/client.ts`: Configured Axios instance
- `api/simulations.ts`: Simulation endpoints

### Custom Hooks
- `useRecentSimulations`: Manages simulation history
- `useMaterials`: Fetches and caches materials
- `useSettings`: Local preferences management

### Form Validation
- Zod schemas for type-safe validation
- Dynamic form generation based on simulation type
- Real-time validation feedback

## Deployment

For local-only deployment (as per requirements):
1. Build the frontend: `npm run build`
2. Serve the dist folder with any static file server
3. Ensure the backend is running on `http://localhost:8000`

## Testing

Testing suite setup is in progress (Task 5.7). Will include:
- Jest + React Testing Library for unit tests
- MSW for API mocking
- Cypress for end-to-end tests

## Contributing

Please refer to the project's coding standards and submit PRs with:
- Clear commit messages
- Updated documentation
- Test coverage for new features 