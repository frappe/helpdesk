# Installation
> `npm install --save @types/prosemirror-dropcursor`

# Summary
This package contains type definitions for prosemirror-dropcursor (https://github.com/ProseMirror/prosemirror-dropcursor).

# Details
Files were exported from https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/prosemirror-dropcursor.
## [index.d.ts](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/prosemirror-dropcursor/index.d.ts)
````ts
// Type definitions for prosemirror-dropcursor 1.0
// Project: https://github.com/ProseMirror/prosemirror-dropcursor
// Definitions by: Bradley Ayers <https://github.com/bradleyayers>
//                 David Hahn <https://github.com/davidka>
//                 Daniil Dotsev <https://github.com/dddotsev>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped
// TypeScript Version: 2.3

import { Plugin } from 'prosemirror-state';

/**
 * Create a plugin that, when added to a ProseMirror instance,
 * causes a decoration to show up at the drop position when something
 * is dragged over the editor.
 *
 * @param options These options are supported:
 * @param options.class A CSS class name to add to the cursor element.
 * @param options.color The color of the cursor. Defaults to `black`.
 * @param options.width The precise width of the cursor in pixels. Defaults to 1.
 */
export function dropCursor(options?: {
  class?: string | null | undefined;
  color?: string | null | undefined;
  width?: number | null | undefined;
}): Plugin;

````

### Additional Details
 * Last updated: Mon, 23 Aug 2021 20:18:30 GMT
 * Dependencies: [@types/prosemirror-state](https://npmjs.com/package/@types/prosemirror-state)
 * Global values: none

# Credits
These definitions were written by [Bradley Ayers](https://github.com/bradleyayers), [David Hahn](https://github.com/davidka), and [Daniil Dotsev](https://github.com/dddotsev).
