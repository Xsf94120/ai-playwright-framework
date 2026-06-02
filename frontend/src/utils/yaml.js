import yaml from 'js-yaml'

export function parseYaml(text) {
  if (!text || !text.trim()) return null
  return yaml.load(text)
}

export function dumpYaml(obj) {
  if (obj === null || obj === undefined) return ''
  return yaml.dump(obj, {
    indent: 2,
    lineWidth: 100,
    noRefs: true,
    sortKeys: false,
  })
}

export function safeParse(text) {
  try {
    return { value: parseYaml(text), error: null }
  } catch (e) {
    return { value: null, error: e.message }
  }
}
