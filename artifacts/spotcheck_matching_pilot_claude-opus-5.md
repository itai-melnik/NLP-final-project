# Matcher pilot spot-check — verify each verdict by hand

Matcher: `claude-opus-5` | prompt `matcher-v3` (pairwise) | 16 requests, 84 pair calls

Each judge issue was compared against every human comment separately.
For each issue: ✅/❌ the matcher's verdict. A verdict is correct if the
linked comment describes the SAME underlying problem (any phrasing/line),
and `null` is correct when no comment does.

---
## openbao__1906  (judge: claude, key `9189d922`)

**Human comments:**
- `c_1` changelog/1906.txt:None — ```suggestion core/leases: lease lookup will now include `path`, `namespace_path` and `revoke_error` ```

**Judge issues → matcher verdicts:**
- [0] vault/logical_system.go:2195 — The new `revoke_error` field is exposed directly in the lease lookup response even though the PR description itself notes this error text may contain sensitive information that is normally only logged, introducing a potential information disclosure risk.
  → **no match**
    - `c_1`: no (conf 0.95) — The human comment is a changelog wording suggestion in changelog/1906.txt, not a security concern. The candidate flags a potential information disclosure risk with the revoke_error field in logical_system.go. Different location and entirely different concern.

---
## openbao__1906  (judge: claude, key `03865299`)

**Human comments:**
- `c_1` changelog/1906.txt:None — ```suggestion core/leases: lease lookup will now include `path`, `namespace_path` and `revoke_error` ```

**Judge issues → matcher verdicts:**
- [0] vault/logical_system.go:2200 — revoke_error is now exposed via the lease lookup API response even though the PR description itself flags that revoke errors could contain sensitive information, creating a potential information disclosure without any redaction or an ACL/permission gate.
  → **no match**
    - `c_1`: no (conf 0.95) — The human comment is a changelog wording suggestion (fixing the changelog text to list the fields). The candidate flags a security/information-disclosure concern about exposing revoke_error in the lease lookup API. These are entirely different concerns and different files.

---
## backstage__32466  (judge: claude, key `5d4880a6`)

**Human comments:**
- `c_1` .changeset/small-jars-lick.md:None — ```suggestion Fixes an issue where a user lacking permission to schedule tasks can now easily see the issue through a custom icon + tooltip. ``` or such?
- `c_2` plugins/devtools/src/components/Content/ScheduledTasksContent/ScheduledTasksContent.tsx:None — Is the import ordering update here intentional? If we can, let's keep the ordering as it was before.

**Judge issues → matcher verdicts:**
- [0] plugins/devtools/src/components/Content/ScheduledTasksContent/ScheduledTasksContent.tsx:0 — PR description claims tests were added but no test files are included or updated in the diff.
  → **no match**
    - `c_1`: no (conf 0.97) — The human comment is about wording of the changeset description file. The candidate flags missing tests in a component file. Completely different concerns and locations.
    - `c_2`: no (conf 0.97) — Human comment concerns import ordering changes in the file; candidate concerns missing tests. Completely different concerns despite same file.

---
## qutebrowser__8845  (judge: claude, key `b99b1c21`)

**Human comments:**
- `c_1` qutebrowser/browser/urlmarks.py:113 — This should do a `self.changed.emit()` like the other methods do. Things *seem* to work correctly despite of it missing because e.g. the `:open` completion does currently always refresh the data using the quickmark manager, but it missing seems like a footgun anyways.
- `c_2` tests/unit/browser/test_urlmarks.py:None — This isn't what you want to test for in this test, so you can leave that off.
- `c_3` tests/unit/browser/test_urlmarks.py:None — This should have a `with qtbot.wait_signal(bm.changed):` around it (like in some other tests) to ensure the signal is emitted.
- `c_4` tests/unit/browser/test_urlmarks.py:None — Maybe use `.org` or so instead of `.com` here, to ensure existing marks are indeed cleared properly?

**Judge issues → matcher verdicts:**
- [0] qutebrowser/browser/urlmarks.py:102 — reload() calls _init_lineparser() again without closing/releasing the previous LineParser instance, potentially leaking file handles or save-manager registrations on repeated reloads.
  → **no match**
    - `c_1`: no (conf 0.85) — The human comment concerns a missing `self.changed.emit()` in the reload method, a signal-notification footgun. The candidate flags a resource-leak concern about not closing the previous LineParser in reload(). Both are in the same reload method region, but the concerns are substantively different (missing signal emission vs. file handle leak).
    - `c_2`: no (conf 0.93) — The human comment is about a test file, saying something shouldn't be tested in that test. The candidate flags a resource-leak concern in urlmarks.py reload(). Different files and unrelated concerns.
    - `c_3`: no (conf 0.97) — The human comment is about a test missing a qtbot.wait_signal wrapper to verify signal emission. The candidate flags a resource-leak concern in reload() in urlmarks.py. Different files, different concerns entirely.
    - `c_4`: no (conf 0.95) — The human comment is a test-file suggestion about using a different domain in a test to verify existing marks are cleared. The candidate flags a resource-leak concern in urlmarks.py reload(). Different files and unrelated concerns.

---
## pipecat__2792  (judge: claude, key `ef696195`)

**Human comments:**
- `c_1` CHANGELOG.md:12 — Is `Nano Banana` a public term?
- `c_2` examples/foundational/07n-interruptible-gemini-image.py:None — Recommended: Swap to GoogleTTSService for faster performance.
- `c_3` examples/foundational/07n-interruptible-gemini-image.py:None — We'll need to modify this prompt too to remove the Gemini TTS "IMPORTANT" guidance.
- `c_4` examples/foundational/07n-interruptible-gemini-image.py:None — I think you can remove `twilio` as an option here.
- `c_5` examples/foundational/07n-interruptible-gemini-image.py:57 — Add the video out dimensions to avoid distorting the image. ```suggestion video_out_enabled=True, video_out_width=1024, video_out_height=1024, ```
- `c_6` examples/foundational/07n-interruptible-gemini-image.py:65 — Add video_out_* params here. ```suggestion audio_out_enabled=True, video_out_enabled=True, video_out_width=1024, video_out_height=1024, ```

**Judge issues → matcher verdicts:**
- [0] src/pipecat/services/google/llm.py:938 — image.tobytes() is called without first converting the image to RGB mode, so if the returned image is not already RGB (e.g., has an alpha channel), the raw bytes will not match the hardcoded format="RGB", producing corrupted OutputImageRawFrame data.
  → **no match**
    - `c_1`: no (conf 0.98) — The human comment questions terminology in CHANGELOG.md ('Nano Banana' branding/public term), while the candidate flags a technical image format bug in llm.py. Completely different concerns and locations.
    - `c_2`: no (conf 0.97) — The human comment is a suggestion in an example file to switch TTS services for performance. The candidate flags an image RGB conversion bug in llm.py. Different files, different concerns.
    - `c_3`: no (conf 0.97) — The human comment is about updating a prompt in an example file to remove Gemini TTS guidance. The candidate issue is about image RGB conversion in the LLM service code. Completely different concerns and locations.
    - `c_4`: no (conf 0.98) — The human comment is about removing 'twilio' as a transport option in an example file. The candidate flags an unrelated technical issue about image RGB conversion in the LLM service file. Different locations and completely different concerns.
    - `c_5`: no (conf 0.90) — The human comment asks to add video output dimensions in the example file to avoid image distortion. The candidate flags a different issue in a different file (llm.py) about image color mode conversion / RGB bytes mismatch. Both are loosely about image rendering correctness, but they are distinct concerns in different code locations.
    - `c_6`: no (conf 0.93) — The human comment asks to add video_out_* transport params in the example file so images can be rendered. The candidate flags a different issue in llm.py about image RGB conversion/tobytes format mismatch. Different files, different concerns.
- [1] src/pipecat/services/google/llm.py:79 — Monkeypatching genai._api_client.READ_BUFFER_SIZE at module import time is a global mutable state change acknowledged as a 'temporary hack' with no guard against future google-genai internal API changes.
  → **no match**
    - `c_1`: no (conf 0.98) — The human comment asks about terminology in CHANGELOG.md ('Nano Banana' being a public term), while the candidate flags a monkeypatch of google-genai internals in llm.py. Completely different locations and concerns.
    - `c_2`: no (conf 0.95) — The human comment suggests swapping TTS service in an example file for performance; the candidate flags a monkeypatch of genai internals in llm.py. Different files, different concerns.
    - `c_3`: no (conf 0.97) — The human comment is about updating a prompt in an example file to remove Gemini TTS guidance. The candidate flags monkeypatching of genai internals in llm.py — completely different file and concern.
    - `c_4`: no (conf 0.97) — The human comment is about removing 'twilio' as an option in an example file, while the candidate issue is about monkeypatching genai internals in the service LLM file. Completely different files and concerns.
    - `c_5`: no (conf 0.97) — The human comment is about missing video output dimensions in an example file causing image distortion. The candidate flags a monkeypatch of genai internals in the LLM service file - entirely different location and concern.
    - `c_6`: no (conf 0.97) — The human comment asks for video_out_* transport params in an example file; the candidate flags a monkeypatch of genai internals in the LLM service file. Different locations and entirely unrelated concerns.
- [2] src/pipecat/services/google/llm.py:0 — No new or updated tests were added to cover the new image-generation handling path (inline_data branch).
  → **no match**
    - `c_1`: no (conf 0.97) — The human comment questions terminology in CHANGELOG.md ('Nano Banana' naming), while the candidate flags missing tests for image-generation handling in llm.py. Different locations and entirely different concerns.
    - `c_2`: no (conf 0.97) — The human comment suggests swapping TTS service in an example file for performance; the candidate flags missing tests for image-generation handling in llm.py. Different files, different concerns entirely.
    - `c_3`: no (conf 0.96) — The human comment is about updating a prompt in an example file to remove Gemini TTS guidance. The candidate flags missing tests for the inline_data image-generation path in llm.py. Different files, different concerns.
    - `c_4`: no (conf 0.98) — The human comment is about removing a 'twilio' option in an example file; the candidate is about missing tests for image-generation handling in llm.py. Different files and entirely unrelated concerns.
    - `c_5`: no (conf 0.97) — The human comment concerns missing video output dimensions in an example file to avoid image distortion. The candidate flags missing tests in a different file (llm.py). Completely different concerns and locations.
    - `c_6`: no (conf 0.97) — The human comment asks for adding video_out_* transport params in an example file. The candidate flags lack of tests for the inline_data image handling in llm.py — entirely different concern and location.

---
## altair__3936  (judge: claude, key `d5fb4262`)

**Human comments:**
- `c_1` altair/vegalite/v6/api.py:5315 — Ref https://github.com/vega/altair/pull/3936#issuecomment-3765042428

**Judge issues → matcher verdicts:**
- [0] altair/vegalite/v6/api.py:5315 — The error message in remove_prop no longer includes the actual conflicting values, reducing diagnostic usefulness compared to before.
  → **no match**
    - `c_1`: no (conf 0.55) — The human comment contains no substantive description \u2014 it is only a link to an external PR comment, so there is no stated concern to compare against. The candidate flags a specific issue (error message losing conflicting values) at the same line, but matching on location alone is insufficient and the human text provides nothing verifiable.
- [1] pyproject.toml:163 — Ruff lint config changes (disabling PLC2801, PLR6201, PLW1514, and preview mode) are unrelated to the stated purpose of fixing type annotations, indicating some scope creep.
  → **no match**
    - `c_1`: no (conf 0.90) — The human comment points to a specific line in altair/vegalite/v6/api.py referencing an external discussion, while the candidate flags unrelated Ruff lint config changes in pyproject.toml as scope creep. Different files and different concerns.

---
## node-postgres__3547  (judge: claude, key `98fc8da2`)

**Human comments:**
- `c_1` packages/pg/lib/connection-parameters.js:10 — Original expression used truthiness: ```suggestion if (config[key]) { ```
- `c_2` packages/pg/lib/index.js:44 — Or `require('./native')` failed. The `try` should only cover the `process.env` access (if we actually want to do it this way at all).
- `c_3` packages/pg/lib/index.js:46 — If I am reading this right, if you are in a deno environment with no --allow-env, then the above will always error, and forceNative will always remain in its default of false, and so it will be impossible to use the native driver. I'm not sure how much of a dealbreaker this actually is (eg does the 
- `c_4` packages/pg/lib/defaults.js:3 — maybe say explicitly `let user = undefined`? I know they behave the same, but semantically this bare `let user` (incorrectly) implies to me that we expect to always set it to a value.

**Judge issues → matcher verdicts:**
- [0] packages/pg/lib/index.js:40 — NODE_PG_FORCE_NATIVE check changed from `typeof process.env.NODE_PG_FORCE_NATIVE !== 'undefined'` to `!!process.env.NODE_PG_FORCE_NATIVE`, so setting the env var to an empty string (which previously forced the native module) now silently falls back to the pure JS client, a behavioral regression.
  → **no match**
    - `c_1`: no (conf 0.78) — The human comment concerns connection-parameters.js line 10, where a truthiness check was altered; the candidate flags a different file/site (index.js NODE_PG_FORCE_NATIVE env check). Although both involve truthiness vs. undefined semantics introduced by the same PR, they point at distinct code changes, so the candidate did not identify the reviewer's specific concern.
    - `c_2`: no (conf 0.85) — The human comment concerns the scope of the try/catch: it wraps `require('./native')` so a native-module failure is silently swallowed, and the try should only cover the `process.env` access. The candidate instead flags a semantic change in the env-var truthiness check (`typeof ... !== 'undefined'` vs `!!`) affecting empty-string values. Same code region but a distinct concern; the candidate does not point at the error-swallowing/try-scope problem.
    - `c_3`: no (conf 0.70) — Both comments concern the NODE_PG_FORCE_NATIVE detection logic in the same block, but they identify distinct bugs. The human is worried that in Deno without --allow-env, accessing process.env throws and the try/catch swallows it, so forceNative can never be enabled. The candidate flags an unrelated truthiness regression (empty-string env var no longer forcing native) and never mentions the Deno permission/error-swallowing concern. Same code area, but different root causes and no indication the judge noticed the reviewer's actual worry.
    - `c_4`: no (conf 0.97) — The human comment is a style/semantics nitpick about declaring `let user` without explicit `undefined` in defaults.js. The candidate flags a behavioral regression in index.js about NODE_PG_FORCE_NATIVE truthiness checks. Different files and completely unrelated concerns.
- [1] packages/pg/lib/defaults.js:10 — Description states the default `user` value should be hardcoded to `'postgres'`, but the diff instead preserves the original `process.env.USER`/`USERNAME` logic wrapped in try/catch, contradicting the stated purpose of avoiding environment variable requirement for the user default.
  → **no match**
    - `c_1`: no (conf 0.90) — The human comment is about connection-parameters.js line 10, noting a change from truthiness check (`if (config[key])`) to something else. The candidate flags defaults.js line 10 about the `user` default env var logic — a different file and a different concern. Not the same issue.
    - `c_2`: no (conf 0.85) — The human comment concerns index.js:44, where a try block too broadly wraps both a process.env access and require('./native'), masking require failures. The candidate flags defaults.js:10 about the `user` default not being hardcoded to 'postgres' despite the PR description. Different file, different code, and a different underlying concern (semantics of the default value vs. overly broad try/catch masking module load errors). Only a loose thematic link via try/catch around process.env.
    - `c_3`: no (conf 0.80) — The human comment is about index.js:46, where a try/catch around env access means forceNative stays false in Deno without --allow-env, making the native driver unusable. The candidate flags a different location (defaults.js:10) about the `user` default preserving process.env logic in try/catch, contradicting the PR description. Both concern env-var access wrapped in try/catch in this Deno-compat PR, but they address different variables and different concerns (native driver inaccessibility vs. default user value not matching description). Not the same issue.
    - `c_4`: no (conf 0.85) — The human comment is a style/semantics nitpick about declaring `let user` without explicit `undefined`. The candidate flags a functional/behavioral discrepancy: that the user default still uses env vars instead of hardcoded 'postgres'. These are different concerns, even though both touch the user default code region.
- [2] packages/pg/lib/index.js:55 — The lazy `native` getter is now always defined on module.exports even when `forceNative` is true, whereas previously it was only defined when NODE_PG_FORCE_NATIVE was unset, introducing redundant/inconsistent behavior versus the prior all-or-nothing branching.
  → **no match**
    - `c_1`: no (conf 0.96) — The human comment concerns a truthiness vs. explicit check in connection-parameters.js line 10, while the candidate flags a lazy native getter definition in index.js line 55. Different files, different lines, different concerns.
    - `c_2`: no (conf 0.83) — The human comment concerns the try/catch being too broad equire./native')` failures get swallowed, so the try should only wrap the process.env access. The candidate instead complains that the lazy `native` getter is always defined even when forceNative is true, calling it redundant/inconsistent. These are different concerns about nearby code; the candidate does not flag the error-swallowing/try-scope problem.
    - `c_3`: no (conf 0.83) — The human comment concerns the env-access error path in Deno (no --allow-env) causing forceNative to always be false, making native driver unusable. The candidate flags a structural/redundancy concern about the lazy getter always being defined even when forceNative is true. Both are near the same code region but address different concerns: one is about env permission errors preventing native use, the other about redundant getter definition. Not the same underlying problem.
    - `c_4`: no (conf 0.98) — The human comment is a style nitpick about explicitly declaring `let user = undefined` in defaults.js:3. The candidate issue concerns a lazy `native` getter behavior in index.js:55 - entirely different file and unrelated concern.

---
## openbao__1906  (judge: claude, key `f547f680`)

**Human comments:**
- `c_1` changelog/1906.txt:None — ```suggestion core/leases: lease lookup will now include `path`, `namespace_path` and `revoke_error` ```

**Judge issues → matcher verdicts:**
- [0] vault/logical_system.go:2200 — revoke_error from leaseEntry is now exposed via the lease lookup API response without redaction, which the PR author themselves flags as a possible sensitive-data leak (and it is also already logged).
  → **no match**
    - `c_1`: no (conf 0.85) — The human comment is a changelog wording suggestion for changelog/1906.txt, listing fields exposed in lease lookup. The candidate flags a potential sensitive data leak by exposing revoke_error in the lease lookup API in vault/logical_system.go. These are different concerns: documentation/changelog wording vs. security of exposing a field. Not a match.
- [1] vault/logical_system_test.go:1225 — New test only asserts the 'path' field; the newly added 'namespace_path' and 'revoke_error' fields are not covered by any test.
  → **no match**
    - `c_1`: no (conf 0.85) — The human comment is a changelog wording suggestion, asking the changelog entry to mention `path`, `namespace_path` and `revoke_error`. The candidate flags missing test coverage for namespace_path and revoke_error in a test file. Both mention the same fields, but the underlying concerns differ (changelog text vs. test coverage) and locations are unrelated. Not the same issue.

---
## agents__4713  (judge: gpt, key `cef83a97`)

**Human comments:**
- `c_1` livekit-agents/livekit/agents/beta/workflows/warm_transfer.py:133 — should we allow a filter parameter here like `chat_ctx.messages(roles=["user", "assistant"])`

**Judge issues → matcher verdicts:**
- [0] livekit-agents/pyproject.toml:11 — Changing `requires-python` to `<3.14` makes the package uninstallable on Python 3.14 even though the previous published constraint supported that runtime, creating an unexplained compatibility regression.
  → **no match**
    - `c_1`: no (conf 0.98) — The human comment asks about adding a filter parameter to a chat context messages API in warm_transfer.py; the candidate flags a Python version constraint in pyproject.toml. Entirely different locations and concerns.

---
## vitest__9521  (judge: gpt, key `c21a90d1`)

**Human comments:**
- `c_1` packages/vitest/src/node/core.ts:None — I think this logic should be here instead: https://github.com/vitest-dev/vitest/blob/7ce3417b1be71689a784cc7a717bd0bce18e39a3/packages/vitest/src/node/coverage.ts#L77
- `c_2` packages/vitest/src/node/coverage.ts:352 — Filtering at this point will be more expensive than filtering before remapping is done, e.g. in `isIncluded`.
- `c_3` packages/vitest/src/node/types/coverage.ts:None — ```suggestion ```
- `c_4` test/coverage-test/test/query-param-transforms.test.ts:None — Oh good catch! Looks like this is also broken for existing `{ test: { changed: 'HEAD' } }`. I'll extend the test to cover both options. 💯
- `c_5` packages/vitest/src/node/coverage.ts:None — Is this if-else order correct? From the test `coverage.changed inherits from test.changed but can be overridden`, it looks like `this.options.changed` should be respected over `this.ctx.config.changed`.
- `c_6` test/coverage-test/test/changed.test.ts:None — Add test for https://github.com/vitest-dev/vitest/pull/9521#discussion_r2810335643 and apply fix if needed.

**Judge issues → matcher verdicts:**
- [0] packages/vitest/src/node/cli/cli-config.ts:309 — `argument: '<commit/branch>'` makes a value mandatory, so the documented bare boolean invocation `--coverage.changed` fails instead of setting the boolean option to `true` (despite the declared `boolean | string` type and boolean transform).
  → **no match**
    - `c_1`: no (conf 0.92) — The human comment is about code placement (logic should be moved from core.ts to coverage.ts), while the candidate flags a CLI argument declaration issue in cli-config.ts making a value mandatory. Different files, different concerns.
    - `c_2`: no (conf 0.97) — The human comment concerns performance of filtering placement in coverage.ts (filter before remapping). The candidate flags a CLI option argument declaration issue in cli-config.ts. Different files, different concerns entirely.
    - `c_3`: no (conf 0.90) — The human comment is a bare suggestion block with no substantive text, in a different file (types/coverage.ts). Per instructions, no substantive text means answer false.
    - `c_4`: no (conf 0.66) — The human comment is about the `changed` option handling being broken for a string value (`{ test: { changed: 'HEAD' } }`) in the query-param transform code/tests, and about extending tests to cover both options. The candidate instead flags the CLI config declaration (`argument: '<commit/branch>'`) making a value mandatory so a bare `--coverage.changed` boolean flag fails. Both touch the `changed` option's boolean|string duality, but they concern different mechanisms (CLI arg parsing vs. query param serialization/transform) and different failure modes (boolean form failing in CLI vs. string form broken in transforms). Not the same underlying problem the reviewer was addressing.
    - `c_5`: no (conf 0.90) — The human comment concerns precedence order in an if-else in coverage.ts (coverage.changed vs test.changed). The candidate flags a CLI argument declaration issue in cli-config.ts about requiring a value for --coverage.changed. Different files and different concerns (precedence logic vs CLI arg parsing).
    - `c_6`: no (conf 0.70) — The human comment merely asks to add a test in test/coverage-test/test/changed.test.ts referencing an external discussion link, with no substantive description of the underlying issue. The candidate flags a specific CLI option definition problem (mandatory argument for --coverage.changed) in a different file. Without evidence the linked discussion concerns that CLI argument issue, and given the human comment lacks substantive content, this cannot be counted as a match.

---
## effect__5952  (judge: gpt, key `c3d1e698`)

**Human comments:**
- `c_1` packages/opentelemetry/package.json:None — I think just get rid of all the optional deps
- `c_2` .changeset/move-sdk-to-subpath-exports.md:None — ```suggestion "@effect/opentelemetry": minor ```

**Judge issues → matcher verdicts:**
- [0] packages/opentelemetry/package.json:65 — Removing the whole `peerDependenciesMeta` block also makes `@opentelemetry/api`, `resources`, `sdk-metrics`, `sdk-trace-base`, and `sdk-logs` required peers, so consumers that previously omitted these optional packages can receive unmet-peer/install failures even though the stated fix only requires the node and web trace SDKs.
  → **matched `c_1`**
    - `c_1`: match (conf 0.70) — Both comments concern the same code: the peerDependenciesMeta / optional peer dependency markers in packages/opentelemetry/package.json. The human reviewer suggests removing all optional deps entirely; the candidate flags that removing the whole peerDependenciesMeta block makes those peers required. The diagnosis/recommendation is inverted, but the candidate identified exactly the contested code and the same underlying subject (which peer deps should remain optional), which counts as a lenient match.
    - `c_2`: no (conf 0.85) — The human comment is about the changeset file, suggesting the version bump for @effect/opentelemetry should be minor (rather than patch). The candidate issue is about removing peerDependenciesMeta in package.json making optional peers required. Different files and different concerns — though arguably both relate to the breaking nature of the change, the candidate does not flag the changeset bump level. Not a match.

---
## coreos-assembler__4359  (judge: gpt, key `981f31a5`)

**Human comments:**
- `c_1` mantle/kola/tests/misc/multipath.go:None — ![high](https://www.gstatic.com/codereviewagent/high-priority.svg) The output from `c.MustSSH` and `c.MustSSHf` can contain leading/trailing whitespace, including newlines. `strconv.Atoi` will fail to parse a string like `"2\n"`, causing the test to fail incorrectly. Also, `sudo multipath -l -v 1` m
- `c_2` mantle/platform/qemu.go:None — ![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg) The indentation in this new function uses spaces, while the rest of the file and Go standard practice is to use tabs. Please use tabs for indentation for consistency. ```go func (inst *QemuInstance) RemoveBlockDeviceForMultipath(
- `c_3` mantle/kola/tests/misc/multipath.go:None — Let's add more info here, if someone see this issue it has a tip to where to look at, maybe we can also do something like it what you are doing with the `c.RunCmdSync(m, "grep mpath.wwid= /proc/cmdline")` c.Fatalf( "Reboot failed: %v. Likely caused by multipath not booting with only one remaining pa

**Judge issues → matcher verdicts:**
- [0] src/cosalib/fedora_messaging_request.py:197 — twisted_consume was previously treated as a single Deferred, so iterating that unresolved Deferred instead of attaching callbacks to it will repeatedly yield/fail before reactor.run and prevent the messaging consumer from starting.
  → **no match**
    - `c_1`: no (conf 0.99) — Completely different files and issues: human flags whitespace trimming/Atoi parsing in multipath test; candidate discusses Deferred handling in fedora_messaging_request.py.
    - `c_2`: no (conf 0.98) — The human comment is a style nitpick about tabs vs spaces in mantle/platform/qemu.go. The candidate flags a Deferred/iteration bug in a different Python file. Completely unrelated.
    - `c_3`: no (conf 0.98) — Completely different files and topics: human comment asks for a better error message in multipath kola test; candidate flags a Deferred iteration bug in fedora_messaging_request.py. No relation.

---
## espnet__6325  (judge: gpt, key `17f2b753`)

**Human comments:**
- `c_1` egs2/tal_zh_adult_teach/asr1/local/data.sh:None — ![critical](https://www.gstatic.com/codereviewagent/critical.svg) The `echo <<EOF` syntax is incorrect for printing a multi-line here-document. This will cause a syntax error and prevent the usage message from being displayed correctly. You should use `cat <<EOF` instead. ```suggestion cat <<EOF Usa
- `c_2` egs2/tal_zh_adult_teach/asr1/local/download_and_untar.sh:None — ![critical](https://www.gstatic.com/codereviewagent/critical.svg) The `echo <<EOF` syntax is incorrect for printing a multi-line here-document. This will cause a syntax error and prevent the usage message from being displayed correctly. You should use `cat <<EOF` instead. ```suggestion cat <<EOF Usa
- `c_3` egs2/tal_zh_adult_teach/asr1/run.sh:26 — usually, we can set these hyperparameters to default ones

**Judge issues → matcher verdicts:**
- [0] egs2/tal_zh_adult_teach/asr1/local/data.sh:35 — `local/data.sh` runs `cd "${TAL_ZH_ADULT_TEACH}"` before creating the default `downloads` directory, so first-time data preparation fails immediately instead of invoking the extractor.
  → **no match**
    - `c_1`: no (conf 0.93) — The human comment flags an incorrect `echo <<EOF` here-document syntax in the usage message. The candidate flags a different problem: a `cd` occurring before creating the default downloads directory. These are distinct concerns in the same file, not the same underlying issue.
    - `c_2`: no (conf 0.95) — The human comment flags an incorrect `echo <<EOF` heredoc syntax in download_and_untar.sh's usage message. The candidate flags a different file (data.sh) and a different problem (cd into non-existent directory before creating downloads dir). These are unrelated issues.
    - `c_3`: no (conf 0.95) — The human comment is about hyperparameters in run.sh line 26 being set to defaults - a configuration style suggestion. The candidate flags a bug in local/data.sh about directory creation ordering causing failure. Different files, different concerns entirely.
- [1] egs2/tal_zh_adult_teach/asr1/local/download_and_untar.sh:24 — The extractor calls `realpath` on `<extract-dir>` before `mkdir -p`; since `realpath` requires the path to exist, invoking the documented command with a new destination directory exits under `set -e`.
  → **no match**
    - `c_1`: no (conf 0.97) — The human comment flags an incorrect `echo <<EOF` heredoc syntax in local/data.sh. The candidate flags a different file (download_and_untar.sh) and a completely unrelated issue about `realpath` being called before `mkdir -p`. Different locations and different problems.
    - `c_2`: no (conf 0.93) — The human comment flags an incorrect `echo <<EOF` here-document syntax in the usage message. The candidate flags a different issue: `realpath` being called before `mkdir -p` causing failure for non-existent directories. These are distinct problems in the same file, not the same underlying issue.
    - `c_3`: no (conf 0.97) — The human comment concerns hyperparameters in run.sh that should be set to defaults; the candidate flags a realpath/mkdir ordering bug in download_and_untar.sh. Different files, unrelated concerns.
- [2] egs2/tal_zh_adult_teach/asr1/README.md:18 — The README's ASR-config link targets `./conf/train/train_asr_branchformer_e24_amp.yaml`, but the added configuration is at `conf/train_asr_branchformer_e24_amp.yaml`, leaving the documented link broken.
  → **no match**
    - `c_1`: no (conf 0.97) — The human comment flags incorrect `echo <<EOF` heredoc syntax in local/data.sh, while the candidate flags a broken link in README.md. Different files and entirely unrelated issues.
    - `c_2`: no (conf 0.98) — The human comment concerns a shell script syntax error (`echo <<EOF` vs `cat <<EOF`) in download_and_untar.sh. The candidate flags a broken documentation link in README.md. Different files, different issues.
    - `c_3`: no (conf 0.95) — The human comment concerns hyperparameters in run.sh that should be set to default values. The candidate flags a broken README link to the ASR config file. Different files, different concerns.

---
## espnet__6325  (judge: gpt, key `540d205e`)

**Human comments:**
- `c_1` egs2/tal_zh_adult_teach/asr1/local/data.sh:None — ![critical](https://www.gstatic.com/codereviewagent/critical.svg) The `echo <<EOF` syntax is incorrect for printing a multi-line here-document. This will cause a syntax error and prevent the usage message from being displayed correctly. You should use `cat <<EOF` instead. ```suggestion cat <<EOF Usa
- `c_2` egs2/tal_zh_adult_teach/asr1/local/download_and_untar.sh:None — ![critical](https://www.gstatic.com/codereviewagent/critical.svg) The `echo <<EOF` syntax is incorrect for printing a multi-line here-document. This will cause a syntax error and prevent the usage message from being displayed correctly. You should use `cat <<EOF` instead. ```suggestion cat <<EOF Usa
- `c_3` egs2/tal_zh_adult_teach/asr1/run.sh:26 — usually, we can set these hyperparameters to default ones

**Judge issues → matcher verdicts:**
- [0] egs2/tal_zh_adult_teach/asr1/local/data.sh:35 — `TAL_ZH_ADULT_TEACH=$(cd "${TAL_ZH_ADULT_TEACH}"; pwd)` runs before creating the default `downloads` directory, so `local/data.sh` fails immediately on a fresh checkout where that directory does not yet exist.
  → **no match**
    - `c_1`: no (conf 0.95) — The human comment flags an incorrect `echo <<EOF` heredoc syntax in the usage message. The candidate flags a different issue: directory resolution occurring before the downloads directory is created. Different concerns in the same file, unrelated problems.
    - `c_2`: no (conf 0.97) — The human comment flags an incorrect `echo <<EOF` heredoc syntax in download_and_untar.sh. The candidate flags a different issue in a different file (data.sh) about directory resolution before creation. Different code, different problem.
    - `c_3`: no (conf 0.95) — The human comment concerns hyperparameters in run.sh being set to defaults, while the candidate flags a directory-existence bug in local/data.sh. Different files and unrelated concerns.
- [1] egs2/tal_zh_adult_teach/asr1/local/download_and_untar.sh:25 — A supplied but nonexistent `--downloads_dir` contradicts the documented fallback behavior because `realpath ${2:-$extract_dir}` exits before the script can fall back to `extract_dir`.
  → **no match**
    - `c_1`: no (conf 0.95) — The human comment is about incorrect `echo <<EOF` heredoc syntax in local/data.sh's usage message. The candidate flags a different file (download_and_untar.sh) and a different issue about realpath failing on nonexistent downloads_dir. Different code, different problem.
    - `c_2`: no (conf 0.90) — The human comment flags a shell syntax error in the usage message (`echo <<EOF` should be `cat <<EOF`). The candidate flags a different issue: the fallback behavior for a nonexistent downloads dir failing due to realpath. Same file, different concerns.
    - `c_3`: no (conf 0.96) — The human comment concerns hyperparameters in run.sh being set to defaults, while the candidate flags a path fallback bug in download_and_untar.sh. Different files and entirely unrelated concerns.
- [2] egs2/tal_zh_adult_teach/asr1/README.md:18 — The README's ASR-config hyperlink targets `conf/train/train_asr_branchformer_e24_amp.yaml`, but the added configuration is at `conf/train_asr_branchformer_e24_amp.yaml`, leaving the documented link broken.
  → **no match**
    - `c_1`: no (conf 0.97) — The human comment concerns incorrect `echo <<EOF` heredoc syntax in local/data.sh; the candidate flags a broken README hyperlink path. Different files, different issues.
    - `c_2`: no (conf 0.98) — The human comment flags an incorrect `echo <<EOF` heredoc syntax in download_and_untar.sh, while the candidate flags a broken README hyperlink path. Different files, different issues entirely.
    - `c_3`: no (conf 0.95) — The human comment is about hyperparameters in run.sh that should use default values. The candidate flags a broken README hyperlink to the config file. Different files and unrelated concerns.

---
## node-postgres__3547  (judge: gpt, key `af4a9286`)

**Human comments:**
- `c_1` packages/pg/lib/connection-parameters.js:10 — Original expression used truthiness: ```suggestion if (config[key]) { ```
- `c_2` packages/pg/lib/index.js:44 — Or `require('./native')` failed. The `try` should only cover the `process.env` access (if we actually want to do it this way at all).
- `c_3` packages/pg/lib/index.js:46 — If I am reading this right, if you are in a deno environment with no --allow-env, then the above will always error, and forceNative will always remain in its default of false, and so it will be impossible to use the native driver. I'm not sure how much of a dealbreaker this actually is (eg does the 
- `c_4` packages/pg/lib/defaults.js:3 — maybe say explicitly `let user = undefined`? I know they behave the same, but semantically this bare `let user` (incorrectly) implies to me that we expect to always set it to a value.

**Judge issues → matcher verdicts:**
- [0] packages/pg/lib/connection-parameters.js:10 — `val()` still reads `process.env` for every absent config key, so constructing a connection with normal partial configuration (for example, omitting an optional parameter) still throws in Deno without --allow-env rather than falling back to defaults.
  → **no match**
    - `c_1`: no (conf 0.78) — The human comment flags a behavioral regression: the check should use truthiness (`if (config[key])`) as the original code did, rather than the new existence/undefined check. The candidate instead complains that `val()` still accesses `process.env` for absent keys, causing Deno permission errors — a different concern about env access completeness, not about the truthiness semantics of the config key check. Same line, unrelated issue.
    - `c_2`: no (conf 0.83) — The human comment concerns an overly broad try/catch in packages/pg/lib/index.js that would also swallow failures from require('./native'), suggesting the try should only wrap the process.env access. The candidate flags a different file (connection-parameters.js) about val() reading process.env causing throws in Deno without env permission. Both touch on process.env access issues broadly, but they identify different code and different problems; the candidate does not note the try/catch masking require('./native') failures.
    - `c_3`: no (conf 0.70) — The human comment is about packages/pg/lib/index.js:46 where env access errors in Deno without --allow-env cause forceNative to silently remain false, making the native driver unusable. The candidate flags a different file/line (connection-parameters.js val()) about process.env access throwing in Deno without --allow-env. Both concern Deno env-permission issues, but the specific concerns differ: the human worries about silently disabled native driver capability; the candidate worries about throwing on missing config keys. They are different code locations with different symptoms, though same general theme of Deno env access. This is a related-theme but distinct issue, not the same flagged code.
    - `c_4`: no (conf 0.95) — The human comment is a stylistic nitpick about declaring `let user` explicitly as `undefined` in defaults.js. The candidate raises a functional concern about `val()` reading process.env in connection-parameters.js causing Deno permission errors. Different files, different concerns.
- [1] packages/pg/lib/index.js:42 — Changing the force-native test from “environment variable is defined” to `!!process.env.NODE_PG_FORCE_NATIVE` means `NODE_PG_FORCE_NATIVE=''` no longer loads the native client, whereas it did before.
  → **no match**
    - `c_1`: no (conf 0.82) — Both concern a truthiness-vs-defined semantic change, but they point at different files and different code: the human comment is about `config[key]` in connection-parameters.js line 10, while the candidate flags the NODE_PG_FORCE_NATIVE env check in index.js line 42. These are distinct instances of a similar class of issue, not the same issue.
    - `c_2`: no (conf 0.82) — The human comment concerns the scope of the try/catch: it also swallows failures from `require('./native')`, and should only wrap the `process.env` access. The candidate instead flags a behavioral change in truthiness checking (`NODE_PG_FORCE_NATIVE=''` no longer forcing native). Although both touch the same few lines, they describe distinct problems — error masking vs. env-var truthiness semantics — so this is a location-only overlap.
    - `c_3`: no (conf 0.70) — Both comments target the new forceNative detection logic in packages/pg/lib/index.js, but they raise different problems. The human reviewer is concerned that in a Deno environment without --allow-env, accessing process.env throws, so forceNative stays false and the native driver can never be used. The candidate flags a semantics change where NODE_PG_FORCE_NATIVE='' (empty string) is now falsy and no longer loads the native client. The candidate says nothing about the Deno/permission error path that the human focused on; it's a distinct edge-case concern about truthiness rather than the thrown-error/permission scenario.
    - `c_4`: no (conf 0.97) — The human comment is a style/semantics nitpick about declaring `let user` vs `let user = undefined` in defaults.js. The candidate flags a behavioral change in index.js about NODE_PG_FORCE_NATIVE truthiness. Different files, different concerns entirely.

---
## espnet__6356  (judge: gpt, key `9c1d0811`)

**Human comments:**
- `c_1` espnet2/text/whisper_token_id_converter.py:None — ![high](https://www.gstatic.com/codereviewagent/high-priority.svg) The current logic rebuilds the list of special tokens by concatenating existing `extra_special_tokens` with new `timestamps` and `sc` tokens, and then passes this entire list to `add_special_tokens`. While this works because `add_spe
- `c_2` espnet2/text/whisper_tokenizer.py:None — ![high](https://www.gstatic.com/codereviewagent/high-priority.svg) The current logic rebuilds the list of special tokens by concatenating existing `extra_special_tokens` with new `timestamps` and `sc` tokens, and then passes this entire list to `add_special_tokens`. While this works because `add_spe

**Judge issues → matcher verdicts:**
- [0] espnet2/ps2st/qwen2_scorer.py:55 — `past_kv.layers[0].get_seq_length()` is a v5 cache API, so with Transformers v4's non-None tuple/list `past_key_values` this raises `AttributeError`, despite the comment claiming support for both versions.
  → **no match**
    - `c_1`: no (conf 0.98) — Different files and entirely different concerns: human flags redundant re-adding of special tokens in whisper_token_id_converter.py; candidate flags a cache API version incompatibility in qwen2_scorer.py.
    - `c_2`: no (conf 0.97) — Different files and entirely different concerns: human comment is about redundant special token list rebuilding in whisper_tokenizer.py; candidate is about cache API version incompatibility in qwen2_scorer.py.
- [1] espnet2/text/whisper_tokenizer.py:94 — The v4 branch no longer includes the tokenizer's existing `additional_special_tokens`; because `add_special_tokens` replaces that list by default, it drops previously registered Whisper special tokens such as language/task tokens from the additional-special-token set.
  → **matched `c_2`**
    - `c_1`: no (conf 0.68) — The human comment targets whisper_token_id_converter.py, objecting that the code needlessly re-concatenates existing extra_special_tokens when calling add_special_tokens (a style/efficiency point, noting it still works since the call is idempotent). The candidate flags a different file/line (whisper_tokenizer.py:94) and asserts the opposite functional problem: that existing additional_special_tokens are omitted and thus dropped. Different code snippet and essentially inverted concern, so not the same issue the reviewer raised.
    - `c_2`: match (conf 0.60) — Both comments target the same `add_special_tokens(dict(extra_special_tokens=...))` call in whisper_tokenizer.py and both concern whether the existing special tokens should be included/concatenated in that call. The human says including them is redundant and only new tokens should be added; the candidate says omitting them drops previously registered tokens. The diagnoses/recommendations are opposite, but they flag the same contested code and the same underlying semantics of add_special_tokens replacing vs. adding, which the leniency guidance accepts.
