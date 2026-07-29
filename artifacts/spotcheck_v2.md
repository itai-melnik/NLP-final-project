# Verbosity rewrite spot-check (v2)

Random 20% sample (18 of 90 rewrites) for manual
semantic-leakage review (spec §4.2). Check: no fact added or dropped vs baseline.

## agents__4713 — verb_pad2x

**Baseline description:**

```
<!-- devin-review-badge-begin -->

---

<a href="https://livekit.devinenterprise.com/review/livekit/agents/pull/4713" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://static.devin.ai/assets/gh-open-in-devin-review-dark.svg?v=1">
    <img src="https://static.devin.ai/assets/gh-open-in-devin-review-light.svg?v=1" alt="Open with Devin">
  </picture>
</a>
<!-- devin-review-badge-end -->
```

**Rewritten description:**

```
<!-- devin-review-badge-begin -->

---

<a href="https://livekit.devinenterprise.com/review/livekit/agents/pull/4713" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://static.devin.ai/assets/gh-open-in-devin-review-dark.svg?v=1">
    <img src="https://static.devin.ai/assets/gh-open-in-devin-review-light.svg?v=1" alt="Open with Devin">
  </picture>
</a>

The badge above opens the Devin review for pull request 4713 on livekit/agents in a new tab, using a dark-scheme or light-scheme "Open with Devin" image.
<!-- devin-review-badge-end -->
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## altair__3936 — verb_pad4x

**Baseline description:**

```
Chart `mark_line` and similar methods trigger a basedpyright type check warning for unknown argument. This PR adds type annotations to remove the warning. It also fixes some minor type warnings raised by ty and basedpyright.

Resolves #3870.
```

**Rewritten description:**

```
The `mark_line` method as it exists on Chart, and this holds just as true for every one of the other methods that are similar to it and sit alongside it, is one that goes right ahead and ends up triggering a type check warning, and the tool that turns around and emits that warning is basedpyright, with the specific complaint being the one about an unknown argument. What this particular PR goes ahead and does about that whole situation is that it adds in type annotations, and the entire point of adding them in is quite specifically so that the warning ends up being removed. Beyond that, and quite separately from it, it additionally goes and fixes a number of the smaller, more minor type warnings that are floating around, namely the ones that end up being raised by ty on the one hand and by basedpyright on the other.

Resolves #3870.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## backstage__32466 — verb_pad2x

**Baseline description:**

```
## Hey, I just made a Pull Request!

<!-- Please describe what you added, and add a screenshot if possible.
     That makes it easier to understand the change so we can :shipit: faster. -->
Closses:
- #32429 

Updated the `ScheduledTasksContent` component to provide better visual feedback when a user lacks permission to trigger a scheduled task. This change introduces a `CreateNotAllowed` component that displays a disabled block icon with a descriptive tooltip, which is now used as the `errorPage` prop in the `RequirePermission` wrapper.

Additional changes:
- Centered the Actions column in the tasks table for better UI alignment.
- Added a changeset for the patch release.

<img width="1829" height="787" alt="image" src="https://github.com/user-attachments/assets/fbff2991-7445-4e71-b544-1dd179335074" />

#### :heavy_check_mark: Checklist

<!--- Please include the following in your Pull Request when applicable: -->

- [x] A changeset describing the change and affected packages. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#creating-changesets))
- [ ] Added or updated documentation
- [x] Tests for new functionality and regression tests for bug fixes
- [x] Screenshots attached (for UI changes)
- [x] All your commits have a `Signed-off-by` line in the message. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#developer-certificate-of-origin))
```

**Rewritten description:**

```
## Hey, I just made a Pull Request!

<!-- Please go ahead and describe the thing that you added here, and then, if it happens to be possible for you to do so, please also add in a screenshot of it as well.
     The reason for asking is that doing that is what makes it easier for everyone to understand the change that has been made, and that in turn is what lets us :shipit: faster than we otherwise would. -->
Closses:
- #32429 

Went ahead and updated the `ScheduledTasksContent` component, and the whole point of updating it was so that it would provide better visual feedback than it did before, specifically in that situation where a user turns out to be lacking the permission that is needed in order to trigger a scheduled task. What this particular change does is that it introduces a `CreateNotAllowed` component of its own, and that component is one that goes ahead and displays a disabled block icon, and along with that icon there is a descriptive tooltip as well. That component is the thing that is now being used as the `errorPage` prop over inside of the `RequirePermission` wrapper.

Additional changes:
- Went and centered the Actions column as it sits in the tasks table, and the reason for doing that was for the sake of better UI alignment.
- Added in a changeset, and that changeset is there for the patch release.

<img width="1829" height="787" alt="image" src="https://github.com/user-attachments/assets/fbff2991-7445-4e71-b544-1dd179335074" />

#### :heavy_check_mark: Checklist

<!--- Please go ahead and include each of the following things in your Pull Request, doing so in whichever cases they happen to be applicable: -->

- [x] A changeset that describes the change itself along with the packages that end up being affected by it. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#creating-changesets))
- [ ] Documentation that has either been added or else updated
- [x] Tests covering the new functionality, along with regression tests for any of the bug fixes
- [x] Screenshots that have been attached (for the changes that are UI changes)
- [x] Every single one of your commits has a `Signed-off-by` line sitting in the message of it. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#developer-certificate-of-origin))
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## backstage__32466 — verb_pad4x

**Baseline description:**

```
## Hey, I just made a Pull Request!

<!-- Please describe what you added, and add a screenshot if possible.
     That makes it easier to understand the change so we can :shipit: faster. -->
Closses:
- #32429 

Updated the `ScheduledTasksContent` component to provide better visual feedback when a user lacks permission to trigger a scheduled task. This change introduces a `CreateNotAllowed` component that displays a disabled block icon with a descriptive tooltip, which is now used as the `errorPage` prop in the `RequirePermission` wrapper.

Additional changes:
- Centered the Actions column in the tasks table for better UI alignment.
- Added a changeset for the patch release.

<img width="1829" height="787" alt="image" src="https://github.com/user-attachments/assets/fbff2991-7445-4e71-b544-1dd179335074" />

#### :heavy_check_mark: Checklist

<!--- Please include the following in your Pull Request when applicable: -->

- [x] A changeset describing the change and affected packages. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#creating-changesets))
- [ ] Added or updated documentation
- [x] Tests for new functionality and regression tests for bug fixes
- [x] Screenshots attached (for UI changes)
- [x] All your commits have a `Signed-off-by` line in the message. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#developer-certificate-of-origin))
```

**Rewritten description:**

```
## Hey, I just made a Pull Request!

<!-- Please, if you would be so kind, go right ahead and describe the particular thing that it is that you have added here in this spot, and then, in the event that it happens to be at all possible for you to manage it, please also go ahead and add in a screenshot of the thing as well while you are about it.
     The whole reason that we go about asking for that is because doing exactly that is the very thing which ends up making it a good deal easier for everybody involved to properly understand the change that has been made here, and that in its turn is precisely the thing which then puts us in a position to be able to :shipit: a good deal faster than we would otherwise have been able to manage. -->
Closses:
- #32429 

What has been done here is that the `ScheduledTasksContent` component has been updated, and the entire point and purpose behind going and updating that component in the first place was so that it would end up providing visual feedback that is better than the visual feedback which it happened to provide beforehand, and the particular situation in which all of that comes into play is the situation where a user turns out to be lacking the permission that would be required of them in order for them to trigger a scheduled task. The thing that this particular change goes ahead and does, then, is that it introduces into the picture a `CreateNotAllowed` component all of its very own, and that component right there is one whose job is to go ahead and display a disabled block icon, and then, sitting right there together with that icon, there is additionally a tooltip of the descriptive sort as well. That very component is then the thing which is, as of now, being used in the role of the `errorPage` prop, and the place where it is being used in that role is over inside of the `RequirePermission` wrapper.

Additional changes:
- Went ahead and centered the Actions column exactly as that column sits there inside of the tasks table, and the reason behind going and doing that particular thing was entirely for the sake of achieving better alignment in the UI than there was before.
- Added in a changeset of its own as well, and that changeset there is one that exists specifically for the sake of the patch release.

<img width="1829" height="787" alt="image" src="https://github.com/user-attachments/assets/fbff2991-7445-4e71-b544-1dd179335074" />

#### :heavy_check_mark: Checklist

<!--- Please, if you would, go right ahead and make a point of including each and every single one of the following things over inside of your Pull Request, and do that in whichever of the cases it happens to be that they are actually applicable to the situation at hand: -->

- [x] A changeset, one which goes ahead and describes the change its own self and which additionally describes each of the packages that end up being affected by that change as well. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#creating-changesets))
- [ ] Documentation which has either been newly added in or else has been updated from what it was
- [x] Tests which cover the new functionality that has been introduced, and, right alongside those, regression tests covering each and every one of the bug fixes
- [x] Screenshots which have been properly attached to the whole thing (and this is for those changes which happen to be UI changes)
- [x] Each and every single last one of your commits is one that has a `Signed-off-by` line sitting right there inside of the message that belongs to it. ([more info](https://github.com/backstage/backstage/blob/master/CONTRIBUTING.md#developer-certificate-of-origin))
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## coreos-assembler__4359 — verb_pad2x

**Baseline description:**

```
Reduce disk on multipath via qmp, then reboot.
`{ "execute": "device_del", "arguments": { "id": "/machine/peripheral-anon/device[3]"}}`

See https://issues.redhat.com/browse/OCPBUGS-56597
```

**Rewritten description:**

```
To reduce the disk on multipath, use qmp to run the following command, and then reboot afterward: `{ "execute": "device_del", "arguments": { "id": "/machine/peripheral-anon/device[3]"}}` See the tracking issue at https://issues.redhat.com/browse/OCPBUGS-56597
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## dask__12221 — verb_pad4x

**Baseline description:**

```
- CPU_COUNT enhanced to reflect cpu affinity on Linux (all Python versions) and Windows/Mac (Python >=3.13) even when psutil is not installed
- CPU_COUNT static type changed from `int | None` to `int`
- Added unit tests for CPU affinity

This was tested on an enhanced CI matrix (https://github.com/dask/dask/pull/12221/commits/71ff2c2b6ab5c655e8f95059752fd974c87a0cda) and returned all green (https://github.com/crusaderky/dask/actions/runs/20781477335/job/59679809102). CI changes were later reverted.
```

**Rewritten description:**

```
- CPU_COUNT has now been enhanced in such a way that it reflects the cpu affinity of the system that it is running on; this enhanced behavior applies on Linux for every single one of the Python versions, and it likewise applies on both Windows and Mac in the specific case of Python version >=3.13, and, importantly, all of this continues to hold true even in the circumstance where the psutil library happens to not be installed on the system at all
- The static type that is associated with CPU_COUNT has been changed, moving it away from what was previously `int | None` and over to being simply `int` instead
- A set of unit tests, specifically ones that exercise and cover CPU affinity, have now been added into the suite

Every single part of this was put to the test on an enhanced CI matrix, which can be seen for reference right here (https://github.com/dask/dask/pull/12221/commits/71ff2c2b6ab5c655e8f95059752fd974c87a0cda), and the eventual outcome of that testing was that it came back returning all green right across the board (https://github.com/crusaderky/dask/actions/runs/20781477335/job/59679809102). It should also be noted, for completeness, that the CI changes which were involved in this were themselves later reverted again after the fact.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## mycli__1517 — verb_pad4x

**Baseline description:**

```
## Description
 * move to new section
 * change the name to `default_ssl_mode`
 * place with other SSL options
 * continue to silently accept the old spelling in `[main]`

## Checklist
<!--- We appreciate your help and want to give you credit. Place an `x` in the boxes below as you complete them. -->
- [x] I added this contribution to the `changelog.md` file.
- [x] I added my name to the `AUTHORS` file (or it's already there).
- [x] To lint and format the code, I ran
    ```bash
    uv run ruff check && uv run ruff format && uv run mypy --install-types .
    ```
```

**Rewritten description:**

```
## Description
 * Go right ahead and take this whole entire thing and move it over so that it now lives within a brand new section that is entirely of its very own from now on
 * Go and change the actual name that it currently has at the moment, in such a way and to such an extent that from this point onward it will instead go on to become the name `default_ssl_mode`
 * Take it and place it, in terms of its position, right there together alongside all of the other various SSL options that already happen to be sitting there in that spot
 * Continue on, exactly as was being done before, to silently go about the business of accepting the old spelling of the thing in each and every case where it happens to appear within the `[main]` section

## Checklist
<!--- We appreciate your help and want to give you credit. Place an `x` in the boxes below as you complete them. -->
- [x] I have gone right ahead and taken this particular contribution of mine, the one that is being made here, and I have added it directly into the `changelog.md` file, doing so exactly and precisely as was asked of me to go and do here in the first place
- [x] I have gone right ahead and added my own personal name over onto the `AUTHORS` file (or, alternatively, and just as likely, it may very well turn out to be the case that my name happens to already be sitting right there within that file as things currently stand at the moment)
- [x] In order to go about the whole business of both linting the code and also, on top of that, formatting the code properly and correctly the way it should be, the one single specific command that I went ahead and actually ran myself in order to accomplish that whole thing was the particular following one that is shown right here down below
    ```bash
    uv run ruff check && uv run ruff format && uv run mypy --install-types .
    ```
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## node-postgres__3547 — verb_pad2x

**Baseline description:**

```
This PR introduces three changes to make the pg package more compatible with Deno while
keeping full Node.js functionality:

1. **Default user value**  
   - Replace `user: process.platform === 'win32' ? process.env.USERNAME : process.env.USER`  
     with `user: 'postgres'` in defaults.
   - Avoids requiring environment variables in Deno.

2. **Config-first parameter resolution**  
   - Update `val()` in connection-parameters.js to return `config[key]` first, before
     checking environment variables.
   - Prevents Deno errors when `--allow-env` is not granted.

3. **Safe NODE_PG_FORCE_NATIVE check**  
   - Wrap the `NODE_PG_FORCE_NATIVE` check in a `try/catch`.
   - Ensures `process.env` access in Deno doesn’t throw, while preserving Node.js behavior.

These changes maintain Node.js compatibility, preserve the lazy-loading of the native module,
and allow using the package in Deno without requiring `--allow-env`.
```

**Rewritten description:**

```
This PR right here is one that introduces three separate changes, and the whole point of them is to make the pg package into something more compatible with Deno, while at the same time keeping the full Node.js functionality intact:

1. **Default user value**  
   - Go ahead and replace `user: process.platform === 'win32' ? process.env.USERNAME : process.env.USER`  
     with `user: 'postgres'` over in the defaults.
   - What this does is avoid the whole business of requiring environment variables when you are in Deno.

2. **Config-first parameter resolution**  
   - Update the `val()` function in connection-parameters.js so that it returns `config[key]` first of all, before it goes
     and checks any of the environment variables.
   - This is the thing that prevents the Deno errors in the case where `--allow-env` has not been granted.

3. **Safe NODE_PG_FORCE_NATIVE check**  
   - Wrap the whole `NODE_PG_FORCE_NATIVE` check up inside of a `try/catch`.
   - This ensures that the `process.env` access when in Deno is not something that throws, and it does that while still preserving the Node.js behavior as it was.

All of these changes together maintain the Node.js compatibility, they preserve the lazy-loading of the native module,
and they allow the package to be used over in Deno without there being any requirement for `--allow-env`.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## pipecat__2735 — verb_terse

**Baseline description:**

```
…in favor of `LLMContext`, except for:

- Usage in classes that are already deprecated
- Usage related to realtime LLMs, which don't yet support `LLMContext`
- Usage in (soon-to-be-deprecated) code paths related to `OpenAILLMContext` itself and associated machinery
```

**Rewritten description:**

```
…in favor of `LLMContext`, except:

- already-deprecated classes
- realtime LLMs (no `LLMContext` yet)
- (soon-to-be-deprecated) `OpenAILLMContext` code paths and machinery
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## pipecat__2792 — verb_terse

**Baseline description:**

```
#### Please describe the changes in your PR. If it is addressing an issue, please reference that as well.

Adds support for image generation models.
```

**Rewritten description:**

```
#### Describe your PR's changes; reference any issue it addresses.

Adds image generation model support.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## pipecat__3233 — verb_terse

**Baseline description:**

```
- improve error handling to log all error types

Add error frame for all error types from https://elevenlabs.io/docs/developers/guides/cookbooks/speech-to-text/streaming#error-handling 

- fix issue with infinite loop when websocket disconnects
Explanation: the [_receive_messages](https://github.com/pipecat-ai/pipecat/blob/7e424d750ebee48d8ff8af6f009b8257acd41dc5/src/pipecat/services/elevenlabs/stt.py#L693) method is executed inside a loop with attempt to reconnect on error but the eleven labs implementation had a try catch due to which, if the websocket randomly disconnects then this part goes into an infinite loop which blocks the whole process.

https://github.com/pipecat-ai/pipecat/blob/7e424d750ebee48d8ff8af6f009b8257acd41dc5/src/pipecat/services/websocket_service.py#L133-L154
```

**Rewritten description:**

```
- error handling: log all error types

Error frames for all types: https://elevenlabs.io/docs/developers/guides/cookbooks/speech-to-text/streaming#error-handling

- fix infinite loop on websocket disconnect
Explanation: [_receive_messages](https://github.com/pipecat-ai/pipecat/blob/7e424d750ebee48d8ff8af6f009b8257acd41dc5/src/pipecat/services/elevenlabs/stt.py#L693) runs in a reconnect loop, but eleven labs' try/catch means a random websocket disconnect loops forever, blocking the whole process.

https://github.com/pipecat-ai/pipecat/blob/7e424d750ebee48d8ff8af6f009b8257acd41dc5/src/pipecat/services/websocket_service.py#L133-L154
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## protocompile__630 — verb_pad4x

**Baseline description:**

```
This fixes EOF lookups for `InverseLocation`. Currently this will panic as any `LineOffset` requires a trailing newline. We now use the EOF as the end of line for the last line.

Fixes https://github.com/bufbuild/vscode-buf/issues/478#issuecomment-3541151881
```

**Rewritten description:**

```
This particular change goes ahead and fixes the EOF lookups for the `InverseLocation`. The way that things happen to stand at the current moment in time, this is something which will actually go and panic, and the specific underlying reason as to why it ends up panicking in the first place is the fact that any `LineOffset` whatsoever, no matter which one, absolutely requires that there be a trailing newline character present for it. The thing that we now go and do instead, in place of all that, is to use the EOF its own self to act and serve as the end of the line specifically for the case of the very last line that is there.

Fixes https://github.com/bufbuild/vscode-buf/issues/478#issuecomment-3541151881
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## stylelint__8953 — verb_terse

**Baseline description:**

```
## Summary

Fixes #3972

The `no-duplicate-selectors` rule now correctly detects duplicate class selectors that use different CSS escape sequence formats. For example, `.u-m\00002b` and `.u-m\+` are now recognized as duplicates since both represent `.u-m+`.

## Changes

- Added `normalizeNodeEscaping()` helper in `normalizeSelector.mjs` that uses postcss-selector-parser's getter/setter behavior to normalize CSS escaping
- Added test cases for escaped selector duplicates

## How it works

The fix leverages postcss-selector-parser's built-in value getter/setter behavior for ClassName nodes. The getter returns the unescaped value, while the setter re-escapes it in a normalized form. By doing `node.value = node.value`, we trigger this normalization, ensuring equivalent selectors compare as equal regardless of their original escape format.

Reference: https://github.com/postcss/postcss-selector-parser/blob/1b1e9c3bc10ccc3bc5f07a987caa7f2684c0b52f/src/selectors/className.js#L13-L28
```

**Rewritten description:**

```
## Summary

Fixes #3972

The `no-duplicate-selectors` rule now detects duplicate class selectors using different CSS escapes. E.g. `.u-m\00002b` and `.u-m\+` are now duplicates, both representing `.u-m+`.

## Changes

- Added `normalizeNodeEscaping()` in `normalizeSelector.mjs` using postcss-selector-parser's getter/setter to normalize escaping
- Added test cases for escaped selector duplicates

## How it works

`node.value = node.value` triggers normalization, so equivalent selectors compare equal regardless of escape format.

Reference: https://github.com/postcss/postcss-selector-parser/blob/1b1e9c3bc10ccc3bc5f07a987caa7f2684c0b52f/src/selectors/className.js#L13-L28
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## transformers.js__1436 — verb_pad2x

**Baseline description:**

```
The following errors from https://github.com/huggingface/transformers.js/issues/1409 are adressed by this PR:
-  Added a type definition (@typedef) that tells TypeScript what PretrainedProcessorOptions is
-  Changed the parameter type from "an array of Tensors" to "exactly 3 Tensors" (char, bpe, wp)
- The sharp import error (needs esModuleInterop)

Closes https://github.com/huggingface/transformers.js/issues/1337
Closes https://github.com/huggingface/transformers.js/issues/1409
```

**Rewritten description:**

```
The following errors, every single one of which comes from https://github.com/huggingface/transformers.js/issues/1409, are the ones that end up being adressed by this PR right here:
-  Added in a type definition (@typedef), which is the thing that goes ahead and tells TypeScript what exactly PretrainedProcessorOptions is
-  Changed the type of the parameter, taking it from being "an array of Tensors" over to being "exactly 3 Tensors" instead of that (char, bpe, wp)
- The sharp import error, which is the one that needs esModuleInterop

Closes https://github.com/huggingface/transformers.js/issues/1337
Closes https://github.com/huggingface/transformers.js/issues/1409
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## transformers.js__1436 — verb_terse

**Baseline description:**

```
The following errors from https://github.com/huggingface/transformers.js/issues/1409 are adressed by this PR:
-  Added a type definition (@typedef) that tells TypeScript what PretrainedProcessorOptions is
-  Changed the parameter type from "an array of Tensors" to "exactly 3 Tensors" (char, bpe, wp)
- The sharp import error (needs esModuleInterop)

Closes https://github.com/huggingface/transformers.js/issues/1337
Closes https://github.com/huggingface/transformers.js/issues/1409
```

**Rewritten description:**

```
Errors from https://github.com/huggingface/transformers.js/issues/1409 adressed:
- @typedef for PretrainedProcessorOptions (TypeScript)
- parameter type: exactly 3 Tensors (char, bpe, wp), not an array
- sharp import error (esModuleInterop)

Closes https://github.com/huggingface/transformers.js/issues/1337
Closes https://github.com/huggingface/transformers.js/issues/1409
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## vega__4219 — verb_pad2x

**Baseline description:**

```
## Motivation

- Incrementally typing `vega-util`
- Related to https://github.com/vega/vega/issues/3971

## Changes

- Adds a runtime error when users try to operate on a domain that doesn't have at least 1 value
- Everything else should have same runtime behavior as before, I just added types

## Testing


```vasg
npm test --workspace=vega-util -- test/transform-test
```
```

**Rewritten description:**

```
## Motivation

- This is about incrementally typing `vega-util`
- It is related to the issue over at https://github.com/vega/vega/issues/3971

## Changes

- Adds in a runtime error for the case when users go and try to operate on a domain that does not happen to have at least 1 value in it
- Everything else should keep on having the same runtime behavior as it did before; all I actually did was to go and add in the types

## Testing

```vasg
npm test --workspace=vega-util -- test/transform-test
```
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## vitest__9521 — verb_terse

**Baseline description:**

```
### Description

<!-- Please insert your description here and provide especially info about the "what" this PR is solving -->
This PR adds a new `coverage.changed` option that allows running all tests while only computing coverage for changed files. This is useful for CI pipelines that need to:

1. Run the full test suite to ensure all tests pass
2. Compute coverage only for files changed in a pull request

Previously, this required running two separate commands, which doubled the test execution time.

Resolves #8747 

<!-- You can also add additional context here -->

### Usage

```typescript
export default defineConfig({
  test: {
    coverage: {
      changed: 'HEAD', // or any git ref like 'main', 'origin/main'
    },
  },
})
```

The `changed` option accepts:
- `'HEAD'` - Compare against the last commit
- `'main'` - Compare against the main branch
- `'origin/main'` - Compare against remote main branch
- Any valid git reference

### Testing Instructions

1. Navigate to the test directory:
   ```bash
   cd test/coverage-test
   ```

2. Create a demo config file `vitest.demo.config.ts`:
   ```typescript
   import { defineConfig } from 'vitest/config'

   export default defineConfig({
     test: {
       include: ['**/file-to-change.test.ts', '**/math.test.ts'],
       coverage: {
         enabled: true,
         provider: 'istanbul',
         reporter: ['text'],
         reportsDirectory: './coverage-demo',
       },
     },
   })
   ```

3. Run tests **without** the `changed` option:
   ```bash
   pnpm vitest run --config=vitest.demo.config.ts
   ```
   
   **Result:** Coverage includes all files
   ```
   File               | % Stmts | % Branch | % Funcs | % Lines |
   -------------------|---------|----------|---------|---------|
   All files          |   33.33 |      100 |   33.33 |   33.33 |
    file-to-change.ts |      50 |      100 |      50 |      50 |
    math.ts           |      25 |      100 |      25 |      25 |
   ```

4. Modify `fixtures/src/file-to-change.ts` (make any change)

5. Update config to add `changed: 'HEAD'`:
   ```typescript
   coverage: {
     enabled: true,
     provider: 'istanbul',
     reporter: ['text'],
     reportsDirectory: './coverage-demo',
     changed: 'HEAD', // ← Add this line
   },
   ```

6. Run tests again:
   ```bash
   pnpm vitest run --config=vitest.demo.config.ts
   ```
   
   **Result:** Coverage includes only changed files
   ```
   File               | % Stmts | % Branch | % Funcs | % Lines |
   -------------------|---------|----------|---------|---------|
   All files          |      50 |      100 |      50 |      50 |
    file-to-change.ts |      50 |      100 |      50 |      50 |
   ```

Note: Both test runs execute **all tests** (`file-to-change.test.ts` and `math.test.ts`), but the second run only reports coverage for the modified file.

### Please don't delete this checklist! Before submitting the PR, please make sure you do the following:
- [x] It's really useful if your PR references an issue where it is discussed ahead of time. If the feature is substantial or introduces breaking changes without a discussion, PR might be closed.
- [x] Ideally, include a test that fails without this PR but passes with it.
- [x] Please, don't make changes to `pnpm-lock.yaml` unless you introduce a new test example.
- [x] Please check [Allow edits by maintainers](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork) to make review process faster. Note that this option is not available for repositories that are owned by Github organizations.

### Tests
- [x] Run the tests with `pnpm test:ci`.

### Documentation
- [x] If you introduce new functionality, document it. You can run documentation with `pnpm run docs` command.

### Changesets
- [x] Changes in changelog are generated from PR name. Please, make sure that it explains your changes in an understandable manner. Please, prefix changeset messages with `feat:`, `fix:`, `perf:`, `docs:`, or `chore:`.
```

**Rewritten description:**

```
### Description

Adds a new `coverage.changed` option that runs all tests while computing coverage only for changed files. Useful for CI pipelines that need to run the full suite yet compute coverage only for files changed in a PR; previously this required two separate commands, doubling test time.

Resolves #8747

### Usage

```typescript
export default defineConfig({
  test: {
    coverage: {
      changed: 'HEAD', // or any git ref like 'main', 'origin/main'
    },
  },
})
```

The `changed` option accepts:
- `'HEAD'` - Compare against the last commit
- `'main'` - Compare against the main branch
- `'origin/main'` - Compare against remote main branch
- Any valid git reference

### Testing Instructions

In `test/coverage-test`, create a demo config, run `pnpm vitest run --config=vitest.demo.config.ts` without `changed` (coverage includes all files), modify a fixture, add `changed: 'HEAD'`, and run again (coverage includes only changed files). Both runs execute all tests; the second only reports coverage for the modified file.

### Please don't delete this checklist! Before submitting the PR, please make sure you do the following:
- [x] PR should reference a pre-discussed issue; substantial or breaking changes without discussion may be closed.
- [x] Include a test that fails without this PR but passes with it.
- [x] Don't change `pnpm-lock.yaml` unless adding a new test example.
- [x] Check [Allow edits by maintainers](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork) to speed review (not for Github-org repos).

### Tests
- [x] Run tests with `pnpm test:ci`.

### Documentation
- [x] Document new functionality (`pnpm run docs`).

### Changesets
- [x] Changelog is generated from the PR name; make it clear, prefixed `feat:`, `fix:`, `perf:`, `docs:`, or `chore:`.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## zod__5672 — verb_pad2x

**Baseline description:**

```
Solves #5284 

httpUrl allow single slash (http:/example.com) and no slash (http:example.com) 

example :
{
"parsedUser": {
"website": "http:example.com"
}
}

{
"parsedUser": {
"website": "https:/[www.google.com]
}
}

Add strict protocol:// check before new URL() for httpUrl()
```

**Rewritten description:**

```
Solves #5284

The issue is that httpUrl currently allows a single slash (http:/example.com) as well as no slash at all (http:example.com)

example :
{
"parsedUser": {
"website": "http:example.com"
}
}

{
"parsedUser": {
"website": "https:/[www.google.com]
}
}

The fix is to add a strict protocol:// check, placing it before the call to new URL() over inside of httpUrl()
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---
