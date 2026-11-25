// @ts-nocheck: this function runs in the browser (see below), so it is written as plain JavaScript.
/**
 * The Copy button on a prompt card. A page writes a prompt for the reader to paste into their
 * chat as a fenced block with the language `prompt` (markdown.ts makes it a `.prompt` card). A
 * click on its button copies the prompt's text and says "Copied" for two seconds; where the
 * clipboard can't be reached (an old browser, a file:// page in some browsers) it selects the
 * text so the reader can copy it by hand, and says "Selected".
 *
 * Like lightbox.ts, the explorer embeds this function's source and the static pages put it in a
 * script on any page with a prompt, so it uses nothing but its argument and the language: no
 * imports, no closures over this module, no template literals.
 */
export const promptCopy = (doc) => {
  if (doc.__promptCopy) return
  doc.__promptCopy = true
  doc.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.prompt-copy')
    if (!b) return
    const code = b.closest('.prompt').querySelector('code')
    const say = (t) => { b.textContent = t; setTimeout(() => { b.textContent = 'Copy' }, 2000) }
    const select = () => {
      const r = doc.createRange(); r.selectNodeContents(code)
      const s = doc.defaultView.getSelection(); s.removeAllRanges(); s.addRange(r)
      say('Selected')
    }
    const nav = doc.defaultView.navigator
    if (nav.clipboard && nav.clipboard.writeText) nav.clipboard.writeText(code.textContent).then(() => say('Copied'), select)
    else select()
  })
}
