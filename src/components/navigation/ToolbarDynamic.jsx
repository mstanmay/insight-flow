'use client';
import React, { useRef, useState } from 'react';
import { motion, MotionConfig } from 'motion/react';
import { useClickOutside } from '../../hooks';
import { ArrowLeft, Search, User } from 'lucide-react';
import { useWorkspace } from '../../context/WorkspaceContext';

const transition = {
  type: 'spring',
  bounce: 0.1,
  duration: 0.2,
};

function Button({
  children,
  onClick,
  disabled,
  ariaLabel,
}) {
  return (
    <button
      className="relative flex h-9 w-9 shrink-0 scale-100 select-none appearance-none items-center justify-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 focus-visible:ring-2 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}

export default function ToolbarDynamic({ className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const containerRef = useRef(null);
  const { toggleTheme } = useWorkspace();

  useClickOutside(containerRef, () => {
    setIsOpen(false);
  });

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setQuery(val);

    const feedbackInput = document.getElementById('feedback-search-input');
    if (feedbackInput) {
      feedbackInput.value = val;
      if (window.filterFeedbackTable) window.filterFeedbackTable();
    }
  };

  return (
    <MotionConfig transition={transition}>
      <div className={`fixed bottom-6 right-6 z-40 ${className}`} ref={containerRef}>
        <div className="h-full w-full rounded-xl border border-zinc-200 dark:border-white/10 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md shadow-2xl shadow-indigo-950/20">
          <motion.div
            animate={{
              width: isOpen ? '300px' : '98px',
            }}
            initial={false}
            className="overflow-hidden"
          >
            <div className="flex items-center gap-1 p-1">
              {!isOpen ? (
                <>
                  <Button
                    onClick={() => setIsOpen(true)}
                    ariaLabel="Search records"
                  >
                    <Search className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={toggleTheme}
                    ariaLabel="Toggle theme"
                  >
                    <User className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <div className="flex w-full items-center gap-2 px-1">
                  <Button
                    onClick={() => setIsOpen(false)}
                    ariaLabel="Back"
                  >
                    <ArrowLeft className="h-4 w-4" />
                  </Button>
                  <div className="relative w-full">
                    <input
                      className="h-8 w-full rounded-lg bg-zinc-100 dark:bg-zinc-800 px-3 text-xs text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans"
                      placeholder="Search signals..."
                      autoFocus
                      value={query}
                      onChange={handleSearchChange}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </MotionConfig>
  );
}
