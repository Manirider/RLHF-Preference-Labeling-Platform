import { useEffect } from 'react';
import { ChoiceType } from '../types';

interface KeyboardShortcutOptions {
  onChoice: (choice: ChoiceType) => void;
  disabled?: boolean;
}

export function useKeyboardShortcuts({ onChoice, disabled = false }: KeyboardShortcutOptions) {
  useEffect(() => {
    if (disabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore when user is actively editing text inputs or textareas
      const target = event.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable)
      ) {
        return;
      }

      // Check key
      const key = event.key.toLowerCase();
      if (key === 'a') {
        event.preventDefault();
        onChoice('A');
      } else if (key === 'b') {
        event.preventDefault();
        onChoice('B');
      } else if (key === 't') {
        event.preventDefault();
        onChoice('tie');
      } else if (key === 's') {
        event.preventDefault();
        onChoice('skip');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChoice, disabled]);
}
