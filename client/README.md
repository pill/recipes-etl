# Recipe Sandbox - React Client

A modern React + TypeScript + Vite client for exploring and searching recipes from the recipes-etl pipeline.

## Features

### 🎲 Random Recipe
Get a random recipe from the database to discover new dishes.

### 🔍 Full-Text Search
Search recipes by keywords in title, description, or instructions using Elasticsearch.

### 🏷️ By UUID
Look up a specific recipe using its unique identifier (UUID). Perfect for:
- Tracking recipes through the ETL pipeline
- Debugging UUID changes
- Direct recipe lookups
- Comparing different versions of the same recipe

### 🥘 By Ingredient
Filter recipes that contain specific ingredients.

### ⚡ Quick & Easy
Find recipes that can be prepared quickly.

### 🌍 Cuisine Analysis
Analyze recipes by cuisine type and view ingredient combinations.

## Setup

### Prerequisites
- Node.js 18+ installed
- Elasticsearch running on `localhost:9200`
- Recipe data loaded into Elasticsearch index

### Installation

```bash
cd client
npm install
```

### Development

```bash
npm run dev
```

The client will start on `http://localhost:5173` and proxy API requests to Elasticsearch.

### Build

```bash
npm run build
```

## Usage Examples

### Search by UUID
1. Click the "By UUID" tab
2. Enter a UUID (e.g., `8faa4a5f-4f52-56db-92aa-fa574ed6b62c`)
3. Press Enter or click "Search"
4. View the complete recipe details including all metadata

This is useful for:
- Finding recipes that changed UUIDs after reprocessing
- Tracking specific recipes through the pipeline
- Debugging duplicate detection

## React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
