# RivaFlow -- Stripe Payment Integration Scope

**Document version:** 1.0
**Date:** 2026-02-07
**Status:** Draft / Scoping
**Author:** Engineering

---

## Table of Contents

1. [Overview](#1-overview)
2. [Stripe Products and Prices](#2-stripe-products-and-prices)
3. [Checkout Flow](#3-checkout-flow)
4. [Subscription Management](#4-subscription-management)
5. [Webhooks](#5-webhooks)
6. [Tier Mapping and Database Schema](#6-tier-mapping-and-database-schema)
7. [Waitlist Integration](#7-waitlist-integration)
8. [Australian Requirements](#8-australian-requirements)
9. [Free Trial Option](#9-free-trial-option)
10. [Architecture Diagram](#10-architecture-diagram)
11. [Tech Stack](#11-tech-stack)
12. [Implementation Plan](#12-implementation-plan)
13. [Security Considerations](#13-security-considerations)
14. [Open Questions](#14-open-questions)

---

## 1. Overview

RivaFlow is an Australian-based BJJ (Brazilian Jiu-Jitsu) training tracker
application. This document defines the scope, architecture, and implementation
plan for integrating Stripe as the payment provider to monetise the platform
through tiered subscription plans and a one-time lifetime purchase option.

**Goals:**

- Accept recurring and one-time payments in AUD via Stripe.
- Minimise PCI compliance burden by using Stripe-hosted Checkout.
- Provide self-service billing management through the Stripe Customer Portal.
- Maintain a clean mapping between Stripe subscription state and the
  application's existing `subscription_tier` column.
- Comply with Australian GST obligations.

---

## 2. Stripe Products and Prices

Three pricing options will be configured in the Stripe Dashboard (and
synchronised via the API in production):

| Product            | Price         | Billing     | Stripe Type          | Notes                        |
|--------------------|---------------|-------------|----------------------|------------------------------|
| Premium Monthly    | $7.99 AUD/mo  | Recurring   | `price` (recurring)  | Standard monthly plan        |
| Premium Annual     | $59.99 AUD/yr | Recurring   | `price` (recurring)  | Save ~37% vs monthly         |
| Lifetime Premium   | $149.00 AUD   | One-time    | `price` (one_time)   | Limited availability         |

### Stripe Dashboard Configuration

```
Product: "RivaFlow Premium"
  - Price: $7.99 AUD / month   (lookup_key: premium_monthly)
  - Price: $59.99 AUD / year   (lookup_key: premium_annual)

Product: "RivaFlow Lifetime Premium"
  - Price: $149.00 AUD / once  (lookup_key: lifetime_premium)
```

### Price ID Management

Price IDs will be stored as environment variables, never hard-coded:

```bash
STRIPE_PRICE_PREMIUM_MONTHLY=price_xxxxxxxxxxxxxxxx
STRIPE_PRICE_PREMIUM_ANNUAL=price_xxxxxxxxxxxxxxxx
STRIPE_PRICE_LIFETIME=price_xxxxxxxxxxxxxxxx
```

### Annual Savings Calculation

Monthly cost over 12 months: $7.99 x 12 = $95.88 AUD
Annual plan cost: $59.99 AUD
Savings: $95.88 - $59.99 = $35.89 AUD (~37.4%)

---

## 3. Checkout Flow

### Recommended Approach: Stripe Checkout (Hosted)

We recommend **Stripe Checkout** (the Stripe-hosted payment page) rather than
Stripe Elements (embedded form). Rationale:

- **PCI compliance**: Stripe Checkout is fully hosted, so RivaFlow never
  touches raw card data. This keeps us in SAQ-A scope (the lightest PCI
  obligation).
- **Conversion optimisation**: Stripe continuously A/B tests the Checkout UI
  for conversion. We benefit automatically.
- **Apple Pay / Google Pay**: Supported out of the box with zero additional
  integration effort.
- **3D Secure / SCA**: Handled transparently by Stripe.
- **Reduced engineering effort**: No need to build or maintain a custom payment
  form.

### End-to-End Checkout Flow

```
1. User clicks "Upgrade to Premium" in the RivaFlow UI.
2. Frontend sends POST /api/v1/billing/checkout-session with the selected
   price_lookup_key (e.g. "premium_monthly").
3. Backend creates a Stripe Checkout Session via the API, embedding the
   user's internal ID in the session metadata.
4. Backend returns the Checkout Session URL to the frontend.
5. Frontend redirects the user to the Stripe-hosted Checkout page.
6. User completes payment on Stripe's domain.
7. Stripe redirects the user back to RivaFlow's success URL:
   https://app.rivaflow.com.au/billing/success?session_id={CHECKOUT_SESSION_ID}
8. In parallel, Stripe fires a checkout.session.completed webhook to the
   RivaFlow backend.
9. The webhook handler verifies the signature, extracts the user ID from
   metadata, and upgrades the user's subscription_tier.
10. The success page polls or checks the user's updated tier and displays
    a confirmation.
```

### Checkout Session Creation (Backend)

```python
# rivaflow/api/v1/billing.py

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from rivaflow.auth.dependencies import get_current_user
from rivaflow.config import settings

router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_LOOKUP = {
    "premium_monthly": settings.STRIPE_PRICE_PREMIUM_MONTHLY,
    "premium_annual": settings.STRIPE_PRICE_PREMIUM_ANNUAL,
    "lifetime": settings.STRIPE_PRICE_LIFETIME,
}


class CheckoutRequest(BaseModel):
    price_lookup_key: str


@router.post("/checkout-session")
async def create_checkout_session(
    body: CheckoutRequest,
    current_user=Depends(get_current_user),
):
    price_id = PRICE_LOOKUP.get(body.price_lookup_key)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid price selection.")

    # Determine mode: "subscription" for recurring, "payment" for one-time
    mode = "payment" if body.price_lookup_key == "lifetime" else "subscription"

    # Reuse existing Stripe customer if the user already has one
    customer_kwargs = {}
    if current_user.stripe_customer_id:
        customer_kwargs["customer"] = current_user.stripe_customer_id
    else:
        customer_kwargs["customer_email"] = current_user.email

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=(
                f"{settings.FRONTEND_URL}/billing/success"
                f"?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={
                "rivaflow_user_id": str(current_user.id),
                "price_lookup_key": body.price_lookup_key,
            },
            **customer_kwargs,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e.user_message}")

    return {"checkout_url": session.url}
```

### Frontend Redirect (React)

```tsx
// src/components/UpgradeButton.tsx

import { useState } from "react";
import { api } from "@/lib/api";

interface UpgradeButtonProps {
  priceLookupKey: "premium_monthly" | "premium_annual" | "lifetime";
  label: string;
}

export function UpgradeButton({ priceLookupKey, label }: UpgradeButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/billing/checkout-session", {
        price_lookup_key: priceLookupKey,
      });
      // Redirect to Stripe-hosted Checkout
      window.location.href = data.checkout_url;
    } catch (err) {
      console.error("Failed to create checkout session:", err);
      setLoading(false);
    }
  };

  return (
    <button onClick={handleUpgrade} disabled={loading}>
      {loading ? "Redirecting..." : label}
    </button>
  );
}
```

---

## 4. Subscription Management

### Stripe Customer Portal

For all post-purchase billing actions, we use the **Stripe Customer Portal**
(hosted by Stripe). This avoids building custom UI for:

- Viewing invoices and payment history
- Updating payment methods
- Switching between monthly and annual plans
- Cancelling a subscription

### Portal Session Creation

```python
@router.post("/portal-session")
async def create_portal_session(
    current_user=Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Please subscribe first.",
        )

    session = stripe.billing_portal.Session.create(
        customer=current_user.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings/billing",
    )
    return {"portal_url": session.url}
```

### Portal Configuration (Stripe Dashboard)

The Customer Portal must be configured in the Stripe Dashboard to allow:

- **Invoice history**: Enabled
- **Payment method update**: Enabled
- **Subscription cancellation**: Enabled, with immediate or end-of-period options
- **Plan switching**: Enabled (monthly <-> annual), with proration
- **Branding**: RivaFlow logo, colour scheme (#1a1a2e primary)

---

## 5. Webhooks

Webhooks are the **authoritative source of truth** for payment state. The
success redirect URL is only used for UX; the actual tier change must always
be driven by a verified webhook.

### Events to Handle

| Event                              | Action                                                        |
|------------------------------------|---------------------------------------------------------------|
| `checkout.session.completed`       | Upgrade user tier; store `stripe_customer_id` and `stripe_subscription_id` |
| `invoice.paid`                     | Confirm renewal; extend `subscription_valid_until`            |
| `invoice.payment_failed`           | Notify user via email; begin grace period (7 days)            |
| `customer.subscription.deleted`    | Downgrade user to `free` tier                                 |
| `customer.subscription.updated`    | Handle plan changes (monthly <-> annual)                      |

### Webhook Signature Verification

Every incoming webhook **must** be verified using the endpoint's signing
secret. Unverified payloads must be rejected with HTTP 400.

```python
# rivaflow/api/v1/webhooks.py

import stripe
from fastapi import APIRouter, Request, HTTPException

from rivaflow.config import settings
from rivaflow.services.billing import BillingService

router = APIRouter(tags=["webhooks"])

WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # --- Signature verification (critical) ---
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=WEBHOOK_SECRET,
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature -- do not trust this request
        raise HTTPException(status_code=400, detail="Invalid signature")

    # --- Route event to handler ---
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(data)
    elif event_type == "invoice.paid":
        await handle_invoice_paid(data)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(data)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(data)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data)
    else:
        # Unhandled event type -- log and acknowledge
        pass

    # Always return 200 to acknowledge receipt; Stripe retries on non-2xx
    return {"status": "ok"}


async def handle_checkout_completed(session: dict):
    """
    Fires when a customer completes Checkout. This is the primary trigger
    for upgrading a user's tier.
    """
    user_id = session["metadata"]["rivaflow_user_id"]
    price_key = session["metadata"]["price_lookup_key"]
    stripe_customer_id = session["customer"]

    if price_key == "lifetime":
        new_tier = "lifetime_premium"
        subscription_id = None
    else:
        new_tier = "premium"
        subscription_id = session.get("subscription")

    await BillingService.upgrade_user(
        user_id=user_id,
        new_tier=new_tier,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription_id,
    )


async def handle_invoice_paid(invoice: dict):
    """
    Fires on every successful payment (including the first). For renewals
    this confirms the subscription is still active.
    """
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return  # One-time payment; already handled by checkout.session.completed

    await BillingService.confirm_renewal(
        stripe_subscription_id=subscription_id,
    )


async def handle_payment_failed(invoice: dict):
    """
    Fires when a recurring payment fails. We notify the user and start a
    7-day grace period before downgrading.
    """
    customer_id = invoice["customer"]
    await BillingService.start_grace_period(
        stripe_customer_id=customer_id,
        grace_days=7,
    )


async def handle_subscription_deleted(subscription: dict):
    """
    Fires when a subscription is fully cancelled (after any remaining
    billing period). Downgrade the user to free.
    """
    subscription_id = subscription["id"]
    await BillingService.downgrade_user(
        stripe_subscription_id=subscription_id,
        new_tier="free",
    )


async def handle_subscription_updated(subscription: dict):
    """
    Fires when a subscription is modified (e.g. plan switch, pause, resume).
    Update internal records accordingly.
    """
    subscription_id = subscription["id"]
    price_id = subscription["items"]["data"][0]["price"]["id"]
    await BillingService.sync_subscription(
        stripe_subscription_id=subscription_id,
        stripe_price_id=price_id,
    )
```

### Webhook Endpoint Registration

Register the endpoint in the Stripe Dashboard or via the CLI:

```bash
# Development (Stripe CLI forwarding)
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Production (Stripe Dashboard)
# Endpoint URL: https://api.rivaflow.com.au/api/v1/webhooks/stripe
# Events:
#   - checkout.session.completed
#   - invoice.paid
#   - invoice.payment_failed
#   - customer.subscription.deleted
#   - customer.subscription.updated
```

### Idempotency

Stripe may deliver the same event more than once. All webhook handlers must
be **idempotent**. The recommended approach is to store the `event.id` in a
`processed_stripe_events` table and skip duplicates:

```python
async def is_event_processed(event_id: str) -> bool:
    """Check if we have already processed this Stripe event."""
    existing = await db.fetch_one(
        "SELECT 1 FROM processed_stripe_events WHERE stripe_event_id = :eid",
        {"eid": event_id},
    )
    return existing is not None


async def mark_event_processed(event_id: str) -> None:
    """Record that we have processed this Stripe event."""
    await db.execute(
        "INSERT INTO processed_stripe_events (stripe_event_id, processed_at) "
        "VALUES (:eid, NOW())",
        {"eid": event_id},
    )
```

---

## 6. Tier Mapping and Database Schema

### Existing Tiers

The application already defines three subscription tiers:

| Tier                | Description                                |
|---------------------|--------------------------------------------|
| `free`              | Default tier after registration             |
| `premium`           | Monthly or annual paid subscription         |
| `lifetime_premium`  | One-time purchase; never expires            |

### Database Changes

Add the following columns to the `users` table (or a dedicated
`user_subscriptions` table):

```sql
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_valid_until TIMESTAMP;
ALTER TABLE users ADD COLUMN grace_period_end TIMESTAMP;
ALTER TABLE users ADD COLUMN trial_ends_at TIMESTAMP;
```

Create the idempotency table:

```sql
CREATE TABLE processed_stripe_events (
    id SERIAL PRIMARY KEY,
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stripe_event_id ON processed_stripe_events (stripe_event_id);
```

### Tier Transition Rules

```
checkout.session.completed (monthly/annual)  -->  subscription_tier = "premium"
checkout.session.completed (lifetime)        -->  subscription_tier = "lifetime_premium"
invoice.paid (renewal)                       -->  subscription_tier remains "premium"
                                                  subscription_valid_until extended
invoice.payment_failed                       -->  subscription_tier remains "premium"
                                                  grace_period_end set to NOW() + 7 days
grace_period_end reached                     -->  subscription_tier = "free"
customer.subscription.deleted                -->  subscription_tier = "free"
trial_ends_at reached (no payment)           -->  subscription_tier = "free"
```

### Tier Check Middleware

```python
# rivaflow/auth/permissions.py

from functools import wraps
from fastapi import HTTPException


def require_premium(func):
    """Decorator that restricts an endpoint to premium or lifetime_premium users."""
    @wraps(func)
    async def wrapper(*args, current_user, **kwargs):
        if current_user.subscription_tier not in ("premium", "lifetime_premium"):
            raise HTTPException(
                status_code=403,
                detail="This feature requires a Premium subscription.",
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
```

---

## 7. Waitlist Integration

### Current Flow (Pre-Stripe)

```
1. User signs up for waitlist (email + name).
2. Admin reviews and sends invite link.
3. User registers via invite link.
4. User is assigned either:
   - "free" tier (standard invite), or
   - "lifetime_premium" tier (early supporter / promo invite).
```

### Future Flow (Post-Stripe)

```
1. User signs up for waitlist (email + name).
2. Admin reviews and sends invite link with an embedded invite_type parameter.
3. User clicks invite link and lands on the registration page.
4. Based on invite_type:

   invite_type = "free"
     --> Standard registration flow
     --> subscription_tier = "free"
     --> No Stripe interaction

   invite_type = "premium"
     --> Registration flow
     --> After account creation, redirect to Stripe Checkout
     --> On successful payment, subscription_tier = "premium"
     --> On cancellation/abandonment, account exists at "free" tier

   invite_type = "lifetime_premium"
     --> Registration flow
     --> subscription_tier = "lifetime_premium" (granted by admin, no payment)
```

### Invite Link Structure

```
https://app.rivaflow.com.au/register?invite_token=abc123&invite_type=premium
```

The `invite_token` is validated server-side. The `invite_type` determines
whether the user is routed through Stripe Checkout after account creation.

---

## 8. Australian Requirements

### GST (Goods and Services Tax)

Australia requires 10% GST on digital services sold to Australian consumers.

**Approach:** All advertised prices are **GST-inclusive**. The GST component is
calculated as `price / 11` (since the 10% is already included in the total).

| Product          | Total (incl. GST) | GST Component | Ex-GST Price |
|------------------|--------------------|---------------|--------------|
| Premium Monthly  | $7.99 AUD          | $0.73         | $7.26        |
| Premium Annual   | $59.99 AUD         | $5.45         | $54.54       |
| Lifetime Premium | $149.00 AUD        | $13.55        | $135.45      |

### Stripe Tax Configuration

```python
# When creating Checkout sessions, enable automatic tax collection:
session = stripe.checkout.Session.create(
    # ... other params ...
    automatic_tax={"enabled": True},
)
```

Alternatively, configure tax rates manually in the Stripe Dashboard:

```
Tax Rate: "AU GST"
  - Percentage: 10%
  - Inclusive: Yes
  - Country: AU
  - Description: "Goods and Services Tax"
```

### Stripe Australia Account

- The Stripe account must be registered as an **Australian entity**.
- An **ABN (Australian Business Number)** is required for the Stripe account
  and must appear on all invoices/receipts.
- Default currency: **AUD**.
- Stripe will deposit funds into an Australian bank account.

### Invoice Requirements

Australian tax invoices for amounts over $82.50 (incl. GST) must include:

- Seller's ABN
- Seller's identity (business name)
- Date of issue
- Description of items
- GST amount
- Total amount

Stripe invoices can be configured to include all of these via Dashboard
settings under **Settings > Branding > Invoice**.

---

## 9. Free Trial Option

### Trial Configuration

- **Duration:** 14 days
- **Payment method required:** No (reduces friction for trial sign-up)
- **Auto-downgrade:** After 14 days, if the user has not subscribed, they
  revert to the `free` tier automatically.

### Implementation

Since the trial does not require a payment method, it is managed
**application-side** rather than through Stripe's built-in trial mechanism
(which requires a subscription object).

```python
# rivaflow/services/billing.py

from datetime import datetime, timedelta


async def start_free_trial(user_id: str) -> None:
    """Activate a 14-day premium trial for the user."""
    trial_end = datetime.utcnow() + timedelta(days=14)
    await db.execute(
        """
        UPDATE users
        SET subscription_tier = 'premium',
            trial_ends_at = :trial_end
        WHERE id = :user_id
          AND subscription_tier = 'free'
          AND trial_ends_at IS NULL
        """,
        {"user_id": user_id, "trial_end": trial_end},
    )


async def check_expired_trials() -> None:
    """
    Scheduled job (run daily via cron or APScheduler) to downgrade users
    whose trials have expired without converting to a paid subscription.
    """
    await db.execute(
        """
        UPDATE users
        SET subscription_tier = 'free',
            trial_ends_at = NULL
        WHERE subscription_tier = 'premium'
          AND trial_ends_at IS NOT NULL
          AND trial_ends_at < NOW()
          AND stripe_subscription_id IS NULL
        """
    )
```

### Trial UX

- Display a banner: "You have X days left in your free trial."
- At day 12 and day 14, send email reminders with a CTA to subscribe.
- After expiry, show a "Your trial has ended" modal with upgrade options.

---

## 10. Architecture Diagram

```
+-------------------+         +---------------------+        +------------------+
|                   |  POST   |                     | create |                  |
|   React Frontend  |-------->|   FastAPI Backend    |------->|  Stripe API      |
|                   |  /api/  |                     |session |                  |
|   @stripe/        |  billing|   stripe Python SDK |        |  Checkout        |
|   stripe-js       |         |                     |        |  Customer Portal |
|                   |         |                     |        |  Webhooks        |
+--------+----------+         +----------+----------+        +--------+---------+
         |                               |                            |
         |  redirect to                  |  webhook POST              |
         |  Stripe Checkout              |  /api/v1/webhooks/stripe   |
         |                               |                            |
         v                               v                            |
+-------------------+         +---------------------+                 |
|                   |         |                     |                 |
|  Stripe Checkout  |         |  Webhook Handler    |<----------------+
|  (hosted page)    |         |                     |  checkout.session.completed
|                   |         |  1. Verify sig      |  invoice.paid
|  Payment form     |         |  2. Parse event     |  invoice.payment_failed
|  Apple/Google Pay |         |  3. Update user     |  customer.subscription.deleted
|  3D Secure        |         |  4. Return 200      |  customer.subscription.updated
|                   |         |                     |
+--------+----------+         +----------+----------+
         |                               |
         |  redirect back                |  UPDATE users SET
         |  /billing/success             |  subscription_tier = ...
         |                               |
         v                               v
+-------------------+         +---------------------+
|                   |         |                     |
|  Success Page     |         |  PostgreSQL          |
|  (confirm tier)   |         |                     |
|                   |         |  users table         |
+-------------------+         |  - subscription_tier |
                              |  - stripe_customer_id|
                              |  - stripe_sub_id     |
                              |  - trial_ends_at     |
                              |                     |
                              |  processed_stripe_  |
                              |  events table        |
                              +---------------------+


Checkout Flow (sequence):

  User          Frontend        Backend           Stripe           Database
   |               |               |                |                 |
   |--click------->|               |                |                 |
   |               |--POST-------->|                |                 |
   |               |  /checkout-   |--create------->|                 |
   |               |   session     |  session       |                 |
   |               |               |<--session.url--|                 |
   |               |<--url---------|                |                 |
   |<--redirect----|               |                |                 |
   |               |               |                |                 |
   |--pay on Stripe Checkout------>|                |                 |
   |               |               |                |                 |
   |<--redirect back to success----|                |                 |
   |               |               |<--webhook------|                 |
   |               |               |  (signed)      |                 |
   |               |               |--verify sig--->|                 |
   |               |               |--UPDATE------->|---------------->|
   |               |               |  user tier     |                 |
   |               |               |--200 OK------->|                 |
   |               |               |                |                 |
```

---

## 11. Tech Stack

### Backend

| Component              | Technology                                       |
|------------------------|--------------------------------------------------|
| Framework              | FastAPI (existing)                                |
| Stripe SDK             | `stripe` Python package (>=7.0.0)                |
| Database               | PostgreSQL (existing)                             |
| ORM / Query Builder    | SQLAlchemy / raw SQL (match existing patterns)    |
| Task Scheduling        | APScheduler or Celery (for trial expiry checks)   |
| Email (notifications)  | Existing email service (for payment failure, trial reminders) |

### Frontend

| Component              | Technology                                       |
|------------------------|--------------------------------------------------|
| Framework              | React (existing)                                 |
| Stripe SDK             | `@stripe/stripe-js` (for redirect-based Checkout)|
| HTTP Client            | Axios or fetch (match existing patterns)         |

### Infrastructure

| Component              | Technology                                       |
|------------------------|--------------------------------------------------|
| Hosting                | Render (existing)                                |
| Secrets Management     | Environment variables via Render Dashboard       |
| Webhook Endpoint       | Publicly accessible HTTPS endpoint               |

### Environment Variables (New)

```bash
# Stripe keys
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx

# Stripe price IDs
STRIPE_PRICE_PREMIUM_MONTHLY=price_xxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_PREMIUM_ANNUAL=price_xxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_LIFETIME=price_xxxxxxxxxxxxxxxxxxxx
```

---

## 12. Implementation Plan

### Phase 1: Foundation (Effort: ~3 days)

| Task                                                    | Estimate |
|---------------------------------------------------------|----------|
| Create Stripe Australia account; configure ABN and GST  | 0.5 day  |
| Create Products and Prices in Stripe Dashboard          | 0.5 day  |
| Add `stripe` to `requirements.txt`                      | 0.1 day  |
| Add Stripe env vars to Render config                    | 0.1 day  |
| Database migration: add billing columns to `users`      | 0.5 day  |
| Database migration: create `processed_stripe_events`    | 0.3 day  |
| Create `BillingService` with tier upgrade/downgrade logic| 1.0 day |

### Phase 2: Checkout and Webhooks (Effort: ~4 days)

| Task                                                    | Estimate |
|---------------------------------------------------------|----------|
| Implement `/billing/checkout-session` endpoint          | 0.5 day  |
| Implement `/webhooks/stripe` endpoint with all handlers | 1.5 days |
| Implement idempotency layer for webhooks                | 0.5 day  |
| Implement `/billing/portal-session` endpoint            | 0.5 day  |
| Configure Stripe Customer Portal in Dashboard           | 0.5 day  |
| Stripe CLI local testing and verification               | 0.5 day  |

### Phase 3: Frontend (Effort: ~3 days)

| Task                                                    | Estimate |
|---------------------------------------------------------|----------|
| Pricing page with three plan cards                      | 1.0 day  |
| Upgrade button component with Checkout redirect         | 0.5 day  |
| Success and cancellation pages                          | 0.5 day  |
| Billing settings page with Portal link                  | 0.5 day  |
| Trial banner and expiry modal                           | 0.5 day  |

### Phase 4: Trial and Waitlist (Effort: ~2 days)

| Task                                                    | Estimate |
|---------------------------------------------------------|----------|
| Free trial start/check/expire logic                     | 0.5 day  |
| Scheduled job for trial expiry                          | 0.5 day  |
| Trial reminder emails (day 12 and day 14)               | 0.5 day  |
| Waitlist invite_type parameter and routing              | 0.5 day  |

### Phase 5: Testing and Launch (Effort: ~3 days)

| Task                                                    | Estimate |
|---------------------------------------------------------|----------|
| Unit tests for BillingService                           | 0.5 day  |
| Integration tests with Stripe test mode                 | 1.0 day  |
| End-to-end test: full checkout + webhook cycle          | 0.5 day  |
| Edge cases: duplicate webhooks, failed payments, refunds| 0.5 day  |
| Production deployment and smoke test                    | 0.5 day  |

### Total Estimated Effort: ~15 days (3 calendar weeks)

---

## 13. Security Considerations

1. **Webhook Signature Verification:** Every webhook request must be verified
   using `stripe.Webhook.construct_event()` with the signing secret. Never
   process unverified payloads.

2. **Secret Key Protection:** The `STRIPE_SECRET_KEY` must never be exposed to
   the frontend or committed to version control. It is stored exclusively in
   environment variables on the server.

3. **Publishable Key Only on Frontend:** The frontend may only use the
   `STRIPE_PUBLISHABLE_KEY` (`pk_live_*` or `pk_test_*`).

4. **HTTPS Only:** All Stripe API calls and webhook endpoints must use HTTPS.
   Render provides this by default.

5. **Idempotent Webhook Processing:** Prevents double-upgrades or
   double-charges from duplicate webhook deliveries.

6. **CSRF Protection:** The checkout session creation endpoint is protected by
   the existing authentication middleware and CSRF token validation.

7. **Rate Limiting:** Apply rate limiting to the checkout session creation
   endpoint to prevent abuse (e.g. 10 requests per minute per user).

8. **Audit Logging:** Log all tier changes with timestamps, source events, and
   Stripe IDs for debugging and compliance.

---

## 14. Open Questions

| #  | Question                                                              | Status   |
|----|-----------------------------------------------------------------------|----------|
| 1  | Should lifetime premium have a cap (e.g. first 200 users)?           | Pending  |
| 2  | Do we offer refunds, and if so, what is the policy?                  | Pending  |
| 3  | Should annual subscribers be able to switch to monthly mid-cycle?    | Pending  |
| 4  | Do we need Stripe Tax for international customers, or AUD-only?     | Pending  |
| 5  | What email service will be used for payment failure notifications?   | Pending  |
| 6  | Should the free trial be offered to all new users or only invitees?  | Pending  |
| 7  | Is there a grace period for failed payments before downgrade?        | 7 days (proposed) |
| 8  | Do existing lifetime_premium users need to be migrated in Stripe?   | Pending  |

---

*End of document.*
