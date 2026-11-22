import type { DataSource } from './contracts'
import { mockData } from './mock'

export function getDataSource(): DataSource {
  if (process.env.NEXT_PUBLIC_DATA_MODE === 'live') throw new Error('Live data is scheduled for Phase 6.')
  return mockData
}
