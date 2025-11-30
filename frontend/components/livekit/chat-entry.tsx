import * as React from 'react';
import { cn } from '@/lib/utils';
import { ShoppingBag, User } from 'lucide-react';

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
  const isAssistant = messageOrigin === 'remote';
  const isCustomer = messageOrigin === 'local';

  return (
    <li
      title={title}
      data-lk-message-origin={messageOrigin}
      className={cn('group flex w-full flex-col gap-2', className)}
      {...props}
    >
      {/* Shopping Assistant - Clean Professional Style */}
      {isAssistant && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-blue-800 shadow-lg">
              <ShoppingBag className="h-4 w-4 text-blue-100" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-blue-300">Shopping Assistant</span>
              <span className="font-mono text-xs text-blue-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
          </div>
          
          <div className="relative ml-10 max-w-[85%] rounded-xl border border-blue-200/20 bg-gradient-to-br from-blue-50 to-slate-50 p-4 shadow-lg dark:from-blue-950/30 dark:to-slate-900/30">
            <p className="text-base leading-relaxed text-slate-800 dark:text-slate-100">
              {message}
            </p>
          </div>
        </div>
      )}

      {/* Customer - Modern Bubble */}
      {isCustomer && (
        <div className="flex flex-col gap-1.5">
          <div className="ml-auto flex items-center gap-2">
            <div className="flex flex-col items-end">
              <span className="text-sm font-bold text-emerald-300">You</span>
              <span className="font-mono text-xs text-emerald-400/60 opacity-0 transition-opacity ease-linear group-hover:opacity-100">
                {time.toLocaleTimeString(locale, { timeStyle: 'short' })}
              </span>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-600 to-emerald-800 shadow-lg">
              <User className="h-4 w-4 text-emerald-100" />
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
