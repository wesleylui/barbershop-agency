# Build Recipe — reusable patterns

Concrete, copy-adaptable patterns for a single-file 3D landing page. Adapt palette, type, and the signature object to the subject; don't ship these verbatim.

## Table of contents
1. Page skeleton + CDN scripts
2. Design tokens (CSS variables)
3. 3D signature object (Three.js)
4. Scroll reveals + parallax (GSAP)
5. Card 3D tilt + cursor glow
6. Floating-review marquee
7. Animated grain
8. Reduced-motion + accessibility

---

## 1. Page skeleton + CDN scripts

Classic (non-module) builds so the file runs on double-click:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
```

Detect reduced motion once and branch every animation on it:
```js
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
```

## 2. Design tokens

Put every color and font in `:root` so the whole palette is swappable from one place. Use a `clamp()` type scale. Example structure (swap values per subject):
```css
:root{
  --bg:#14110F; --accent:#C9A35B; --accent-2:#7A2E2A; --fg:#EDE6D8; --fg-dim:#A89F8E;
  --display:"Fraunces",serif; --body:"Archivo",system-ui,sans-serif;
  --pad-x:clamp(1.25rem,5vw,6rem); --maxw:1240px;
}
```

## 3. 3D signature object

Renderer + camera + warm-key/cool-rim lighting; cap pixel ratio; pause on hidden tab.
```js
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
scene.add(new THREE.AmbientLight(0xffffff,0.55));
const key = new THREE.DirectionalLight(0xffe6bf,1.5); key.position.set(4,6,6); scene.add(key);
const rim = new THREE.DirectionalLight(0x6f8bff,0.6); rim.position.set(-6,-2,-4); scene.add(rim);
```

Barber-pole pattern (a cylinder with a diagonal red/white/navy CanvasTexture whose `offset.y` animates so stripes climb; brass caps + domes). Cursor parallax with damping; scroll drives scale/position:
```js
if(!reduceMotion){ tex.offset.y -= 0.0016; pointer.x += (pointer.tx-pointer.x)*0.06; }
group.rotation.y = performance.now()*0.00025 + pointer.x*0.5;
group.position.y = -scrollProg*2.4;
```
Swap the geometry+texture for a different subject (record, bottle, dumbbell, etc.). If the brief needs a realistic figure, load a supplied GLB with `GLTFLoader` — do not sculpt a human from primitives.

## 4. Scroll reveals + parallax (GSAP)

Base state `.reveal{opacity:0;transform:translateY(28px)}`, then:
```js
gsap.registerPlugin(ScrollTrigger);
if(!reduceMotion){
  gsap.utils.toArray('.reveal').forEach(el=>gsap.to(el,{opacity:1,y:0,duration:0.9,ease:'power3.out',
    scrollTrigger:{trigger:el,start:'top 85%'}}));
} else { gsap.set('.reveal',{opacity:1,y:0}); }
```
Stagger grids with `stagger:0.08` on the container's children.

## 5. Card 3D tilt + cursor glow

`transform-style:preserve-3d` on the card; a radial-gradient `.glow` child that follows the pointer; tilt from pointer position:
```js
card.addEventListener('pointermove',e=>{
  const r=card.getBoundingClientRect();
  const px=(e.clientX-r.left)/r.width, py=(e.clientY-r.top)/r.height;
  card.style.transform=`perspective(800px) rotateX(${(0.5-py)*10}deg) rotateY(${(px-0.5)*12}deg) translateZ(6px)`;
  glow.style.left=(e.clientX-r.left)+'px'; glow.style.top=(e.clientY-r.top)+'px';
});
card.addEventListener('pointerleave',()=>card.style.transform='');
```
Guard the whole block behind `if(!reduceMotion)`.

## 6. Floating-review marquee

Two rows, opposite directions, pure-CSS transform loop, pause on hover, edge fades. Each track holds the card set **twice** (a `.dup aria-hidden` copy) so `translateX(-50%)` seams seamlessly.
```css
.track.left{animation:scroll-left 46s linear infinite}
.track.right{animation:scroll-right 54s linear infinite}
.marquee:hover .track{animation-play-state:paused}
@keyframes scroll-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes scroll-right{from{transform:translateX(-50%)}to{transform:translateX(0)}}
```
Edge fades via `.marquee::before/::after` gradients matching the section bg. Reduced-motion: `animation:none`, wrap into a centered grid, and `display:none` the `.dup` cards so it isn't a wall of repeats. Duration is fixed in seconds — re-tune it if the card count changes.

## 7. Animated grain

A `<canvas>` filled with accent-tinted random alpha noise, redrawn every few frames; on reduced-motion draw once and stop.

## 8. Reduced-motion + accessibility checklist

- `.reveal{opacity:1!important;transform:none!important}` under the reduced-motion media query.
- Stop marquees, particles, tilt, grain when reduced.
- `a:focus-visible,.btn:focus-visible{outline:2px solid var(--accent);outline-offset:3px}`.
- Semantic landmarks (`header`,`nav`,`section`,`footer`), real heading order, `100svh` hero, responsive to ~320px.
