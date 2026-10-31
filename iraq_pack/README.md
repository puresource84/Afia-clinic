# Afia Clinic — Iraq pack

Modules for Iraqi clinics only. These are **not** part of the Odoo App Store
product and are never published to the store.

| Module | Purpose |
| --- | --- |
| `itcs_license_manager` | ITCS licence enforcement and plan capacity (dentist/patient limits) |
| `payment_paytabs` | PayTabs payment provider |
| `payment_zaincash` | ZainCash payment provider |

`itcs_license_manager` depends on `afia_dental_core`; install the global
product first, then this pack. The two payment modules depend only on Odoo's
own `payment` module and are independent of Afia.

Excluded deliberately: `dental_pricing_iq` — its own manifest marks it
DEPRECATED (2026-07-17) and `installable: False`. It is seed pricing for a
hosted multi-tenant product that was dropped in favour of self-hosted, and it
depends on `bytekol_saas_subscription`, which was removed. It is not in this
pack and not in the product.
