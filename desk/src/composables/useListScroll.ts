import { onMounted, onUnmounted } from 'vue';

/**
 * Enables keyboard navigation (Page Up/Down, Home, End) for scrollable list views
 * This composable adds keyboard event handlers to scroll the #list-rows container
 * since browser default keyboard scrolling doesn't work on overflow containers
 */
export function useListScroll() {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Only handle if not typing in an input
    const activeElement = document.activeElement;
    if (
      activeElement instanceof HTMLInputElement ||
      activeElement instanceof HTMLTextAreaElement ||
      (activeElement as any)?. contentEditable === 'true'
    ) {
      return;
    }

    // Find the scrollable list container
    const scrollContainer = document.querySelector('#list-rows') as HTMLElement;
    if (!scrollContainer) return;

    let handled = false;
    const scrollAmount = scrollContainer.clientHeight * 0.9; // 90% of visible height

    switch (e.key) {
      case 'PageDown':
        scrollContainer.scrollTop += scrollAmount;
        handled = true;
        break;
      case 'PageUp': 
        scrollContainer.scrollTop -= scrollAmount;
        handled = true;
        break;
      case 'Home':
        scrollContainer.scrollTop = 0;
        handled = true;
        break;
      case 'End':
        scrollContainer.scrollTop = scrollContainer. scrollHeight;
        handled = true;
        break;
    }

    if (handled) {
      e.preventDefault();
    }
  };

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown);
  });

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown);
  });
}