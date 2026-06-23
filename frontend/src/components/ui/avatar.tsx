import * as React from "react"
import { cn } from "@/lib/utils"

const Avatar = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { src?: string; fallback?: string }>(
  ({ className, src, fallback, ...props }, ref) => (
    <div ref={ref} className={cn("relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full", className)} {...props}>
      {src ? (
        <img src={src} alt="" className="aspect-square h-full w-full" />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-muted text-sm font-medium text-muted-foreground">
          {fallback || "?"}
        </div>
      )}
    </div>
  ),
)
Avatar.displayName = "Avatar"
export { Avatar }
