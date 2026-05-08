# Frontend Architecture

The frontend is organized by responsibility, not by accident of growth.

## Layers

- `api.ts`: compatibility facade that composes domain API clients.
- `api/`: typed domain API clients plus the shared request helper and payload contracts.
- `types.ts`: DTOs shared by views and components.
- `constants.ts`: domain constants, default form values, view identifiers, and route mapping.
- `utils/`: pure formatting and normalization helpers.
- `styles/`: split stylesheet layers for base rules, layout, forms, components, pages, and responsive behavior.
- `styles.css`: stylesheet entrypoint that imports the split layers in order.
- `components/ui.tsx`: reusable low-level UI primitives with no product workflow ownership.
- `components/layout.tsx`: app shell and authentication layout.
- `components/opportunities.tsx`: compatibility barrel for opportunity-specific reusable UI.
- `components/opportunity/`: opportunity card, drawer, scoring, and requirement summary components.
- `views/`: route-level page compositions. These receive data and callbacks from `App.tsx`.
- `hooks/`: reusable state derivation and orchestration hooks, including route, session, profile, workspace, assistant, notification, and admin controllers.
- `routes/`: route composition that maps domain controllers to page views.
- `App.tsx`: application shell coordinator for top-level wiring and cross-domain handoffs.

## Rules

- Keep API calls and cross-view orchestration in a dedicated hook when the behavior belongs to one domain.
- Keep reusable controls in `components/ui.tsx`.
- Keep domain-specific display components near their domain, such as `components/opportunities.tsx`.
- New large screens should be added as `views/*View.tsx`, not inline inside `App.tsx`.
- Pure helpers belong in `utils/`; they should not import React.
- Prefer typed controller objects at route boundaries instead of forwarding dozens of individual props.

## Completed Refactor Cuts

- `DashboardView` and `FeedView` are extracted.
- Profile editing and public profile imports are extracted into `ProfileView`.
- Board, reminders, notifications, application assistant, and admin screens are extracted into focused view modules.
- Opportunity cards, score explanations, requirement summaries, and the detail drawer are extracted into opportunity components.
- Auth and shell layout are extracted into layout components.
- The API layer is split into domain clients behind the existing `api` facade.
- Workspace-derived state is isolated in `useWorkspaceSelectors`.
- Sidebar navigation is route-based with stable URLs such as `/dashboard`, `/matches`, `/profile`, and `/admin`.
- Route navigation is isolated in `useAppRoute`.
- Auth/session state is isolated in `useSession`.
- Opportunity catalog, recommendations, statuses, reminders, filters, and drawer state are isolated in `useWorkspace`.
- Profile editing, profile details, ORCID import, and OpenAlex import are isolated in `useProfileForms`.
- Application assistant form and generation flow are isolated in `useApplicationAssistant`.
- Notification list, preferences, read state, and unsubscribe flow are isolated in `useNotifications`.
- Admin imports, background jobs, queue inspection, and operations loading are isolated in `useAdminOps`.
- `WorkspaceRoutes` now receives domain controllers rather than a flat prop tunnel.
- Opportunity UI is split into card, drawer, scoring, and requirement modules.
- Route/controller prop contracts are moved to `routes/types.ts`.
- Global styling is split into focused files under `styles/`.

## Next Refactor Targets

- Move controller/type definitions into feature folders as they grow.
- Move reusable form types out of route contracts as feature modules emerge.
- Add a real router dependency if nested routes, route loaders, or URL params become important.
- Add focused component tests after the view boundaries stabilize.
