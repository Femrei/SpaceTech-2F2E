import { InfoIcon } from "lucide-react"

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

// Terimin yanında küçük bir (i) simgesi gösterir; üzerine gelince/dokununca
// sözlükteki açıklama baloncukta çıkar. Açıklama yoksa hiçbir şey çizmez.
export function InfoTip({ text }: { text?: string }) {
  if (!text) return null
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={text}
          className="inline-flex size-4 items-center justify-center text-muted-foreground hover:text-foreground"
        >
          <InfoIcon className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">{text}</TooltipContent>
    </Tooltip>
  )
}
