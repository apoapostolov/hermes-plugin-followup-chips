import { describe, it, expect, beforeEach } from 'vitest'
import { JSDOM } from 'jsdom'
import { act } from 'react'
import { createRoot } from 'react-dom/client'

import { host, lastSubmission, resetSubmissionLog, makeCtx } from './sdk-stub.js'

// The REAL plugin, unmodified - the vite alias resolves its SDK import to the stub.
const pluginModule = await import('../plugin.js')
const plugin = pluginModule.default

function newSession() {
  const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/' })
  global.document = dom.window.document
  global.window = dom.window
  const rootInstance = createRoot(dom.window.document.getElementById('root'))
  return { dom, rootInstance }
}

function renderBlock(attrs, source) {
  const ctx = makeCtx()
  plugin.register(ctx)
  const contrib = ctx.registered[0]
  return contrib.data.render({ attrs, source, sessionId: 'sess-1' })
}

function mount(el, s) {
  act(() => {
    s.rootInstance.render(el)
  })
  return s.dom.window.document.getElementById('root')
}

/** The AnswerBlock send button: never a chip (chips are never disabled). */
function sendBtnIn(root) {
  return Array.from(root.querySelectorAll('button')).find((b) => !b.disabled && !b.className.includes('fu-chip'))
}

function click(s, el) {
  act(() => {
    el.dispatchEvent(new s.dom.window.MouseEvent('click', { bubbles: true }))
  })
}

beforeEach(() => {
  resetSubmissionLog()
})

describe('plain chips (no kind)', () => {
  it('renders one chip per qN and clicking submits that question', () => {
    const s = newSession()
    const root = mount(renderBlock({ q1: 'Ship it?', q2: 'Add tests?' }, 'src'), s)
    const chips = Array.from(root.querySelectorAll('button')).filter((b) => b.className.includes('fu-chip'))
    expect(chips.length).toBe(2)
    expect(chips[0].textContent).toContain('Ship it?')
    click(s, chips[0])
    expect(lastSubmission().text).toBe('Ship it?')
  })

  it('falls back to plain mode on unknown kind: no checkboxes', () => {
    const s = newSession()
    const root = mount(renderBlock({ kind: 'wat', q1: 'A' }, 'src'), s)
    expect(root.querySelectorAll('input[type=checkbox]').length).toBe(0)
  })

  it('accepts an uppercase kind VALUE (keys arrive pre-lowercased from the parser)', () => {
    const s = newSession()
    const root = mount(renderBlock({ kind: 'ANSWER', q1: 'A', q2: 'B' }, 'src'), s)
    expect(root.querySelectorAll('input[type=checkbox]').length).toBe(2)
  })
})

describe('kind="multi"', () => {
  it('composes bare numbered items for checked rows without text', () => {
    const s = newSession()
    const root = mount(renderBlock({ kind: 'multi', q1: 'Alpha', q2: 'Beta' }, 'src'), s)
    const boxes = root.querySelectorAll('input[type=checkbox]')
    expect(boxes.length).toBe(2)
    act(() => {
      boxes[1].click()
    })
    const btn = sendBtnIn(root)
    expect(btn).toBeTruthy()
    click(s, btn)
    expect(lastSubmission().text).toBe('2. Beta')
  })
})

describe('kind="answer"', () => {
  it('composes numbered item:answer lines; typing auto-picks the row', () => {
    const s = newSession()
    const root = mount(renderBlock({ kind: 'answer', q1: 'Deploy?', q2: 'Tag?' }, 'src'), s)
    const texts = root.querySelectorAll('input[type=text]')
    expect(texts.length).toBe(2)
    expect(sendBtnIn(root)).toBeUndefined() // nothing picked yet
    const input = texts[0]
    act(() => {
      const setter = Object.getOwnPropertyDescriptor(s.dom.window.HTMLInputElement.prototype, 'value').set
      setter.call(input, 'yes, at 16:00')
      input.dispatchEvent(new s.dom.window.Event('input', { bubbles: true }))
      input.dispatchEvent(new s.dom.window.FocusEvent('focusin', { bubbles: true }))
    })
    const btn = sendBtnIn(root)
    expect(btn).toBeTruthy()
    click(s, btn)
    expect(lastSubmission().text).toBe('1. Deploy?: yes, at 16:00')
  })
})

describe('host contract', () => {
  it('composer.submit returns true and records the text', () => {
    expect(host.composer.submit('sess-1', 'hello')).toBe(true)
    expect(lastSubmission().text).toBe('hello')
  })
})
