/**
 * Stand-in for the app's `@hermes/plugin-sdk` module, so the plugin renders
 * and submits outside Hermes (tests + demo). Mirrors the real surface the
 * plugin uses: TRANSCRIPT_DIRECTIVE_AREA, host.composer.submit, host.notify,
 * ctx.onEvent and ctx.storage (sync get/set).
 */
export const TRANSCRIPT_DIRECTIVE_AREA = 'transcript.directives'

const submissions = []

export const host = {
  composer: {
    /** Mirrors the real contract: returns true when accepted. */
    submit: function (sessionId, text) {
      submissions.push({ sessionId, text, at: Date.now() })
      return true
    },
  },
  notify: function (msg) {
    submissions.push({ notify: msg })
  },
}

/** Reads like the real one: submissions[submissions.length - 1]. */
export function lastSubmission() {
  return submissions.length ? submissions[submissions.length - 1] : null
}

export function resetSubmissionLog() {
  submissions.length = 0
}

/** The plugin registers itself against a ctx like this in tests/demo. */
export function makeCtx() {
  const handlers = {}
  const store = new Map()
  const registered = []
  return {
    onEvent: function (name, fn) {
      handlers[name] = handlers[name] || []
      handlers[name].push(fn)
    },
    emitEvent: function (name, payload) {
      ;(handlers[name] || []).forEach(function (fn) {
        fn(payload)
      })
    },
    register: function (contrib) {
      registered.push(contrib)
    },
    registered,
    storage: {
      get: function (key, fallback) {
        return store.has(key) ? store.get(key) : fallback
      },
      set: function (key, value) {
        store.set(key, value)
      },
    },
    _store: store,
  }
}
