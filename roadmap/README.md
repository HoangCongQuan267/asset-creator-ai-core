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
- Begin USA/EU GTM; pilot China via cross-border CDN + enterprise trials
