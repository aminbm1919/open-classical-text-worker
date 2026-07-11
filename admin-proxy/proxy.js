// chunking-admin — thin proxy worker (NOT the main worker).
//
// WHY THIS EXISTS: ChatGPT will not accept two separate Custom-GPT Actions that
// share the same domain, and our 52 operations cannot fit in one Action (30-op
// cap). So the admin Action needs a SECOND distinct hostname. Cloudflare gives
// exactly one free workers.dev subdomain per worker, so a second worker is the
// free way to get a second hostname:
//     routine Action -> https://chunking.YOUR-SUBDOMAIN.workers.dev        (main worker)
//     admin   Action -> https://chunking-admin.YOUR-SUBDOMAIN.workers.dev  (this proxy)
//
// WHAT IT DOES: forwards every request — method, headers (incl. X-Admin-Token),
// body, and path — straight to the main `chunking` worker through a Service
// Binding (direct worker-to-worker; no public internet round-trip, ~0 added
// latency). ALL real logic, routing, and resource bindings (D1/R2/Vectorize/AI)
// live in the main worker. This file has no bindings of its own and never needs
// to change when worker.js changes.
export default {
  async fetch(request, env) {
    return env.MAIN.fetch(request);
  }
};
