'use client'

import { useEffect, useRef } from 'react'

type Point = readonly [number, number]
const glyphs: readonly (readonly Point[])[] = [
  [[30,42],[64,42],[136,239],[208,42],[242,42],[152,280],[121,280]],
  [[230,280],[318,42],[350,42],[438,280],[404,280],[381,217],[287,217],[264,280]],
  [[298,188],[370,188],[334,89]],
  [[448,280],[536,42],[568,42],[656,280],[622,280],[599,217],[505,217],[482,280]],
  [[516,188],[588,188],[552,89]],
  [[697,280],[697,42],[729,42],[864,224],[864,42],[895,42],[895,280],[864,280],[728,98],[728,280]],
  [[951,42],[983,42],[983,280],[951,280]],
]

const outlines = glyphs.map(glyph => glyph.flatMap(([x,y], index) => {
  const [nextX,nextY] = glyph[(index + 1) % glyph.length]
  const segments = Math.ceil(Math.hypot(nextX - x, nextY - y) / 12)
  return Array.from({length: segments}, (_, step) => {
    const t = step / segments
    return [x + (nextX - x) * t, y + (nextY - y) * t] as const
  })
}))

function path(points: readonly Point[]) {
  return points.map(([x,y], index) => `${index ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ') + ' Z'
}

export function FooterMark() {
  const mark = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const svg = mark.current
    if (!svg) return
    const paths = svg.querySelectorAll('path')
    const nodes = svg.querySelectorAll('circle')
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    let frame = 0
    let previous = 0
    let strength = 0
    let target = 0
    let x = 0, y = 0, aimX = 0, aimY = 0

    function draw() {
      const project = ([px,py]: Point): Point => {
        const dx = px - x, dy = py - y
        const weight = Math.exp(-(dx * dx + dy * dy) / 10500) * strength * .62
        return [px + dx * weight, py + dy * weight]
      }
      outlines.forEach((outline, index) => paths[index].setAttribute('d',path(outline.map(project))))
      glyphs.flat().forEach((point, index) => {
        const [px,py] = project(point)
        nodes[index].setAttribute('cx',px.toFixed(2))
        nodes[index].setAttribute('cy',py.toFixed(2))
      })
    }

    function tick(now: number) {
      const delta = previous ? Math.min(now - previous, 45) : 16
      previous = now
      const blend = 1 - Math.exp(-delta / 85)
      strength += (target - strength) * blend
      x += (aimX - x) * blend
      y += (aimY - y) * blend
      if (Math.abs(target - strength) + Math.abs(aimX - x) + Math.abs(aimY - y) < .01) {
        strength = target
        x = aimX
        y = aimY
        frame = 0
        previous = 0
      } else {
        frame = requestAnimationFrame(tick)
      }
      draw()
    }

    function move(event: PointerEvent) {
      if (reduced.matches || event.pointerType === 'touch') return
      const box = svg?.getBoundingClientRect()
      if (!box?.width || !box.height) return
      aimX = (event.clientX - box.left) * 1014 / box.width
      aimY = (event.clientY - box.top) * 322 / box.height
      if (strength === 0) { x = aimX; y = aimY }
      target = 1
      if (!frame) frame = requestAnimationFrame(tick)
    }

    function leave() {
      target = 0
      if (strength && !frame) frame = requestAnimationFrame(tick)
    }

    function reset() {
      cancelAnimationFrame(frame)
      frame = previous = strength = target = 0
      draw()
    }

    svg.addEventListener('pointermove',move)
    svg.addEventListener('pointerleave',leave)
    svg.addEventListener('pointercancel',leave)
    reduced.addEventListener('change',reset)
    return () => {
      svg.removeEventListener('pointermove',move)
      svg.removeEventListener('pointerleave',leave)
      svg.removeEventListener('pointercancel',leave)
      reduced.removeEventListener('change',reset)
      cancelAnimationFrame(frame)
    }
  },[])

  return (
    <svg ref={mark} className="footer-mark" viewBox="0 0 1014 322" role="img" aria-label="VAANI">
      <rect width="1014" height="322" fill="transparent" />
      <g fill="none" stroke="currentColor" strokeWidth="1.15" strokeLinejoin="round">
        {outlines.map((outline,index) => <path key={index} d={path(outline)} />)}
      </g>
      <g fill="currentColor">
        {glyphs.flat().map(([x,y],index) => <circle key={index} cx={x} cy={y} r="2.2" />)}
      </g>
    </svg>
  )
}
