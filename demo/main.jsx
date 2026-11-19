// Playground: renders the REAL plugin.js against the SDK stub, one block per
// variant. The stub's composer log is the source of truth for what would be
// sent — no prop mutation, one React root, created once.
import { useState, useEffect, createElement as h } from 'react'
import { createRoot } from 'react-dom/client'

import plugin from '../plugin.js'
import { lastSubmission } from '../test/sdk-stub.js'

// Register once; the plugin pushes its transcript-directive contribution here.
const contributions = []
plugin.register({
  onEvent() {},
  register(c) {
    contributions.push(c)
  },
  storage: { get: () => ({}), set: () => {} },
})
const renderDirective = contributions[0].data.render

const variants = [
  ['Default chips (one click sends)', { q1: 'Ship this?', q2: 'Add tests first?', q3: 'Write a demo?' }],
  ['title label', { title: 'Next steps', q1: 'Deploy to staging', q2: 'Open a PR' }],
  ['free-text row (other)', { q1: 'Keep the fork?', other: 'true', otherlabel: 'Something else…' }],
  ['kind="multi" — select several', { kind: 'multi', q1: 'Refactor the parser', q2: 'Bump the pin', q3: 'Leave it' }],
  ['kind="answer" — reply per item', { kind: 'answer', title: 'Concretely', q1: 'Deploy at 16:00?', q2: 'Tag v1.3.0?' }],
]

function App() {
  const [log, setLog] = useState('— nothing yet —')
  useEffect(function subscribe() {
    const timer = setInterval(function () {
      const last = lastSubmission()
      setLog(last && last.text ? last.text : '— nothing yet —')
    }, 300)
    return function () {
      clearInterval(timer)
    }
  }, [])

  const blocks = variants.map(function ([label, attrs]) {
    return h('section', { key: label }, [
      h('h2', { key: 'h' }, label),
      renderDirective({ attrs, source: label, sessionId: 'demo' }),
    ])
  })

  return h('div', null, [
    h('h1', { key: 'title' }, 'followup-chips playground'),
    h('p', { key: 'intro' }, 'Click anything. What the composer receives is logged below. This is the real plugin.js — Hermes not required.'),
    ...blocks,
    h('h2', { key: 'logH' }, 'Composer received'),
    // Text only via React — no raw HTML, no injection surface.
    h('pre', { key: 'log', className: 'sent' }, log),
  ])
}

createRoot(document.getElementById('root')).render(h(App))
