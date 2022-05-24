## v4.2.2

- Switch dependent internal utility functions to lodash family

## v4.2.1

- Fix invert retain across multiple ops

## v4.2.0

- Add `invert()`

## v4.1.0

- Use fast-diff 1.2.0 in `diff()`, so that diffs do not split Unicode surrogate pairs

## v4.0.1

- Fix build package casing

## v4.0.0

Source rewritten in Typescript

#### Breaking Changes

These were never documented as officially supported but to be safe we are doing a major version bump.

- No longer works in IE8 as there is function called `delete` and IE8 treats that as a reserved identifier
- The source structure has changed so those utilizing NPM's ability to import from arbitrary directories ex. `import DeltaOp from 'quill-delta/lib/op'` will have to update their imports

## v3.6.3

- Performance optimization for `compose`

## v3.6.2

- Documentation fixes

## v3.6.1

- Stop using `=>` because of IE11

## v3.6.0

- Add experimental method `changeLength()`

## v3.5.0

- Add counter and early return to `eachLine()`

## v3.4.0

- Support index suggestion in `diff()`

## v3.3.0

- Add `partition()`

## v3.2.0

- Add `eachLine()`, `map()`, `reduce()`, `filter()`, `forEach()`

## v3.1.0

- Pull out quilljs/delta from ottypes/rich-text

## v3.0.0

#### Breaking Changes

- Deep copy and compare attributes and deltas

## v2.1.0

- Add `concat()` method for document Deltas

## v2.0.0

#### Breaking Changes

- `compose()` returns a new Delta instead of self-modifying

#### Features

- Support embed being any non-string type
