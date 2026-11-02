import * as React from "react"

/**
 * A label wrapping its control. The explicit aria-label keeps a select's option text out of
 * its accessible name, which a wrapping label would otherwise include.
 */
export function Field({ label, children, hint }: { label: string; children: React.ReactElement<{ "aria-label"?: string }>; hint?: string }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium">{label}</span>
      {React.cloneElement(children, { "aria-label": label })}
      {hint && <span className="block text-xs text-muted-foreground">{hint}</span>}
    </label>
  )
}
