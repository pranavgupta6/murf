import * as React from 'react';
import { cn } from '@/lib/utils';
import { Mic, Sparkles } from 'lucide-react';

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
  const isHost = messageOrigin === 'remote';
  const isContestant = messageOrigin === 'local';

  return (
    <li
      title={title}
      data-lk-message-origin={messageOrigin}
      className={cn('group flex w-full flex-col gap-2', className)}
      {...props}
    >
      {/* Improv Host - Energetic Purple Style */}
      {isHost && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-purple-800 shadow-lg">
              <Sparkles className="h-4 w-4 text-purple-100" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-purple-300">Improv Host</span>
              <span className="font-mono text-xs text-purple-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
          </div>
          
          <div className="relative ml-10 max-w-[85%] rounded-xl border border-purple-200/20 bg-gradient-to-br from-purple-50 to-fuchsia-50 p-4 shadow-lg dark:from-purple-950/30 dark:to-fuchsia-900/30">
            <p className="text-base leading-relaxed text-purple-950 dark:text-purple-100">
              {message}
            </p>
          </div>
        </div>
      )}

      {/* Contestant - Bright Yellow/Orange Bubble */}
      {isContestant && (
        <div className="flex flex-col gap-1.5">
          <div className="ml-auto flex items-center gap-2">
            <div className="flex flex-col items-end">
              <span className="text-sm font-bold text-amber-300">You</span>
              <span className="font-mono text-xs text-amber-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg">
              <Mic className="h-4 w-4 text-amber-50" />
            </div>
          </div>
          
          <div className="ml-auto mr-10 max-w-[85%] rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 px-4 py-3 shadow-lg">
            <p className="text-base leading-relaxed text-white">
              {message}
            </p>
          </div>
        </div>
      )}
    </li>
  );
};
