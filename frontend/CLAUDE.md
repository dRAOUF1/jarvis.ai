# frontend/ — Claude Code local rules

Next.js 14 App Router + TS + Tailwind + shadcn/ui. Import types ONLY from `lib/types.gen.ts`
(generated; never edit). Read data from `lib/mockApi.ts`; swapping to `lib/api.ts` is one line.
Dark theme, indigo #6D5EF7, Inter, 16px radius. SSE hooks parse `data: {json}` lines into contract
unions. Keep components small. See root `ARCHITECTURE.md` + `TEAM_PLAN.md §2`.
