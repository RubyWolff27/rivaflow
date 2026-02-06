# Stripe Payment Gateway — Integration Scope

**Date:** February 2026
**Status:** Scoping Only — DO NOT BUILD YET
**Author:** Claude Opus 4.6 (AI-generated, review before implementation)

---

## 1. Product & Price Structure

### Subscription Tiers

| Tier | Price (AUD) | Billing | Features |
|------|------------|---------|----------|
| **Free** | $0 | — | Basic session logging, 30-day history, 3 friends, public feed |
| **Premium Monthly** | $7.99/mo | Monthly | Unlimited history, advanced analytics, unlimited friends, photo storage (50), PDF/CSV export |
| **Premium Annual** | $59.99/yr | Annual | Same as Premium Monthly (save 37%) |
| **Lifetime** | $149 one-time | One-time | All Premium features forever, limited availability, early adopter badge |
| **Coach** | $29.99/mo | Monthly | All Premium + student management (30), team analytics, curriculum builder, class scheduling |

### Stripe Products Setup

```
Product: "RivaFlow Premium"
  - Price: $7.99 AUD / month (recurring)
  - Price: $59.99 AUD / year (recurring)

Product: "RivaFlow Lifetime"
  - Price: $149 AUD (one-time)

Product: "RivaFlow Coach"
  - Price: $29.99 AUD / month (recurring)
```

---

## 2. Checkout Flow

### Recommended: Stripe Checkout (Hosted)

Use **Stripe Checkout** (hosted payment page) rather than embedded/custom forms:

- PCI-compliant out of the box (no card data touches our servers)
- Handles 3D Secure, Apple Pay, Google Pay automatically
- Mobile-optimised by Stripe
- Supports coupons and trials natively
- Less development effort (~4 hours vs ~20 hours for custom)

### Flow

```
User clicks "Upgrade to Premium"
  → Frontend calls POST /api/v1/billing/create-checkout-session
  → Backend creates Stripe Checkout Session with:
      - price_id (from selected plan)
      - customer_email (from user profile)
      - success_url: /billing/success?session_id={CHECKOUT_SESSION_ID}
      - cancel_url: /billing/cancelled
      - metadata: { user_id, tier }
  → Backend returns session URL
  → Frontend redirects to Stripe Checkout page
  → User completes payment on Stripe
  → Stripe redirects to success_url
  → Webhook fires: checkout.session.completed
  → Backend updates user tier
```

### With Waitlist Integration

```
Admin invites waitlist entry with tier="premium"
  → Invite email sent with link: /register?invite=TOKEN
  → User registers (free account created)
  → Immediately redirected to Stripe Checkout for Premium
  → On payment success: tier upgraded to premium
  → If user cancels checkout: stays on free tier with note

Admin invites with tier="free" or "lifetime_premium"
  → No checkout required (free or gifted)
  → Account created with assigned tier directly
```

---

## 3. Subscription Management

### Stripe Customer Portal

Use **Stripe Customer Portal** for self-service billing management:

- Update payment method
- View invoices and receipts
- Cancel subscription
- Switch between monthly/annual
- Resume cancelled subscription

```
User clicks "Manage Subscription" in Settings
  → Frontend calls POST /api/v1/billing/create-portal-session
  → Backend creates Stripe Billing Portal Session
  → Frontend redirects to Stripe portal
  → User manages billing
  → Stripe redirects back to app
```

---

## 4. Webhook Events

### Events to Handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Upgrade user tier, store Stripe customer_id |
| `invoice.paid` | Confirm subscription active, extend access |
| `invoice.payment_failed` | Send email warning, grace period (3 days) |
| `customer.subscription.updated` | Handle plan changes (monthly ↔ annual) |
| `customer.subscription.deleted` | Downgrade to free tier |
| `customer.subscription.paused` | Pause premium features (if enabled) |

### Webhook Endpoint

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)

    match event["type"]:
        case "checkout.session.completed":
            handle_checkout_completed(event["data"]["object"])
        case "invoice.payment_failed":
            handle_payment_failed(event["data"]["object"])
        case "customer.subscription.deleted":
            handle_subscription_cancelled(event["data"]["object"])
```

### Security
- Verify webhook signature using `STRIPE_WEBHOOK_SECRET`
- Idempotency: check if event already processed (store event IDs)
- Use raw request body for signature verification (not parsed JSON)

---

## 5. Tier Upgrade/Downgrade Logic

### Database Changes

```sql
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT;
ALTER TABLE users ADD COLUMN tier_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN payment_status TEXT DEFAULT 'none';
-- payment_status: none, active, past_due, cancelled, lifetime
```

### Tier Transitions

| From | To | Trigger | Action |
|------|----|---------|--------|
| free | premium | checkout.session.completed | Set tier='premium', store stripe IDs |
| free | lifetime | Admin assigns OR checkout | Set tier='lifetime_premium', payment_status='lifetime' |
| premium | free | subscription.deleted | Set tier='free', clear stripe IDs |
| premium (monthly) | premium (annual) | subscription.updated | Update billing cycle, no tier change |
| any | free | payment_failed (after grace) | Downgrade, restrict features |

### Feature Gating

```python
def require_premium(current_user: dict):
    if current_user.get("tier") not in ("premium", "lifetime_premium", "coach"):
        raise HTTPException(403, "Premium feature. Upgrade to access.")
```

Frontend: Check `user.tier` and show upgrade prompt for gated features.

---

## 6. Australian Requirements

### GST (Goods & Services Tax)
- Australia requires 10% GST on digital services
- Stripe Tax can handle this automatically
- Prices should be GST-inclusive (display $7.99 AUD incl. GST)
- Configure Stripe Tax with Australian tax registration

### Currency
- Default currency: AUD
- Stripe handles currency display and conversion
- Set `currency: 'aud'` on all Price objects

### Stripe Australia
- Register Stripe account in Australia
- ABN required for business account
- Payouts in AUD to Australian bank account
- 1.75% + $0.30 AUD per transaction (domestic cards)
- 2.9% + $0.30 AUD (international cards)

### Legal
- Must display prices inclusive of GST
- Must provide tax invoices/receipts (Stripe does this)
- Must have refund policy displayed
- Australian Consumer Law applies (cooling-off periods for subscriptions)

---

## 7. Free Trial Option

### Recommended: 14-Day Premium Trial

```
New user registers → Free tier
  → Prompt: "Try Premium free for 14 days"
  → If yes: Stripe Checkout with trial_period_days=14
  → No payment required during trial (Stripe handles this)
  → After 14 days: auto-charge or downgrade to free
  → User can cancel trial anytime via Customer Portal
```

Stripe handles trial lifecycle automatically with `subscription_data.trial_period_days`.

---

## 8. Implementation Architecture

### Backend Files

```
rivaflow/api/routes/billing.py          # Checkout, portal, webhook endpoints
rivaflow/core/services/billing_service.py   # Stripe API calls, tier logic
rivaflow/db/migrations/0XX_billing.sql  # stripe_customer_id, subscription columns
```

### Frontend Files

```
web/src/pages/Pricing.tsx       # Public pricing page
web/src/pages/BillingSuccess.tsx  # Post-checkout success
web/src/components/UpgradePrompt.tsx  # Already exists — wire to checkout
web/src/api/client.ts           # Add billingApi methods
```

### Environment Variables

```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PREMIUM_MONTHLY_PRICE_ID=price_...
STRIPE_PREMIUM_ANNUAL_PRICE_ID=price_...
STRIPE_LIFETIME_PRICE_ID=price_...
STRIPE_COACH_PRICE_ID=price_...
```

---

## 9. Effort Estimate

| Task | Effort | Priority |
|------|--------|----------|
| Stripe account setup + products | 1 hour | P0 |
| Backend: billing routes + webhook | 6 hours | P0 |
| Backend: tier gating middleware | 2 hours | P0 |
| Database migration | 30 mins | P0 |
| Frontend: pricing page | 3 hours | P0 |
| Frontend: upgrade prompts | 2 hours | P1 |
| Frontend: billing settings | 2 hours | P1 |
| Testing (end-to-end with Stripe test mode) | 4 hours | P0 |
| GST/tax configuration | 1 hour | P1 |
| Documentation | 1 hour | P2 |

**Total: ~22 hours (3-4 days)**

---

## 10. Transition from Waitlist

### Phase 1 (Current): Waitlist → Admin Invite → Free/Lifetime Access
- No Stripe required
- Admin manually assigns tier

### Phase 2 (Next): Waitlist → Admin Invite → Optional Stripe Checkout
- Free tier invites: direct registration (no payment)
- Premium invites: registration → Stripe Checkout → premium access
- Lifetime invites: admin-gifted (no payment)

### Phase 3 (Future): Open Registration → Free Tier → Stripe Upgrade
- Remove waitlist gating
- Anyone can register (free tier)
- Upgrade via Stripe Checkout
- Waitlist becomes marketing/lead gen tool only

---

## Recommendation

**Build Phase 2 when reaching ~100 active users.** The waitlist architecture is already designed to support this transition. Focus on user acquisition and retention first — monetisation should follow product-market fit.

**Key decision needed from Ruby:**
1. Which Stripe plan to use (Standard vs Express)?
2. Trial period: 14 days or 7 days?
3. Launch with monthly only, or monthly + annual from day 1?
4. Lifetime tier: how many to offer? (Creates urgency if limited)

---

*This document is for planning purposes. Flag to Ruby for business decisions before implementation.*
