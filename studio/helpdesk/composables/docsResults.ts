export type Hit = { title: string; is_converted?: boolean; [key: string]: any }

// Marked, escaped server text to plain lowercase text.
export function plainTitle(title: string): string {
  const text = title.replace(/<\/?mark>/g, '')
  const decoded = new DOMParser().parseFromString(text, 'text/html').documentElement.textContent
  return (decoded || '').trim().toLowerCase()
}

export function hasQueryWords(title: string, query: string): boolean {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  return words.every((word) => plainTitle(title).includes(word))
}

// An Article wins a same-title pair; a Converted Article does not count.
export function visibleDocs(articles: Hit[], docs: Hit[], query: string): Hit[] {
  const taken = new Set(articles.filter((a) => !a.is_converted).map((a) => plainTitle(a.title)))
  const kept = docs.filter((doc) => !taken.has(plainTitle(doc.title)))
  const full = kept.filter((doc) => hasQueryWords(doc.title, query))
  return [...full, ...kept.filter((doc) => !full.includes(doc))]
}
