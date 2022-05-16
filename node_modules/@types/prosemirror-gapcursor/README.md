# Installation
> `npm install --save @types/prosemirror-gapcursor`

# Summary
This package contains type definitions for prosemirror-gapcursor (https://github.com/ProseMirror/prosemirror-gapcursor).

# Details
Files were exported from https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/prosemirror-gapcursor.
## [index.d.ts](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/prosemirror-gapcursor/index.d.ts)
````ts
// Type definitions for prosemirror-gapcursor 1.0
// Project: https://github.com/ProseMirror/prosemirror-gapcursor
// Definitions by: Bradley Ayers <https://github.com/bradleyayers>
//                 David Hahn <https://github.com/davidka>
//                 Tim Baumann <https://github.com/timjb>
//                 Patrick Simmelbauer <https://github.com/patsimm>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped
// TypeScript Version: 2.3

import { Plugin, Selection } from 'prosemirror-state';
import { NodeSpec } from 'prosemirror-model';

/**
 * Gap cursor selections are represented using this class. Its
 * `$anchor` and `$head` properties both point at the cursor position.
 */
export class GapCursor extends Selection {}
/**
 * Create a gap cursor plugin. When enabled, this will capture clicks
 * near and arrow-key-motion past places that don't have a normally
 * selectable position nearby, and create a gap cursor selection for
 * them. The cursor is drawn as an element with class
 * `ProseMirror-gapcursor`. You can either include
 * `style/gapcursor.css` from the package's directory or add your own
 * styles to make it visible.
 */
export function gapCursor(): Plugin;

declare module "prosemirror-model" {
    interface NodeSpec {
        /**
         * By default, gap cursor are only allowed in places where the
         * default content node (in the schema content constraints) is a
         * textblock node. You can customize this by adding an `allowGapCursor`
         * property to your node specs — if it's true, gap cursor are allowed
         * everywhere in that node, if it's false they are never allowed.
         */
        allowGapCursor?: boolean | undefined;
    }
}

````

### Additional Details
 * Last updated: Wed, 07 Jul 2021 17:02:38 GMT
 * Dependencies: [@types/prosemirror-state](https://npmjs.com/package/@types/prosemirror-state), [@types/prosemirror-model](https://npmjs.com/package/@types/prosemirror-model)
 * Global values: none

# Credits
These definitions were written by [Bradley Ayers](https://github.com/bradleyayers), [David Hahn](https://github.com/davidka), [Tim Baumann](https://github.com/timjb), and [Patrick Simmelbauer](https://github.com/patsimm).
