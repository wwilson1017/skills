---
name: site-redo
description: Take a small business from "here's my current website" to a clickable beta of their new one. An intake form the client fills in on their own time, a short call transcript, and a crawl of the existing site go into a brief. Several agents design different homepage options, the owner picks one, and the whole site is built in that style, reviewed, and published for tweaking. Use when the user says "site redo", "new website for <client>", "website intake", or runs /site-redo <client>.
argument-hint: "<client or business name>"
---

# Site redo

Take one small business from their current site to a clickable beta. Client details (names, phone numbers, addresses) stay in a local folder that is not a git repo.

## What you need

- A place to host the intake form and the working pages (Simple Sites, or the same hosted-page collector this user already uses for grill-me pages). Configure the host in a local config file, not in this skill.
- The current site's URL and the business name.

## Flow

1. **New client.** Create `~/site-redo/<slug>/` (local, not a repo). Mint an intake form the client can fill in on their own time. The form collects what visitors should do on the site, how those requests are handled, hours, pages, tools, reviews, and sites they like. Send the client the link. Optionally record a short call and drop the transcript beside the form answers.
2. **Brief.** Crawl the current site. Combine the crawl, the intake, and the call into a short brief in the client folder.
3. **Homepage options.** Several agents each design a different homepage from the brief. Publish every option with its own link. The owner picks one.
4. **Build the beta.** Build the rest of the site in the chosen style. Review it (including on a phone-sized screen). Publish a beta the client can click through. Each republish is a new version; old links the client already has should not go dead. A dashboard for the job lists the intake state, the homepage options, and every beta version.
5. **Tweak and hand off.** Apply the client's notes. When they are happy, hand over the files and the live beta link.

## Rules

- Do not put client PII in git, in the skill, or on a public repo.
- Intake pages and betas are unlisted, not secret. No passwords or private message text on them.
- Keep host-specific wiring (collectors, dashboards, watchdogs) in local scripts or config, not hard-coded to one company's domain.
