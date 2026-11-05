import type { AgentEvent, Cash, PaymentResult, RunResult, Ticket } from "./types.ts"

export const API = "http://localhost:8000"

async function fail(response: Response): Promise<never> {
  const text = await response.text()
  let message = text || response.statusText
  try {
    const body = JSON.parse(text) as { detail?: unknown }
    if (typeof body.detail === "string") message = body.detail
  } catch {
    // The body was not JSON. The raw text is already the message.
  }
  throw new Error(message)
}

export async function fetchTickets(): Promise<Ticket[]> {
  const response = await fetch(`${API}/tickets`)
  if (!response.ok) return fail(response)
  const body = (await response.json()) as { tickets: Ticket[] }
  return body.tickets
}

export async function fetchCash(): Promise<Cash> {
  const response = await fetch(`${API}/cash`)
  if (!response.ok) return fail(response)
  return (await response.json()) as Cash
}

export async function fetchEvents(): Promise<AgentEvent[]> {
  const response = await fetch(`${API}/events?limit=80`)
  if (!response.ok) return fail(response)
  const body = (await response.json()) as { events: AgentEvent[] }
  return body.events
}

export async function runTicket(ticketId: number): Promise<RunResult> {
  const response = await fetch(`${API}/tickets/${ticketId}/run`, { method: "POST" })
  if (!response.ok) return fail(response)
  return (await response.json()) as RunResult
}

export async function approvePayment(ticketId: number): Promise<PaymentResult> {
  const response = await fetch(`${API}/payments/${ticketId}/approve`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ approved_by: "owner" }),
  })
  if (!response.ok) return fail(response)
  return (await response.json()) as PaymentResult
}
