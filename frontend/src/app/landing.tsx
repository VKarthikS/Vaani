'use client'

import { useEffect, useRef, useState } from 'react'
import { copy, languages, type Language } from './copy'

const sections = ['idea', 'services', 'process', 'demo']
const languageOptions = ['en', 'te', 'hi'] as const

function VoiceMark() {
  return (
    <svg className="voice-mark" aria-hidden="true" viewBox="0 0 490 560" fill="none">
      {Array.from({ length: 36 }, (_, index) => {
        const y = 27 + index * 14
        const span = Math.sin(index / 35 * Math.PI) * 135
        return <path key={index} d={`M ${145 - span} ${y} Q 225 ${y - span * .8} 285 ${y} T ${330 + span} ${y}`} stroke="currentColor" opacity={0.35 + span / 250} />
      })}
    </svg>
  )
}

export function Landing({ phoneNumber }: { phoneNumber?: string }) {
  const [language, setLanguage] = useState<Language>('en')
  const [menu, setMenu] = useState(false)
  const [scenario, setScenario] = useState(0)
  const dialog = useRef<HTMLDialogElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const words = copy[language]

  useEffect(() => { document.documentElement.lang = language }, [language])

  function closeMenu() {
    setMenu(false)
    toggle.current?.focus()
  }

  return (
    <div id="top" onKeyDown={event => { if (menu && event.key === 'Escape') closeMenu() }}>
      <a className="skip" href="#content">{words.skip}</a>
      <header className="site-header">
        <a href="#top" className="wordmark" aria-label="Vaani" onClick={() => setMenu(false)}>VAANI<span>.</span></a>
        <button className="menu-toggle" ref={toggle} type="button" aria-expanded={menu} aria-controls="navigation" onClick={() => setMenu(!menu)}>{words.menu}<span aria-hidden="true">{menu ? '−' : '+'}</span></button>
        <nav id="navigation" className={menu ? 'navigation open' : 'navigation'} aria-label={words.menu}>
          {sections.map((id, index) => <a key={id} href={`#${id}`} onClick={() => setMenu(false)}>{words.nav[index]}</a>)}
        </nav>
        <select aria-label={words.language} value={language} onChange={event => setLanguage(event.currentTarget.value as Language)}>
          {languageOptions.map(key => <option key={key} value={key} lang={key}>{languages[key]}</option>)}
        </select>
      </header>
      <main id="content" tabIndex={-1}>
        <section className="hero wrap" aria-labelledby="headline">
          <VoiceMark />
          <div className="hero-copy">
            <p className="eyebrow">VAANI / VOICE RECEPTIONIST</p>
            <h1 id="headline">{words.hero.map((line, index) => <span key={index}>{line}</span>)}</h1>
            <p className="hero-intro">{words.intro}</p>
          </div>
          <div className="hero-foot">
            <span>Homingo Hack Days · Hyderabad</span>
            <a href="#idea">{words.nav[0]} <span aria-hidden="true">↓</span></a>
          </div>
        </section>
        <section id="idea" className="editorial wrap">
          <p className="eyebrow">{words.nav[0]}</p>
          <div><h2>{words.philosophy}</h2><p className="lead">{words.belief}</p><p>{words.product}</p></div>
        </section>
        <section id="services" className="services wrap">
          <p className="eyebrow">{words.nav[1]}</p>
          <h2>{words.serviceTitle}</h2>
          {words.services.map(([name, description], index) => <article className="service" key={index}><span aria-hidden="true">0{index + 1}</span><h3>{name}</h3><p>{description}</p></article>)}
        </section>
        <section id="process" className="editorial process wrap">
          <p className="eyebrow">{words.nav[2]}</p>
          <div><h2>{words.processTitle}</h2><ol>{words.steps.map((step, index) => <li key={index}>{step}</li>)}</ol></div>
        </section>
        <section className="languages wrap" aria-labelledby="language-heading">
          <div className="scripts" aria-hidden="true"><span lang="te">తెలుగు</span><span lang="hi">हिन्दी</span><span lang="en">English</span></div>
          <div><h2 id="language-heading">{words.languageTitle}</h2><p>{words.languageBody}</p></div>
        </section>
        <section id="demo" className="editorial demo wrap">
          <p className="eyebrow">{words.nav[3]}</p>
          <div>
            <h2>{words.demoTitle}</h2>
            <div className="actions">
              <button type="button" className="action" onClick={() => dialog.current?.showModal()}>{words.cta} <span aria-hidden="true">↗</span></button>
              {phoneNumber && <a className="action" href={`tel:${phoneNumber}`}>{words.call}</a>}
            </div>
          </div>
        </section>
      </main>
      <footer className="footer wrap"><span className="wordmark">VAANI<span>.</span></span><span>Homingo Hack Days · <a href="https://github.com/vudigapranav/Vaani">GitHub</a></span><a href="#top">{words.top} ↑</a></footer>
      <dialog ref={dialog} aria-labelledby="sample-title">
        <form method="dialog"><button className="close" aria-label={words.close}>×</button></form>
        <h2 id="sample-title">{words.cta}</h2>
        <p>{words.demoNote}</p>
        <div className="scenarios">
          {words.services.map(([name], index) => <button key={index} aria-pressed={scenario === index} onClick={() => setScenario(index)}>{name}</button>)}
        </div>
        <dl aria-live="polite"><dt>{words.you}</dt><dd>{words.exchanges[scenario][0]}</dd><dt>Vaani</dt><dd>{words.exchanges[scenario][1]}</dd></dl>
      </dialog>
    </div>
  )
}
