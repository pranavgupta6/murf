import { Button } from '@/components/livekit/button';
import { useState } from 'react';

function WelcomeImage() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-fg0 mb-4 size-16"
    >
      <path
        d="M32 4C30.8954 4 30 4.89543 30 6V10C30 11.1046 30.8954 12 32 12C33.1046 12 34 11.1046 34 10V6C34 4.89543 33.1046 4 32 4ZM18.3432 10.3432C17.5621 9.5621 16.2931 9.5621 15.5121 10.3432C14.7311 11.1243 14.7311 12.3932 15.5121 13.1743L18.3432 16.0054C19.1243 16.7864 20.3932 16.7864 21.1743 16.0054C21.9553 15.2243 21.9553 13.9553 21.1743 13.1743L18.3432 10.3432ZM45.6568 10.3432C44.8758 9.5621 43.6068 9.5621 42.8258 10.3432L39.9946 13.1743C39.2136 13.9553 39.2136 15.2243 39.9946 16.0054C40.7757 16.7864 42.0447 16.7864 42.8258 16.0054L45.6568 13.1743C46.4379 12.3932 46.4379 11.1243 45.6568 10.3432ZM32 14C22.0589 14 14 22.0589 14 32C14 33.6497 14.2526 35.2382 14.7161 36.7308C15.6431 39.7159 17.4528 42.3509 19.9012 44.3027C20.0359 44.4092 20.1759 44.5099 20.3205 44.6046C21.3716 45.2971 22.5226 45.8333 23.7513 46.1859C23.9259 46.2373 24.1024 46.2854 24.2806 46.3304C25.7732 46.6892 27.3617 46.9048 29.0114 46.9048H35.0114C37.9966 46.9048 40.7815 45.7176 42.8682 43.7489C43.0128 43.6132 43.1528 43.4711 43.2878 43.3228C45.7362 40.7315 47.3046 37.2315 47.7161 33.3308C47.8526 32.2382 48 30.9497 48 32C48 22.0589 39.9411 14 32 14ZM24 26C25.6569 26 27 27.3431 27 29C27 30.6569 25.6569 32 24 32C22.3431 32 21 30.6569 21 29C21 27.3431 22.3431 26 24 26ZM40 26C41.6569 26 43 27.3431 43 29C43 30.6569 41.6569 32 40 32C38.3431 32 37 30.6569 37 29C37 27.3431 38.3431 26 40 26ZM23 36H41C41.5523 36 42 36.4477 42 37C42 41.4183 38.4183 45 34 45H30C25.5817 45 22 41.4183 22 37C22 36.4477 22.4477 36 23 36ZM6 30C4.89543 30 4 30.8954 4 32C4 33.1046 4.89543 34 6 34H10C11.1046 34 12 33.1046 12 32C12 30.8954 11.1046 30 10 30H6ZM54 30C52.8954 30 52 30.8954 52 32C52 33.1046 52.8954 34 54 34H58C59.1046 34 60 33.1046 60 32C60 30.8954 59.1046 30 58 30H54ZM18.3432 47.9946C17.5621 47.2136 16.2931 47.2136 15.5121 47.9946L12.6809 50.8258C11.8999 51.6068 11.8999 52.8758 12.6809 53.6568C13.462 54.4379 14.7311 54.4379 15.5121 53.6568L18.3432 50.8258C19.1243 50.0447 19.1243 48.7757 18.3432 47.9946ZM45.6568 47.9946C44.8758 47.2136 43.6068 47.2136 42.8258 47.9946C42.0447 48.7757 42.0447 50.0447 42.8258 50.8258L45.6568 53.6568C46.4379 54.4379 47.7069 54.4379 48.4879 53.6568C49.269 52.8758 49.269 51.6068 48.4879 50.8258L45.6568 47.9946ZM32 52C30.8954 52 30 52.8954 30 54V58C30 59.1046 30.8954 60 32 60C33.1046 60 34 59.1046 34 58V54C34 52.8954 33.1046 52 32 52Z"
        fill="currentColor"
      />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: (playerName: string) => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [playerName, setPlayerName] = useState('');

  const handleStart = () => {
    if (playerName.trim()) {
      onStartCall(playerName.trim());
    }
  };

  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center">
        <WelcomeImage />

        <h1 className="text-foreground text-2xl font-bold mb-2">
          Improv Battle
        </h1>
        <p className="text-foreground max-w-prose pt-1 leading-6 font-medium">
          Step into the spotlight and improvise your way through wild scenarios!
        </p>

        <div className="mt-6 w-64 flex flex-col gap-3">
          <input
            type="text"
            placeholder="Enter your name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleStart()}
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-foreground placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            autoFocus
          />
          <Button 
            variant="primary" 
            size="lg" 
            onClick={handleStart} 
            disabled={!playerName.trim()}
            className="w-full font-mono disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Improv Battle
          </Button>
        </div>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          A high-energy improv game show where you'll perform wild scenarios and get real-time feedback from your AI host!
        </p>
      </div>
    </div>
  );
};
