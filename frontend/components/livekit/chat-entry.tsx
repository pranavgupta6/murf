import * as React from 'react';
import { cn } from '@/lib/utils';
import { Scroll, Swords } from 'lucide-react';

export interface ChatEntryProps extends React.HTMLAttributes<HTMLLIElement> {
  /** The locale to use for the timestamp. */
  locale: string;
  /** The timestamp of the message. */
  timestamp: number;
  /** The message to display. */
  message: string;
  /** The origin of the message. */
  messageOrigin: 'local' | 'remote';
  /** The sender's name. */
  name?: string;
  /** Whether the message has been edited. */
  hasBeenEdited?: boolean;
}

export const ChatEntry = ({
  name,
  locale,
  timestamp,
  message,
  messageOrigin,
  hasBeenEdited = false,
  className,
  ...props
}: ChatEntryProps) => {
  const time = new Date(timestamp);
  const title = time.toLocaleTimeString(locale, { timeStyle: 'full' });
  const isGM = messageOrigin === 'remote';
  const isPlayer = messageOrigin === 'local';

  return (
    <li
      title={title}
      data-lk-message-origin={messageOrigin}
      className={cn('group flex w-full flex-col gap-2', className)}
      {...props}
    >
      {/* GM Narration - Parchment Style */}
      {isGM && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-amber-700 to-amber-900 shadow-lg">
              <Scroll className="h-4 w-4 text-amber-100" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-amber-200">Game Master</span>
              <span className="font-mono text-xs text-amber-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
          </div>
          
          <div className="gm-parchment relative ml-10 max-w-[85%] rounded-lg border-2 border-amber-900/30 bg-gradient-to-br from-amber-50 to-amber-100 p-4 shadow-xl dark:from-amber-950/40 dark:to-amber-900/30">
            {/* Decorative corners */}
            <div className="pointer-events-none absolute -left-1 -top-1 h-3 w-3 border-l-2 border-t-2 border-amber-700" />
            <div className="pointer-events-none absolute -right-1 -top-1 h-3 w-3 border-r-2 border-t-2 border-amber-700" />
            <div className="pointer-events-none absolute -bottom-1 -left-1 h-3 w-3 border-b-2 border-l-2 border-amber-700" />
            <div className="pointer-events-none absolute -bottom-1 -right-1 h-3 w-3 border-b-2 border-r-2 border-amber-700" />
            
            <p className="font-serif text-base leading-relaxed text-amber-950 dark:text-amber-100">
              {message}
            </p>
          </div>
        </div>
      )}

      {/* Player Speech - Modern Bubble */}
      {isPlayer && (
        <div className="flex flex-col gap-1.5">
          <div className="ml-auto flex items-center gap-2">
            <div className="flex flex-col items-end">
              <span className="text-sm font-bold text-emerald-300">You</span>
              <span className="font-mono text-xs text-emerald-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-600 to-emerald-800 shadow-lg">
              <Swords className="h-4 w-4 text-emerald-100" />
            </div>
          </div>
          
          <div className="ml-auto mr-10 max-w-[85%] rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-700 px-4 py-3 shadow-lg">
            <p className="text-base leading-relaxed text-white">
              {message}
            </p>
          </div>
        </div>
      )}
    </li>
  );
};
