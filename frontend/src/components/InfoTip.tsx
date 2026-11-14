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
          className="-m-1 inline-flex size-6 items-center justify-center rounded-full text-muted-foreground hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring"
        >
          <InfoIcon className="size-3.5" />
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">{text}</TooltipContent>
    </Tooltip>
  )
}
