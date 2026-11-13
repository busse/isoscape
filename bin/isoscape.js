#!/usr/bin/env node
// Node 22.18+ strips TypeScript types natively; there is no build step.
import { main } from '../src/cli.ts'

main(process.argv.slice(2)).catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
})
