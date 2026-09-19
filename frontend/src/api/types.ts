export type RegionCode = 'QLD1' | 'NSW1' | 'VIC1' | 'SA1' | 'TAS1'

export interface RegionInfo {
  code: RegionCode
  name: string
}

export interface DispatchObservation {
  region: RegionCode
  interval_datetime: string
  price: string
  demand: string
  generation: string | null
  interchange: string | null
}

export interface AlertItem {
  id: string
  rule_key: string
  rule_type: string
  region: RegionCode
  interval_datetime: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  observed_value: string
  threshold: string
  created_at: string
  acknowledged_at: string | null
  acknowledgement_note: string | null
}

export interface Page<T> {
  items: T[]
  limit: number
  offset: number
  has_more: boolean
}

export interface ProblemDetail {
  code: string
  message: string
  fields?: Record<string, string>
}

export interface ReplayJob {
  id: string
  source: string
  regions: RegionCode[]
  speed: number
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'failed'
  total: number
  processed: number
  published: number
  rejected: number
  current_interval: string | null
  started_at: string | null
  completed_at: string | null
  cancel_requested: boolean
  failure_message: string | null
}
