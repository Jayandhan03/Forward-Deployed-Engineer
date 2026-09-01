# 04 · Frontend

Enough to build a polished, production SaaS UI on your own — not enough to call yourself a frontend
specialist, and that's fine. The bar: a paying user can't tell an engineer built it.

**Depth target:** L4 (working competence). **Budget:** 4–5 weeks.

---

## Tech stack (decided — JS/TS base)

| Concern | Choice | Why |
|---|---|---|
| Language | **TypeScript** (strict mode) | Types catch the class of bug you'll otherwise ship. |
| Runtime / package manager | Node 20+ / **pnpm** | Fast, disk‑efficient, strict by default. |
| Framework | **Next.js (App Router)** + React 19 | SSR/streaming, file routing, one deploy target, huge ecosystem. |
| Styling | **Tailwind CSS** + **shadcn/ui** (Radix primitives) | Fast, consistent, accessible components you own the code of. |
| Client state | **Zustand** | Minimal; reach for Redux Toolkit only if the app genuinely needs it. |
| Server state / caching | **TanStack Query** | Caching, refetch, mutations, optimistic updates done right. |
| Forms | **React Hook Form** + **Zod** | Share Zod schemas with validation; generate types. |
| API client | **openapi-typescript** / **orval** from FastAPI's OpenAPI | Typed client, regenerated on backend change — no drift. |
| Auth | **Auth.js (NextAuth)** or FastAPI JWT in httpOnly cookies | Keep tokens out of JS. |
| LLM streaming UI | SSE / `ReadableStream`; **Vercel AI SDK** optional | Token‑by‑token rendering, cancel, tool‑call UI. |
| Testing | **Vitest** + React Testing Library; **Playwright** for e2e | Unit + real browser flows. |
| Lint / format | ESLint + Prettier + `tsc --noEmit` in CI | Non‑negotiable on a team. |
| Deploy | **Vercel** (or Docker + Nginx next to the backend) | Zero‑config previews per PR. |
| Monorepo (optional) | **Turborepo** | Only if frontend + backend + shared packages live together. |

---

## 00-web-basics

- [ ] HTML & semantics · [ ] CSS fundamentals (box model, cascade, specificity)
- [ ] Layout — flexbox & grid · [ ] Tailwind · [ ] Responsive design · [ ] Accessibility (a11y)

## 01-javascript

- [ ] Language core — closures, `this`, prototypes, modules, event loop
- [ ] DOM & events · [ ] Fetch & promises · [ ] Modules & bundlers (Vite) · [ ] Async/await

## 02-typescript

- [ ] Types & interfaces · [ ] Generics · [ ] Narrowing & type guards
- [ ] Utility types (`Partial`, `Pick`, `Omit`, `Record`…) · [ ] tsconfig & strict flags
- [ ] Typing API responses — from generated OpenAPI types

## 03-react

- [ ] Components & props · [ ] State & effects (and when `useEffect` is wrong)
- [ ] Hooks — built‑in & custom · [ ] Context & providers
- [ ] Data fetching — TanStack Query · [ ] Forms & validation — RHF + Zod
- [ ] Performance & memoization — `memo`, `useMemo`, `useCallback`, profiler

## 04-nextjs

- [ ] App Router — layouts, nested routes, loading/error boundaries
- [ ] Server vs client components — the boundary, and what breaks it
- [ ] Server actions · [ ] Route handlers (API) · [ ] Auth (Auth.js / sessions)
- [ ] Caching & revalidation — the mental model · [ ] Deploy to Vercel

## 05-app-patterns

- [ ] State management — Zustand (client) vs Query (server); don't mix responsibilities
- [ ] API client layer — one typed module, error normalization, auth refresh
- [ ] **Streaming UI** — render LLM tokens as they arrive; stop/cancel
- [ ] Optimistic UI — update now, reconcile on response, roll back on error
- [ ] Loading & error states — skeletons, retries, empty states
- [ ] Design system & components — tokens, spacing scale, shadcn/ui composition

---

## Mini‑projects

- **Auth'd dashboard shell** — login, protected routes, nav, dark mode, responsive.
- **Streaming chat UI** — connects to `projects/07`; token streaming, markdown, code blocks, stop button.
- **CRUD table** — TanStack Query, optimistic create/delete, form validation, pagination.

## Done when

You can build a responsive, accessible, auth'd multi‑page app against your own FastAPI backend with a
typed API client, streaming chat, optimistic updates, and a CI that lints + type‑checks + runs Playwright.

## Resources

- Next.js docs (App Router) · React docs (the new ones, react.dev) · TypeScript handbook
- TanStack Query docs · shadcn/ui docs · Tailwind docs · *Total TypeScript* (Matt Pocock) essentials
