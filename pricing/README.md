# Pricing & Margin Strategy

This document provides per-asset cost calculations and recommended pricing with margins aligned to current market expectations for automated game asset generation.

## Goals

- Keep per-asset prices attractive for indies while achieving healthy margins.
- Reflect true variable costs: GPU time, CPU processing, storage, and CDN egress.
- Offer simple per-asset pricing and subscription bundles for predictability.

## Cost Inputs (Baselines)

- GPU: G4dn.xlarge (us-east-1)
  - On-Demand: $0.526/hour (~$0.0088/min)
  - Spot (avg): ~$0.158/hour (~$0.0026/min)
- CPU (Fargate/ASG): negligible for short tasks relative to GPU costs
- Storage: S3 Standard ~$0.023/GB-month
- CDN Egress: CloudFront ~$0.10/GB (region dependent; use $0.10 conservative)
- Reference: see [Server Cost Analysis](../server/README.md)

## Typical Step Durations

- Text → Image (SDXL, GPU): 6–12s
- Refine/Upscale (CPU/GPU): 2–6s
- Image → 3D (TripoSR, GPU): 12–20s
- Retopo (Blender, CPU): 45–90s
- Rigging (RigNet, GPU): 30–60s
- Animation (MDM/MoDi, GPU): 20–40s
- Export (Blender, CPU): 5–15s

## Per-Asset Variable Cost (Spot)

- 2D Sprite (TTI + Refine):
  - GPU ~10s (0.17 min) × $0.0026 ≈ $0.00044
  - Egress (5–10 MB): $0.0005–$0.001
  - Total: ~$0.001–$0.002
- 3D Character (TTI + TripoSR + Rig + CPU steps):
  - GPU ~70s (1.17 min) × $0.0026 ≈ ~$0.0030
  - Egress (150–250 MB): $0.015–$0.025
  - Storage (0.2 GB, 1 month): ~$0.0046
  - Total: ~$0.023–$0.033
- Animation Clip (20–40s GPU + 20 MB egress):
  - GPU 30s (0.5 min) × $0.0026 ≈ ~$0.0013
  - Egress (20 MB): ~$0.002
  - Total: ~$0.003–$0.004
- Background/VFX (2D heavy):
  - Similar to Sprite; Total: ~$0.002–$0.005 (higher if larger textures)

## Recommended Prices & Margins

- 2D Sprite / Background:
  - Price: $0.10–$0.25
  - Margin: ~98–99% (covers support, retries, storage months)
- 3D Character (Full Pipeline):
  - Price: $1.99–$4.99 (tier by quality presets and asset size)
  - Margin: ~85–99% (largest driver is CDN egress and storage duration)
- Animation Clip (per 3–5s loop):
  - Price: $0.49–$0.99
  - Margin: ~90–98%
- Bulk Exports (packs):
  - Price: $4.99–$19.99 depending on count/content
  - Margin: similar; apply volume discount

## Subscription Bundles (Examples)

- Indie ($19/month):
  - Includes: 50 2D assets + 3 3D characters + 10 clips
  - Overage: $0.20 per 2D, $2.00 per 3D, $0.49 per clip
- Studio ($99/month):
  - Includes: 500 2D assets + 50 3D characters + 100 clips
  - Overage: $0.15 per 2D, $1.50 per 3D, $0.39 per clip
- Enterprise:
  - Custom quotas, private CDN, SLAs; negotiated rates

## Pricing Calculator (Formulas)

- GPU Cost ($) = (gpu_minutes) × (gpu_rate_per_min)
  - Spot gpu_rate_per_min ≈ $0.0026; On‑Demand ≈ $0.0088
- Egress ($) = (asset_size_MB / 1024) × (egress_per_GB)
  - egress_per_GB default = $0.10
- Storage ($) = (asset_size_GB) × (months) × $0.023
- Total Variable Cost ($) = GPU + Egress + Storage + Minor CPU
- Price Recommendation ($) = Total Variable Cost × target_margin_multiplier
  - Suggested multipliers: 10×–50× for low-cost items; 5×–15× for high-value items

### Example (3D Character)

- GPU: 1.17 min × $0.0026 = $0.0030
- Egress: 200 MB → (200/1024) × $0.10 ≈ $0.0195
- Storage: 0.2 GB × 1 mo × $0.023 ≈ $0.0046
- Cost: ~$0.027
- Price: $2.99 (≈110× cost); Margin ≈ 99%

## Adjustments & Market Signals

- Lower prices if targeting mass indie adoption; increase for studio-grade QA or larger asset packs.
- If average asset sizes grow (e.g., 500 MB GLB + textures), raise price bands or add storage limits/archival.
- Offer regional pricing if CDN egress varies significantly.

## Notes

- Use signed URLs and per‑project namespaces to prevent asset leakage.
- Track egress per asset version to forecast costs and optimize delivery formats (Draco, KTX2).

---

## Safeguards & Dynamic Adjustments

- **Price Floors**: Minimum charge per transaction $0.10 to cover payment fees and support overhead.
- **Retry Overhead**: Add a 1.2× multiplier to GPU minutes to account for P95 retries/failures.
- **Retention Policy**: Default storage retention 30 days; archive thereafter. Restore fee applies for cold archives.
- **Micropayment Avoidance**: Prefer credit bundles (e.g., 100 credits = $10) for small 2D assets to reduce fees.
- **Regional Egress Variance**: Use $0.085–$0.12/GB depending on region; set default $0.10 and override per CDN billing.
- **SLA/Urgency Modifiers**: Priority compute adds +10–30% price; standard/batch queue is base price.
- **Data Residency**: Private CDN or region‑locked storage incurs +5–15% surcharge.

## Quality Presets (Guidance)

- **Basic**: 512–768 px initial, single pass refine; lowest cost, fastest.
- **Standard**: 1024 px initial, upscale to 2k; recommended default for game pipelines.
- **High Quality**: 2k initial or multi‑view, advanced refine; higher GPU minutes and larger egress (adjust price).

## Regional Egress Reference (Indicative)

- **US/EU**: ~$0.085–$0.11/GB
- **APAC**: ~$0.10–$0.12/GB
- **Notes**: Actual rates depend on edge location and tier; keep conservative default and measure monthly.
