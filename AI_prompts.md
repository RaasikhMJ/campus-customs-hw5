# AI prompts — Homework 5: Campus Customs Multi-Agent Operations

**Course:** MGT 409 — AI Foundations for Managers, Yale School of Management  
**Coder:** Goldie  
**Folder:** `YALE EMBA AI FOUNDATIONS/hw5 Campus Customs`

Each problem below has its own section. A section is filled only with prompts you typed. A follow-up is included only when a later prompt was needed, with one sentence on what the first prompt did not capture.

**How we move:** one problem at a time. The next section stays empty until you describe that problem.

**Current problem:** 10 — Reflection  
**Next:** Waiting for your prompt.

---

## Standing rules (not a problem)

- This homework stays in `hw5 Campus Customs`, beside `hw4 Campus Customs`. It does not touch the earlier homework folders.
- The original shop database is `data/campus_customs.db`. It stays untouched so a run can be reset.
- Tools and agents use the working copy `data/campus_customs_new.db`.
- Model calls use `PORTKEY_API_KEY` from a local `.env`. The key is not written into code. `.env.example` has a placeholder only.
- Every agent uses `gpt-6-luna` through Portkey. No other model.
- Payments need a human yes before cash moves. The pay path refuses if the account would go negative.
- Drafts stay on the board. No real customer emails and no real vendor calls.
- One problem at a time. The next problem waits until you describe it.

### Folder map

```
hw5 Campus Customs/
├── AI_prompts.md
├── .env.example
├── data/
│   ├── campus_customs.db       original, do not edit
│   └── campus_customs_new.db   working copy
├── mcp_server/                 MCP tools
├── backend/                    FastAPI and the agent team
├── frontend/                   dispatch dashboard
├── prompts/                    prompt files as we write them
└── output/                     harness, smoke tests, ticket boards
```

---

## Problem 1: Vibe coder prompts

**Status:** Done. This file is the log.

**Prompt:**

> Hey Goldie: lets start HW 5 for AI foundations for managers. Please let me know you understand the assignement and youre ready for my prompts with all files located and folders zoned appropriately

**Follow-up:**

> create AI_prompts.md and keep it updated as we work. this is where i will describe each problem prompt and guide goldie accordingly. Goldie be sure to hafve one section for each problem and each section has to include: the problem number and title, at least one prompt i hvae typed in my own words and one follow-up prompr if it was needed with one sentence of what was lacking from the results of the inital prompt

The first prompt started Homework 5 and asked for the files and folders to be ready. It did not say to keep this log, or that each section needs the problem number and title, a prompt in your own words, and a follow-up with one sentence on what the first result lacked.

---

## Problem 2: Study the Campus Customs database

**Status:** Done. The original database was read, `data/campus_customs_new.db` is a fresh copy, and `output/harness.md` lists every field with one line on why the table matters.

**Prompt:**

> /Users/CEO/Library/Mobile Documents/com~apple~CloudDocs/YALE EMBA AI FOUNDATIONS/data.zip unzip to access data/campus_customes.db it shoul dhave tables that include desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments and invoices. As tickets get resolved make sure these tools update the referenced datbase making a copy of the databaases file called data/campus_customs_new.db pointing the MCP server and backend at this working copy. Make sur eyou keep campus_customs.db untouched

**Follow-up:**

> make sure you understand the rules for the shop and communicate them to me

The first prompt unpacked the database and pointed the servers at the working copy. It did not ask for the shop rules to be stated.

**Follow-up:**

> open data/campus_customs.db and look through all the tables and fields. copy the original file to data/campus_custom_new.db later problems need to update the working copy. then start output/harness.md and for each table list the fields and on short line on why the table matters for the agents

The rules follow-up named the shop constraints. It did not ask for every field listed in `output/harness.md`, or for one short line on why each table matters to the agents.

---

## Problem 3: Build the MCP server

**Status:** Done. Three FastMCP tools in `mcp_server/server.py` read `data/campus_customs_new.db`, and `output/harness.md` ties each tool to one ticket.

**Prompt:**

> write a MCP server in mcp_server/ using FastMCP which will talk to data/campus_customs_new.db every agent in this assignment will call on the tools in this MCP server. we will add mote tools to it later but for now write 3 tools you know you will need for the tickets and databases. Keep the names clear, never invent any data and only use information in the database

**Follow-up:**

> in output/harness.md list each of the 3 MCP tools and for every tool include: which table it reads, which ticket it helps unlock (101, 102 or 103) and 1 sentece o why that tool is the right one for that particular ticket

The first prompt asked for the three tools on the MCP server. It did not ask for `output/harness.md` to name each tool's table, the ticket it unlocks, and why that tool fits that ticket.

**Follow-up:**

> vagues lines like "reads inventory" score low - tie the tool to the ticket and also add a short mcp_server/README.md file that explains what the MCP server is for, wich databases file it uses and the threee tools it has

The harness follow-up asked for a table, a ticket, and one sentence per tool. It did not say those sentences had to use the ticket's own bill, lease, or size, and it did not ask for `mcp_server/README.md`.

---

## Problem 4: Add the MCP server to vibe coder and test each tool

**Status:** Done. Each tool was called through the MCP server, and `output/mcp_smoke.json` has the prompt, the tool name, and the output.

**Prompt:**

> have you added the MCP server to this project so the vive coder can call the tools? be sure to save the JSON teext in .mcp.json file under this project for the local MCP server list

**Follow-up:**

> Yo Goldie: for every tool be sure to include: the prompt askeds here in the vibe coder, the tool name, the tool output which must match the values in data/campus_customs_new.db

The first prompt saved the server list in `.mcp.json`. It did not ask to record, for each tool, the prompt, the tool name, and the output checked against the working database.

---

## Problem 5: Build the agent team and grow the MCP tools

**Status:** In progress. The five agents, their prompts, and the handoff loop are in place.

**Prompt:**

> now build the agentis team fort the campus customs using PydanticAI with the following orgaizational structure: Boss, Inventory, Accounting, Facilities and customer service. Show me a diagram once it is seuo to verify you hvae set it uo correctly. be sure to include prompts, models and agent loops so they can delegate work to each other with full connectivity

**Follow-up:**

> place the agent prompts in backend/prompts/ with one (1) file per agent. Put data types in backend/models.py and the agent files under backend/  then show me a layout schematic in side panel  with the 5 roles clearly laid ouit. each agent should use portkey_api_key and only gpt-6-luna for every agent

The first prompt built the team and asked for a delegation diagram. It did not ask for the file layout in a side panel, or for a check that every agent uses PORTKEY_API_KEY and only gpt-6-luna.

**Follow-up:**

> Note the jobs for the following agents sourced from my organizational strategy chatgpt prompt: Boss is Chief Executive Officer / General Manager, Inventory is Director of Inventory & Merchandising, Account is Director of Accounting & Finance, Facilities is Director of Facilities & Store Operations, and Customer Service is Director of Customer Experience. Each has a mission, departmental responsibilities, authority limits, and a reporting line to the Boss. The human owner keeps ultimate authority, and payments are never sent by an agent.

The layout follow-up placed the files and the model. It did not give the job titles, missions, or authority limits from the organizational strategy.

**Follow-up:**

> make sure agents are wired so they append to output/audit_trail.json as they run: for each agent-loop step record enough to audit later. append to this file and do not wiope it each run

The job-description follow-up set each department's mission and limits. It did not ask for an append-only record of every agent-loop step.

**Follow-up:**

> in the output/harness.md list each agent and each mcp tool (including ones added in this problem) Also add a short safety section that establishes firm guardrails for a real business so that agents dont touch real customers and real money and make sure reasonable limits for token useage are in play as this should not be and expensive project

The audit follow-up recorded each loop step. It did not ask for the harness to name every agent and tool, or for the customer, money, and token caps to be written down.

**Follow-up:**

> when asked for an elite array of tools for this project via chat: [the message continued with a five-agent stack of executive, inventory, accounting, facilities, and customer-service tools, plus Slack, Shopify, QuickBooks, n8n, and the other outside products]

The harness follow-up listed the three original tools. It did not add the ticket, shop-date, cash, price, and size-run reads the open tickets still needed, and it did not say which outside products stay unconnected.

**Follow-up:**

> verify guardrails are established and uodate the mcp_server/README.md so the tool list matches what we have in place

The elite-tools follow-up added the shop reads. It did not ask for a check that those reads cannot move cash or contact a customer, or for the README tool list to be matched to the server.

---

## Problem 6: Plan the three tickets

**Status:** Expected on tickets 101, 102, and 103 is in your words. Actual, Cash, and Reflection are empty.

**Prompt:**

> before we wire the backend of this project lets make sure we understand what I expect the team to do with each open ticket. Build output/desk_ticket.html this should be a page i can double-click with one tab per ticket (101, 102 and 103) be sure to also add empty cash and reflection tabs for later problem applications leaving them blank woith a "coming soon" note for now. on each ticket tab fill an expected section onlu while leaving room for an actual section i will fill after youo run the agents goldie

**Follow-up:**

> prompt me to let you know in my own words for each ticket's expected section who the boss should call and why, all the agent delegtions i expect not that the BOSS calls everyone and which MCP tools I should expect that run to ue. I want to avoid plans that send every specialist on every ticket as this is not efficient. I will ultimately compare this written plan to what actually take splace when we run the agents to resolve the threee tickets

The first prompt built the page and filled Expected from the shop records. It did not ask you to write, in your own words, who the Boss calls, which handoffs you expect, and which MCP tools that run should use.

**Follow-up:**

> 101 - agent should call inventory to verify we have the priduct, befor ecalling customner service to message that the order is in process before reporting results to the boss who will tell me (owner/human) how we fulfillgoing forward. then accounting reconciles payment with purchase. using aapprorpiate mcp tools

The prompt-me follow-up asked for all three tickets. This reply covers ticket 101 only.

**Follow-up:**

> 102 - when rent is due facilities should determine that there are not any operational issue preventing us from paying rent like the landlord not fulfilling lease requirement which shoul dbe reported to the boss who will determine its ok to pay. the acconting department should schedule rent check to arrive and landlord's office as long as boss has not reported any stop payment call relevant MCP tool to make process efficient

The 101 reply did not cover the rent ticket. This one does: Facilities checks the lease, the Boss can stop payment, and Accounting schedules the rent only if that stop is absent.

**Follow-up:**

> 103 - customer service works with inventory and account to varify that we have inventory for bulk order and that the boss is ok with a bulk order discount calling on relevant mcp tools to make process efficenitn

The 102 reply did not cover the hoodie ticket. This one does: Customer Service works with Inventory and Accounting, and the Boss has to approve the bulk discount.

---

## Problem 7: Backend routes

**Status:** In progress. The six routes are in `backend/main.py`, and the server is `http://localhost:8000`.

**Prompt:**

> our react frontend dashboard need aa backend it can call. in backend/main.py use a FastAPI and add route that do the following: return tyhe 3 tickets verifying whether they are open or resolved, take a ticket id and run the agent team on that ticket, return recent agent events with that each agent said and which tools they used so the actual board can refresh naturally, also approe a payment or purchase after a human clicks approve as aganet sshould  only prepare the pay and this route is what tangibly changes cash tracking, return the current chefking balance from cash_accounts, and reset the database to the original values when you want to try to fresh new run

**Follow-up:**

> from the backend/ folder start the server with: uvicorn main:app --reload --port 8000  which will turn our backend at http://localhost:8000 so the frontend dashboard can call those routes and in output/harness.md list each route in one line witht the URL and what it does

The first prompt asked for the six routes. It did not ask to start the server, or to list each URL and what it does in the harness.

---

## Problem 8: Agent dashboard

**Status:** In progress. The desk is the React app in `frontend/`.

**Prompt:**

> build the frontend dashboard in frontend/ with react + vite + typescript where the page should call the route i have built in previous problem and at minimum the board should perform the followinhg: lsit all 3 tickets, let me pick one ticket and start the agent team on it, show each agent and what theua re saying/doing while the ticket runs, mark a ticket resolved when the run finishes, show a short summary of what each agent did on that ticket, let a human approve a pay or purchase when asked, show the checking balance (it should drop after an approved pay) make sure this desk is a beautiful place to sit, it shoul dlook modern with carribbean beachfront motifs and people having great family time with the business's apparel on the beaches of trinidad and tobago after a week of carnival enjoying love, doubles, bake and shark and laughs with rum

**Follow-up:**

> make sure the front end talks to the backend at http://localhost:8000 where on the backend allos the vite page origin usually http:lllocalhost:5173 so the browser is allowed to all those routes and start the board with: npm run dev which opens the react desk in your browser so you can pick tickets and watch agents write output/design.md with what i have described ad the dashbaord look woth the layout and how agents read and resolve tickets and how cash flows show up in that organic real world beach life fashion that humans would enjoy

The first prompt built the desk and the beach look. It did not ask to confirm the Vite origin on the shop, to start `npm run dev`, or to write `output/design.md` in that beach-life voice.

**Follow-up:**

> find me actual shots of the beautiful caribbean beach to incorporate like a tourisim guide instead of the poor graphical representations you sourced

The origin follow-up kept a drawn bay. It did not ask for real beach photographs, set out like a travel guide.

**Follow-up:**

> make beach images more of a fluid collage interface that flows seamlessly and is not disjointed

The photograph follow-up put the shores in separate cards with caption bars between them. It did not ask for one continuous collage.

---

## Problem 9: Resolve the tickets

**Status:** Cash, the resolved-ticket file, the board page, and the harness are filled from the same three runs. Reflection is still empty.

**Prompt:**

> then before testing the agents on a full run over the three tickets, reset the workingh database data/campus_customs)new.db again so you start clean while noting the starting checking balance then run all theee tickets on the board (101, 102, 103) until each is resolved. Then opn output/desk_tickets.html from problem 6 on each ticket tab, fill the actual section from this run which agents worked, what they delegated, and which tools they used while keeping the expected section so you can compare the 2

**Follow-up:**

> on the cash tab of the same output?desk_tickets.html itemis the money with starting checking balance (after the reset), for each ticket include how cach changed when the ticket resolved and why with which pay/purchase, dollar amount and the ending checking balance which must match cash_accounts in the working database. we cannot have and cash loses due to poor math reconciliation even if the tickets are resolves. also make sure to save: output/resolved_tickets.json whereas for each ticket: id, final status, short outcome, what each agent contributed and any human approvals. output/resolved_board.html whereas a page you can double-click with a screenshot of the react board for each resolced tocket (101, 102 and 103) be sure to append real runs to output/audit_trail.json finsih outputt/harness.md so it covers tables, mcp tools, the five agents, api routes, the dashboard and safety rules

The first prompt filled Actual and left the cash tab, the resolved-ticket file, the board screenshots, and the finished harness for a later pass.

---

## Problem 10: Reflection

**Status:** All five answers are on the Reflection tab, each one tied to the ticket tabs and the Cash tab.

**Prompt:**

> please open output/desk_tickets.html and fill the relection tab and i need to answer in my own vibe being detaile dan thorough. please queue the questions from problem 10 relection here so ican answer them 1 by one

The first prompt asked for the questions and left the tab empty.

**Follow-up:**

> 101 - smooth and seamless without issue 102 - smooth and seamless without isse 103 - presented a limit issue so we had to rework how we address those matters so the boss is not called too many times.

That reply is the performance answer for tickets 101, 102, and 103. The first prompt had not collected it yet.

**Follow-up:**

> 101 and 102 worked as expected but 103 needed a more efficient process which should be saved as a pathway to work out similar issues in the future

That reply is the Actual-versus-Expected answer. The question before it had only asked how the agents performed.

**Follow-up:**

> 103 could have been handled soley by the boss or human as it required human thinking to resolve the matter

That reply is the one-agent answer. The question before it had only asked how Actual compared with the plan.

**Follow-up:**

> campus customs can run out of inventory and now it can replenish and keep certain pars always in production versus sales. Customer service needs to have the funtionality to queue emails and to punch down solutions like recommending alternative styles and accounting needs a calendar that is shared globallly for when recurring bills come up so we dont have to stop production becouse the rent is not paid or our vendors are not paid

That reply is the three problems this team could take. The question before it had only asked what one agent could have done.

**Follow-up:**

> 1. campus customs needs an app with a shopper experience, 2. capus customs needs client feedback and reviews on the website. 3. campus customs needs to showcase their seasonal releases through media like reels that are top notch productions

That reply is the three problems this team could not take. The question before it had only asked what the current tools could already handle.

**Follow-up:**

> tie very answer to this app and the three tickets we ran use the ticket tabs and cash tab on the same page as the evidence

That reply asks for the ticket tabs and the Cash tab under every answer. The answers before it named the judgments and did not yet cite those tabs.

---

## Problem 11: Submit to GitHub

**Status:** Waiting for your prompt.
