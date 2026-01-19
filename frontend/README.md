# Dana Dairy Frontend

## Overview

Dana Dairy Frontend is a modern dairy management web application built with Next.js, featuring a robust authentication system, intuitive user interface, and seamless user experience with dark/light theme support.

## Tech Stack

- Frontend Framework: Next.js (v16.0.6), React (v19.2.0)
- Programming Language: TypeScript
- UI Components: Radix UI + Shadcn UI
- Styling: Tailwind CSS (v4)
- Icons: Lucide React
- Forms: React Hook Form + Zod validation
- Authentication: NextAuth.js (v5)
- Theming: next-themes
- Notifications: Sonner

## Prerequisites

Before you begin, ensure you have the following installed:

- Node.js (v18.x.x or higher)
- pnpm (v8.x.x or higher)
- Git

## Code Style

- We use ESLint for code linting
- Follow the TypeScript strict mode guidelines
- Consistent component structure using Radix UI primitives
- React Compiler enabled via Babel plugin

## Getting Started

Follow these steps to set up and run the application on your local machine:

1. Clone the repository

   ```bash
   git clone <your-repository-url>
   ```

2. Install dependencies

   ```bash
   pnpm install
   ```

3. Set up environment variables

   ```bash
   cp .env.example .env.local
   ```

4. Run the application

   ```bash
   pnpm dev
   ```

   The application will be available at `http://localhost:3000`

## Available Scripts

- `pnpm dev` - Starts the development server
- `pnpm build` - Creates a production build
- `pnpm start` - Runs the production server
- `pnpm lint` - Runs ESLint for code checking
- `pnpm lint:fix` - Runs ESLint and automatically fixes issues

## Key Features

- Modern UI components using Radix UI + Shadcn UI
- Type-safe development with TypeScript
- Efficient styling with Tailwind CSS v4
- Server-side rendering with Next.js 16
- Secure authentication with NextAuth.js v5
- Dark/Light theme support
- Toast notifications with Sonner
- Form validation with React Hook Form and Zod

## Contributing

Please read our contributing guidelines before submitting any changes.

## License

This project is private and proprietary. All rights reserved.
