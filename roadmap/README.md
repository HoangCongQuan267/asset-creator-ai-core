# Roadmap & Overseas Go-To-Market (From Vietnam)

This document outlines the product roadmap and a practical path to enter overseas markets (USA, EU, China) starting from Vietnam.

## Objectives

- Launch an end-to-end asset pipeline with production reliability
- Achieve overseas readiness: payments, compliance, delivery, support
- Keep COGS low and margins strong; scale via step queues and CDN

## Phased Plan

- **Phase 0 (Weeks 1–2)**: Foundations
  - Finalize backend orchestrator endpoints and DB schema
  - Infra as code (Terraform/CDK) for API, SQS per step, GPU/CPU pools, S3/CloudFront, EventBridge, DB
  - Bake GPU AMIs; enable warm pools; pin model weights
  - Add observability: metrics, tracing, logs; health dashboards
- **Phase 1 (Weeks 3–6)**: MVP
  - Implement Text→Image, 3D, Retopo, Rig, Export end-to-end
  - HITL review gates; asset library indexing; versioned delivery
  - Pricing and subscriptions live; credit bundles for micro-assets
  - UI polish; onboarding; docs; sample projects and templates
- **Phase 2 (Weeks 7–10)**: Beta International
  - Payment rails and tax compliance; regional pricing; currency
  - Global delivery optimizations (CloudFront, compression)
  - Support playbook; SLAs; incident response; status page
  - Developer relations: tutorials, sample repos, engine guides
- **Phase 3 (Weeks 11+)**: GA & Scale
  - Growth channels; partnerships; team workflows
  - Optional multi-region DR; DB global tables/read replicas
  - Enterprise features: SSO, audit, DPA, data residency

## Overseas GTM (USA/EU/China)

- **USA**
  - Payments: Stripe or Paddle; USD pricing; sales tax automation
  - Compliance: CCPA basics; standard privacy policy and ToS
  - Infra: Single-region GPU hub + CloudFront; optional Global Accelerator
  - Channels: Product Hunt, Unity Asset Store, Unreal Marketplace, Reddit r/gamedev
- **EU**
  - Payments: Stripe/Paddle with VAT handling; EUR pricing
  - Compliance: GDPR (data export, deletion, DPA); cookie consent
  - Infra: CloudFront; optional DynamoDB Global Tables or Postgres read replicas for DR
  - Localization: EN→DE/FR/ES landing pages; support times aligned
- **China**
  - Delivery: Mainland users behind GFW; consider local CDN (Alibaba Cloud or Tencent Cloud)
  - ICP: For a Mainland-hosted site, file ICP; otherwise deliver assets via local CDN buckets with cross-border replication
  - Payments: Alipay/WeChat via partners or local entity; or agency model with Paddle
  - Strategy: Start with cross-border delivery for enterprise trials; evaluate Mainland stack later

## Payments & Entity

- **Vietnam Base**: Use Paddle/PayPal/2Checkout for global coverage; Stripe via Singapore/Delaware entity if needed
- **Currencies**: USD/EUR/JPY/CNY; regional price bands based on egress and support costs
- **Invoices**: Tax ID, company name, country; automatic VAT/GST collection where required

## Legal & Compliance

- Terms of Service, Privacy Policy, Acceptable Use Policy
- Data Processing Addendum (GDPR), SCCs for EU data transfer
- Security: signed URLs, per-project namespaces, audit logs
- Content safety filters; incident response; breach notifications

## Localization & Support

- Languages: EN first; add Vietnamese, Mandarin, Japanese for landing pages
- Help Center: how-to guides, runbooks, FAQs, status page
- Support: email + chat; response targets; priority for paid tiers

## Infra Alignment

- See server design: [Server](../server/README.md)
- Pipeline orchestration and DB writes: [Pipeline](../pipeline/README.md), [Backend](../backend/README.md), [Database](../database/README.md)
- Global delivery via CloudFront; compression (Draco/KTX2) to reduce egress

## Pricing & Bundles

- Review pricing: [Top-Level README](../README.md#L73-L127) and [Pricing](../pricing/README.md)
- Tiered subscriptions with fair overages; regional pricing and currency display

## KPIs

- Time-to-first-asset, P95 latency per step
- Conversion rate from trial to paid
- Asset egress per user and per region
- Support resolution time; incident count

## Risks & Mitigations

- **Egress Costs**: Use compression and CDN; archive large assets; quotas per tier
- **Cold Starts**: AMI baking; warm pools; baseline on-demand nodes
- **Payment Coverage**: Use Paddle/PayPal until Stripe entity ready
- **China Delivery**: Start cross-border; move to local CDN after initial traction

## Next Steps

- Implement infra as code and seed DB schemas
- Launch MVP, instrument KPIs, iterate pricing

---

## Marketing Strategy

### Positioning

- Value: "From prompt to production‑ready assets in minutes — consistent, game‑engine‑ready"
- Differentiators: end‑to‑end pipeline, HITL review gates, clean topology, rigging, export, low COGS/pricing
- ICPs: indie teams, small studios, technical artists, prototyping teams, outsourcing vendors

### Channels

- Developer Communities: Reddit r/gamedev, r/IndieDev, Discord servers, Hacker News ShowHN
- Marketplaces: Unity Asset Store, Unreal Marketplace, itch.io tools section
- Content: tutorials, sample scenes, pipeline walkthroughs, engine‑specific guides
- Social Proof: case studies, before/after, performance benchmarks, live streams
- Partnerships: game engine factions, local VN studios, bootcamps, universities

### Product‑Led Growth

- Free tier or trial with limited assets; strong onboarding and templates
- Shareable asset links (CDN) and project portfolios; referral rewards
- In‑product prompts for upgrades when hitting quotas or high quality presets

### SEO & Content

- Keywords: "text to 3D", "auto rigging", "game asset generator", "Unity FBX export", "Unreal pipeline"
- Publish weekly: "How to go from prompt to rigged character", "KTX2 textures for faster delivery", "Retopo basics"
- Video tutorials on YouTube; short clips for TikTok/Instagram showcasing LODs and exports

### Launch Plan

- Pre‑launch list: landing page with demo; collect emails and use early access codes
- Launch: Product Hunt, ShowHN, Reddit posts, dev communities; offer limited‑time Studio tier discount
- Follow‑up: webinars; office hours; showcase user projects; feature library of styles/templates

### Pricing & Offers

- Region‑aware pricing (USD/EUR/CNY/JPY); indie‑friendly starter bundles
- Referral program: 10% credit bonus; affiliate partners for creators and educators
- Enterprise pilots: custom quotas, SSO, SLA; cross‑border delivery for China trials

### Metrics

- Activation: time to first asset; % completing end‑to‑end pipeline
- Engagement: assets per project; repeat rate; HITL approvals
- Conversion: trial→paid, bundle upgrades; referral rate
- Acquisition: channel performance; CAC per channel

### USA/EU/China Specifics

- USA: Stripe/Paddle, paid ads (limited), dev communities, marketplaces, outbound to small studios
- EU: GDPR compliance messaging, VAT pricing clarity, localized pages, partner with EU accelerators
- China: cross‑border enterprise pilots, local CDN partner, Mandarin landing page, WeChat/Alipay via partner

## Competitor Analysis

| Competitor Category | Key Players                                 | Strengths                                                   | Our Gaps / Weaknesses                                                                    | **Our Winning Edge (Differentiation)**                                                                                 |
| :------------------ | :------------------------------------------ | :---------------------------------------------------------- | :--------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **2D Gen AI**       | MidJourney, Stable Diffusion, Adobe Firefly | High artistic quality, massive datasets, brand recognition. | We rely on open models (SDXL/Kandinsky) which may lag slightly in "raw art" consistency. | **Game-Ready Pipeline**: We don't just make images; we make sprites, spines, and textures ready for engines.           |
| **3D Gen AI**       | Luma AI, Meshy, CSM, TripoSR                | Fast mesh generation, strong reconstruction from video.     | Some have better "text-to-mesh" fidelity in isolation.                                   | **Topology & Rigging**: They output messy meshes. We output **retopologized, UV-mapped, rigged characters** with LODs. |
| **Asset Stores**    | Unity Asset Store, TurboSquid, Sketchfab    | Massive library of human-made assets, verified quality.     | Instant availability (no generation wait time).                                          | **Customizability & Cost**: We allow _infinite_ variations for $1.50 vs $30-$100 for a static asset.                   |
| **Avatar Systems**  | Ready Player Me, VRoid                      | Perfect rigging, high quality anime/stylized avatars.       | They are specialized in avatars only; hard to break their specific style.                | **Versatility**: We handle props, environments, monsters, and distinct styles, not just one avatar type.               |

### Strategic Implications

1.  **Don't Fight on "Art Quality" Alone**: MidJourney wins on pure pixels. We win on **"Usability"**.
2.  **Own the "Technical Artist" Pipeline**: Focus on the boring stuff that saves time—UVs, Rigging, LODs, Export formats.
3.  **Price for Volume**: Competitors charge high subscriptions ($30+/mo). We capture the long tail with pay-as-you-go and low-cost bundles.
4.  **Ship Unity/Unreal Guides**: Reduce import friction to zero.

### Detailed Landscape

- **2D Generation**: MidJourney, Stable Diffusion (ComfyUI/Automatic1111), Adobe Firefly
- **3D Generation**: Luma AI, Meshy, Kaedim, TripoSR/Rodin, Gaussian Splatting toolchains
- **Pipelines/Assets**: Ready Player Me, Sloyd, CGTrader/TurboSquid libraries
- **Scanning**: Polycam, RealityCapture; strong for photogrammetry but not auto‑retopo/rig/export

### Observed Gaps

- Few deliver end‑to‑end from prompt to engine‑ready assets with consistent topology, UVs, LODs, rigging, and export
- Limited batch/API workflows, job orchestration, and project‑level asset libraries
- Weak guarantees on PBR material compliance and game engine import friction
- Opaque or high pricing for enterprise; limited indie‑friendly per‑asset models

### Notable Competitors

- **MidJourney**: best‑in‑class 2D; no 3D or game‑ready export; complementary for concepting
- **Luma AI**: strong reconstruction; limited topology/LOD/export control for games
- **Meshy**: text‑to‑3D; pipeline coverage improving but retopo/rig/export consistency varies
- **Kaedim**: image‑to‑3D with retopo; more manual/higher pricing; enterprise focus
- **Ready Player Me**: avatar domain; excellent engine integrations; narrow asset category
- **Sloyd**: parametric low‑poly; fast but not generative and limited versatility
