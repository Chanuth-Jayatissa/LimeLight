# LimeLight

LimeLight is a startup discovery and investing platform prototype. It gives users a discovery feed of startups, founder/profile pages, and a studio workflow for creating startup pitch cards from a URL, voice input, generated pitch content, and token-style launch metadata.

## Features

- Public landing page for a startup investing platform.
- Protected app routes for discovery, studio, and profile pages.
- Startup discovery feed with mock startup market, traction, and radar data.
- Studio dashboard for managing generated startup cards.
- Create flow that can scrape a URL, process a voice recording, and generate pitch/audio metadata through API endpoints.
- Local persistence for user-created startup cards.
- AWS Amplify/Cognito integration points for authenticated API calls.

## Tech Stack

- React and TypeScript
- Vite
- Tailwind CSS
- AWS Amplify Auth
- Lucide React and Motion
- Express-related server dependencies for API integration work

## Project Structure

- src/App.tsx - route shell, auth guard, and app navigation
- src/pages/Landing.tsx - public landing page
- src/pages/Discover.tsx - startup discovery masonry feed
- src/pages/Studio.tsx - startup creation and management workflow
- src/pages/Profile.tsx - founder/startup profile view
- src/contexts/AuthContext.tsx - auth state handling
- src/components/StartupCard.tsx - reusable startup card UI

## Getting Started

Install dependencies and start the frontend:

~~~bash
npm install
npm run dev
~~~

Optional Cognito configuration can be provided through Vite environment variables:

~~~bash
VITE_USER_POOL_ID=your_cognito_user_pool_id
VITE_APP_CLIENT_ID=your_cognito_app_client_id
~~~

## Useful Commands

~~~bash
npm run dev
npm run build
npm run preview
npm run lint
~~~

## Status

Portfolio prototype. The UI and product flow are present, with mocked startup data and integration points for auth, URL analysis, voice generation, and token launch workflows.
