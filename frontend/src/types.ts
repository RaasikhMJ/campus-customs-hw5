export type Ticket = {
  id: number
  type: string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  lease_id: number | null
  invoice_id: number | null
  status: string
  open: boolean
  resolved: boolean
  notes: string | null
  cash_move: {
    direction: "in" | "out"
    kind: string
    amount: number
    label: string
    detail?: string
    already: boolean
  } | null
}

export type Cash = {
  name: string
  balance: number
  date: string
}

export type AgentEvent = {
  time: string
  run_id: string
  agent: string
  said: string
  tools: string[]
}

export type Delegation = {
  from_role: string
  to_role: string
  task: string
  reply: string
}

export type RunResult = {
  ticket_id: number
  run_id: string
  answer: string
  delegations: Delegation[]
  llm_name: string
  cash_changed: boolean
}

export type PaymentResult = {
  approved: boolean
  ticket_id: number
  direction: "in" | "out"
  amount: number
  balance_before: number
  balance_after: number
  kind: string
  label: string
  detail?: string
  approved_by: string
}
