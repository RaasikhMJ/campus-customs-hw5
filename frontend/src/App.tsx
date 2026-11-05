import { useEffect, useState } from "react"
import { approvePayment, fetchCash, fetchEvents, fetchTickets, runTicket } from "./api.ts"
import type { AgentEvent, Cash, Delegation, Ticket } from "./types.ts"

const SEATS = [
  { id: "boss", name: "Boss", chair: "Runs the desk", towel: "gold" },
  { id: "inventory", name: "Inventory", chair: "The rack", towel: "palm" },
  { id: "accounting", name: "Accounting", chair: "The till", towel: "sea" },
  { id: "facilities", name: "Facilities", chair: "The lease", towel: "sand" },
  { id: "customer_service", name: "Customer Service", chair: "The guests", towel: "hibiscus" },
] as const

const DOING: Record<string, string> = {
  check_size_on_hand: "counting a size on the rack",
  list_sizes_on_hand: "walking the rest of the sizes",
  read_vendor_invoice: "reading the vendor bill",
  read_lease: "reading the lease",
  read_ticket: "opening the ticket",
  read_shop_date: "checking the shop date",
  read_cash_accounts: "looking at checking",
  read_sku_price: "reading cost and list price",
  list_open_tickets: "reading the open board",
  ask_inventory: "asking Inventory",
  ask_accounting: "asking Accounting",
  ask_facilities: "asking Facilities",
  ask_customer_service: "asking Customer Service",
  ask_boss: "reporting to the Boss",
}

type Summary = {
  answer: string
  events: AgentEvent[]
  delegations: Delegation[]
}

function money(value: number) {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" })
}

function kindLabel(type: string) {
  if (type === "customer_order") return "Customer order"
  if (type === "rent_notice") return "Rent notice"
  if (type === "price_override") return "Price override"
  return type
}

function ticketLine(ticket: Ticket) {
  if (ticket.sku) {
    const size = ticket.size ? ` · size ${ticket.size}` : ""
    const qty = ticket.qty != null ? ` · qty ${ticket.qty}` : ""
    return `${ticket.sku}${size}${qty}`
  }
  if (ticket.lease_id != null) return `Lease ${ticket.lease_id}`
  return "No product on this ticket"
}

function tillLine(ticket: Ticket) {
  const move = ticket.cash_move
  if (move == null) return ""
  const dollars = money(move.amount)
  if (move.detail) return move.detail
  if (move.direction === "in") {
    const reprint = ticket.invoice_id != null ? " The reprint bill stays unpaid." : ""
    return `${dollars} comes into checking. ${move.label}.${reprint}`
  }
  return `${dollars} leaves checking. ${move.label}.`
}

function doing(tools: string[]) {
  const words = tools.map((tool) => DOING[tool] ?? tool.replaceAll("_", " "))
  if (words.length === 0) return ""
  return words.join(" · ")
}

function seatWords(agent: string, events: AgentEvent[], summary?: Summary) {
  const event = events.find((item) => item.agent === agent)
  const handoff = summary?.delegations.find((item) => item.to_role === agent)
  const said = event?.said || handoff?.reply || (agent === "boss" ? summary?.answer ?? "" : "")
  const tools = event?.tools ?? []
  return { said, tools }
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [selectedId, setSelectedId] = useState(() => {
    const asked = Number(new URLSearchParams(window.location.search).get("ticket"))
    return asked === 101 || asked === 102 || asked === 103 ? asked : 101
  })
  const [runningId, setRunningId] = useState<number | null>(null)
  const [live, setLive] = useState<AgentEvent[]>([])
  const [summaries, setSummaries] = useState<Record<number, Summary>>({})
  const [resolved, setResolved] = useState<Set<number>>(new Set())
  const [paidNote, setPaidNote] = useState<Record<number, string>>({})
  const [paying, setPaying] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    let gone = false
    Promise.all([fetchTickets(), fetchCash()])
      .then(([nextTickets, nextCash]) => {
        if (gone) return
        setTickets(nextTickets)
        setCash(nextCash)
      })
      .catch((reason: unknown) => {
        if (!gone) setError(reason instanceof Error ? reason.message : "The desk cannot reach the shop.")
      })
    return () => {
      gone = true
    }
  }, [])

  const selected = tickets.find((ticket) => ticket.id === selectedId) ?? null
  const summary = summaries[selectedId]
  const showing = runningId === selectedId ? live : summary?.events ?? []
  const selectedResolved = selected != null && (resolved.has(selected.id) || selected.resolved)

  async function startRun(ticketId: number) {
    setError("")
    setRunningId(ticketId)
    setSelectedId(ticketId)
    setLive([])
    let known = new Set<string>()
    try {
      known = new Set((await fetchEvents()).map((event) => event.run_id))
    } catch {
      known = new Set()
    }
    const timer = window.setInterval(() => {
      fetchEvents()
        .then((events) => {
          const fresh = events.filter((event) => event.run_id && !known.has(event.run_id))
          if (fresh.length > 0) setLive(fresh)
        })
        .catch(() => {
          // A missed poll should not stop the run. The next one can catch up.
        })
    }, 1200)
    try {
      const result = await runTicket(ticketId)
      const events = (await fetchEvents()).filter((event) => event.run_id === result.run_id)
      setLive(events)
      setSummaries((current) => ({
        ...current,
        [ticketId]: {
          answer: result.answer,
          events,
          delegations: result.delegations,
        },
      }))
      setResolved((current) => new Set(current).add(ticketId))
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The team did not finish.")
    } finally {
      window.clearInterval(timer)
      setRunningId(null)
    }
  }

  async function approve(ticketId: number) {
    setError("")
    setPaying(true)
    try {
      const payment = await approvePayment(ticketId)
      const [nextCash, nextTickets] = await Promise.all([fetchCash(), fetchTickets()])
      setCash(nextCash)
      setTickets(nextTickets)
      const verb = payment.direction === "in" ? "came into checking" : "left checking"
      const note = payment.detail
        ? `${payment.detail} The till is now ${money(payment.balance_after)}.`
        : `${money(payment.amount)} ${verb}. The till is now ${money(payment.balance_after)}.`
      setPaidNote((current) => ({
        ...current,
        [ticketId]: note,
      }))
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The payment was not approved.")
    } finally {
      setPaying(false)
    }
  }

  return (
    <div className="shore">
      <BeachGuide />
      <header className="mast">
        <div>
          <p className="eyebrow">Maracas Bay desk · after carnival</p>
          <h1>Campus Customs</h1>
          <p className="lede">
            The family is on the sand in the tees and hoodies. Doubles, bake and shark, and a
            little rum for the grown folks. The work is still here on the counter.
          </p>
        </div>
        <div className="till" aria-live="polite">
          <span>Checking</span>
          <strong>{cash ? money(cash.balance) : "—"}</strong>
          <small>{cash ? `Shop till ${cash.date}` : "Waiting for the shop"}</small>
        </div>
      </header>

      {error ? <p className="banner">{error}</p> : null}

      <main className="layout">
        <section className="board" aria-label="Open tickets">
          <h2>Three tickets</h2>
          <ul>
            {tickets.map((ticket) => {
              const done = resolved.has(ticket.id) || ticket.resolved
              return (
                <li key={ticket.id}>
                  <button
                    type="button"
                    className={ticket.id === selectedId ? "ticket on" : "ticket"}
                    aria-pressed={ticket.id === selectedId}
                    onClick={() => setSelectedId(ticket.id)}
                  >
                    <span className="ticket-id">{ticket.id}</span>
                    <span>
                      <strong>{ticket.subject}</strong>
                      <em>{ticket.requester}</em>
                      <small>
                        {kindLabel(ticket.type)} · {ticketLine(ticket)}
                      </small>
                    </span>
                    <span className={done ? "stamp done" : "stamp"}>{done ? "Resolved" : "Open"}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </section>

        <section className="desk" aria-label="Agent desk">
          {selected ? (
            <>
              <div className="desk-head">
                <div>
                  <p className="eyebrow">Ticket {selected.id}</p>
                  <h2>{selected.subject}</h2>
                  <p>{selected.notes}</p>
                </div>
                <div className="desk-actions">
                  <button
                    type="button"
                    className="run"
                    disabled={runningId != null}
                    onClick={() => startRun(selected.id)}
                  >
                    {runningId === selected.id ? "The team is out with it" : "Start the team"}
                  </button>
                  {selectedResolved && selected.cash_move ? (
                    <button
                      type="button"
                      className="run"
                      disabled={paying || selected.cash_move.already}
                      onClick={() => approve(selected.id)}
                    >
                      {paying
                        ? "Sending"
                        : selected.cash_move.already
                          ? "Already recorded"
                          : selected.cash_move.direction === "in"
                            ? "Approve the sale"
                            : "Approve payment"}
                    </button>
                  ) : null}
                </div>
              </div>

              {selectedResolved && selected.cash_move ? (
                <div className="approve" id="approval">
                  <div>
                    <h3>Your approval</h3>
                    <p>{tillLine(selected)}</p>
                    {paidNote[selected.id] ? <p className="paid">{paidNote[selected.id]}</p> : null}
                  </div>
                </div>
              ) : null}

              <div className="seats" aria-live="polite">
                {SEATS.map((seat) => {
                  const words = seatWords(seat.id, showing, runningId === selected.id ? undefined : summary)
                  const active = words.said.length > 0 || words.tools.length > 0
                  return (
                    <article key={seat.id} className={`seat towel-${seat.towel}${active ? " speaking" : ""}`}>
                      <header>
                        <h3>{seat.name}</h3>
                        <span>{seat.chair}</span>
                      </header>
                      {words.said ? <p>{words.said}</p> : <p className="quiet">{runningId === selected.id ? "Listening for this ticket." : "In a beach chair, waiting."}</p>}
                      {words.tools.length > 0 ? <p className="doing">Doing: {doing(words.tools)}</p> : null}
                    </article>
                  )
                })}
              </div>

              {selectedResolved && summary ? (
                <div className="summary">
                  <h3>What they did</h3>
                  <p>{summary.answer || "The Boss closed without a note."}</p>
                  <ul>
                    {SEATS.map((seat) => {
                      const words = seatWords(seat.id, summary.events, summary)
                      if (!words.said && words.tools.length === 0) return null
                      return (
                        <li key={seat.id}>
                          <strong>{seat.name}.</strong> {words.said || doing(words.tools)}
                          {words.tools.length > 0 && words.said ? <small> Tools: {words.tools.join(", ")}</small> : null}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ) : null}
            </>
          ) : (
            <p className="quiet">The three tickets have not arrived from the shop yet.</p>
          )}
        </section>
      </main>
    </div>
  )
}

const SHORES = [
  {
    name: "maracas",
    src: "/guide/maracas-bay.jpg",
    title: "Maracas Bay",
    place: "Trinidad",
    alt: "Families and palms along the water at Maracas Bay, Trinidad.",
    focus: "center 60%",
    credit: "Kalamazadkhan",
    license: "CC BY-SA 4.0",
    href: "https://commons.wikimedia.org/wiki/File:Maracas_Bay_-_Trinidad,_West_Indies.jpg",
  },
  {
    name: "pigeon",
    src: "/guide/pigeon-point.jpg",
    title: "Pigeon Point",
    place: "Tobago",
    alt: "The thatch jetty at Pigeon Point, Tobago.",
    focus: "center 40%",
    credit: "Kp93",
    license: "CC BY-SA 3.0",
    href: "https://commons.wikimedia.org/wiki/File:Pigeon_Point_beach.jpg",
  },
  {
    name: "englishman",
    src: "/guide/englishmans-bay.jpg",
    title: "Englishman’s Bay",
    place: "Tobago",
    alt: "A quiet cove at Englishman’s Bay, Tobago.",
    focus: "center",
    credit: "Kalamazadkhan",
    license: "CC BY-SA 4.0",
    href: "https://commons.wikimedia.org/wiki/File:Englishman%27s_Bay_-_Tobago,_West_Indies.jpg",
  },
  {
    name: "maracas-stand",
    src: "/guide/bake-and-shark.jpg",
    title: "Bake and shark",
    place: "Maracas",
    alt: "Richard’s bake and shark stand at Maracas, with the hills behind.",
    focus: "center 28%",
    credit: "Grueslayer",
    license: "CC BY-SA 3.0",
    href: "https://commons.wikimedia.org/wiki/File:MISC_Bake_%26_Shark_Hut_Maracas.jpg",
  },
] as const

function BeachGuide() {
  return (
    <section className="collage" aria-label="Trinidad and Tobago shores">
      {SHORES.map((shore) => (
        <figure key={shore.name} className={`tile ${shore.name}`}>
          <img src={shore.src} alt={shore.alt} style={{ objectPosition: shore.focus }} />
          <figcaption>
            <strong>{shore.title}</strong>
            <span>
              {shore.place} · {shore.credit}, <a href={shore.href}>{shore.license}</a>
            </span>
          </figcaption>
        </figure>
      ))}
    </section>
  )
}
