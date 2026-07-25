# Verbosity rewrite spot-check (v1)

Random 20% sample (24 of 120 rewrites) for manual
semantic-leakage review (spec §4.2). Check: no fact added or dropped vs baseline.

## agents__4846 — verb_pad2x

**Baseline description:**

```
if there's a crash earlier on in the session, we do not correctly upload logs to the server. this makes it difficult to troubleshoot.

we'll always upload crash logs but still honor user-specified record settings.
```

**Rewritten description:**

```
If there happens to be a crash earlier on in the course of the session, we currently do not correctly upload the logs to the server the way we should. Because those logs never make it up, this whole situation makes it much more difficult to troubleshoot what actually went wrong. To fix that, from now on we will always upload the crash logs, while at the same time we will still continue to honor whatever record settings the user has specified.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## chia-blockchain__20099 — verb_pad4x

**Baseline description:**

```
Big changes:
- `Union` types ~are no longer~ will soon not be supported through Ruff.  Use `A | B` or `A | None` for `Optional[A]`
- `kw_only` is now a supported option across all versions for dataclasses! Probably a good idea to consider this as the default.
```

**Rewritten description:**

```
Big changes:
- `Union` types ~are no longer~ will soon not be supported when going through Ruff, which means that from this point onward the recommended approach is to instead write things out in the form `A | B`, and in the specific situation where you previously would have reached for `Optional[A]` you should now use the equivalent `A | None` spelling in its place instead
- `kw_only` is at this point now a fully supported option, and importantly it is supported uniformly across every single one of the versions, whenever you happen to be doing any work with dataclasses! In light of that broad availability across the board, it is very probably a genuinely good idea for us to go ahead and give some serious thought to the real possibility of considering, and then actually going and adopting, this particular option to serve as the default choice going forward from here.
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

## coreos-assembler__4359 — verb_pad4x

**Baseline description:**

```
Reduce disk on multipath via qmp, then reboot.
`{ "execute": "device_del", "arguments": { "id": "/machine/peripheral-anon/device[3]"}}`

See https://issues.redhat.com/browse/OCPBUGS-56597
```

**Rewritten description:**

```
In order to reduce the amount of disk that is on a multipath setup, the approach here is to use qmp so as to run the specific command that is shown just below, and then, once that step is done, to go ahead and reboot the machine afterward as the final step: `{ "execute": "device_del", "arguments": { "id": "/machine/peripheral-anon/device[3]"}}` For any further details and additional context on this, please see the associated tracking issue, which can be found over at https://issues.redhat.com/browse/OCPBUGS-56597
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## dask__12106 — verb_pad2x

**Baseline description:**

```
Improves on #12105 by using the shard shape as the `previous_chunks` parameter instead of `chunks`. This results in rechunking with with larger chunks that are still shard-aligned. Thanks to @dcherian for reminding me that `auto_chunks` nearly always concatenates the `previous_chunks` argument.

But not always. This change brings the possibility of shard-misaligned chunks if the global configuration declares a memory limit smaller than the shard size. What should we do when there's competition between the global config and shard shape of the zarr array? Would an exception be appropriate here, prompting the user to change the config?
```

**Rewritten description:**

```
This improves on #12105 by taking the shard shape and using it as the `previous_chunks` parameter, rather than using `chunks` for that role as before. The effect of doing it this way is that the rechunking ends up producing larger chunks which are nevertheless still shard-aligned. Thanks are due to @dcherian for reminding me of the fact that `auto_chunks` nearly always ends up concatenating the `previous_chunks` argument that it is given. But that is not something that happens every single time. Because of that, this change introduces the possibility of chunks that are shard-misaligned, specifically in the case where the global configuration declares a memory limit that is smaller than the shard size itself. So what exactly should we do in the situation where there is competition between the global config on one side and the shard shape of the zarr array on the other? Would raising an exception be the appropriate response here, one that prompts the user to go and change their config?
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## deepchem__4601 — verb_pad4x

**Baseline description:**

```
## Description

Fix #(issue)

<!-- Please include a summary of the change and which issue is fixed.
Please also include relevant motivation and context.
List any dependencies that are required for this change. -->


## Type of change

Please check the option that is related to your PR.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - In this case, we recommend to discuss your modification on GitHub issues before creating the PR
- [ ] Documentations (modification for documents)

## Checklist

- [ ] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
  - [ ] Run `yapf -i <modified file>` and check no errors (**yapf version must be  0.32.0**)
  - [ ] Run `mypy -p deepchem` and check no errors
  - [ ] Run `flake8 <modified file> --count` and check no errors
  - [ ] Run `python -m doctest <modified file>` and check no errors
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New unit tests pass locally with my changes
- [ ] I have checked my code and corrected any misspellings
```

**Rewritten description:**

```
## Description

Fix #(issue)

<!-- Please include a summary of the change and which issue is fixed.
Please also include relevant motivation and context.
List any dependencies that are required for this change. -->

## Type of change

Please, if you would be so kind, take a brief moment out of your time to go ahead and carefully check off the one single option that is listed down below here in this section, namely the specific one among all of them that happens to be the particular option which is genuinely and directly related to your own particular PR here in this specific instance of yours.

- [ ] Bug fix (this particular one here is a non-breaking sort of change, which is another way of saying that it is a change which simply goes ahead and fixes some already-existing issue that happened to be present beforehand)
- [ ] New feature (this particular one here is, in much the same way, a non-breaking sort of change as well, which is another way of saying that it is a change which goes ahead and adds some brand-new functionality on top of what already exists)
- [ ] Breaking change (this one would be either a fix or else instead a feature, but specifically one that would end up having the consequence of causing the existing functionality to no longer continue working in the particular manner that it is currently expected by everyone to work in)
  - In this specific situation right here, the thing that we would go ahead and recommend to you is that you should first take the time to discuss your intended modification over on the GitHub issues page, and that you do this well in advance of the point at which you go and actually create the PR itself
- [ ] Documentations (this one refers to a modification that is being carried out specifically and deliberately for the express sake of the documents themselves)

## Checklist

- [ ] My code follows [the style guidelines of this project](https://deepchem.readthedocs.io/en/latest/development_guide/coding.html)
  - [ ] Please go ahead and run `yapf -i <modified file>`, and then, once that has finished, carefully check over everything to confirm that there are no errors at all present (**the yapf version that you have installed and use here absolutely must be exactly 0.32.0**)
  - [ ] Please go ahead and run `mypy -p deepchem`, and then, once that has fully finished running, carefully check back over everything that it printed in order to confirm for yourself that there are no errors at all present or reported anywhere in its output
  - [ ] Please go ahead and run `flake8 <modified file> --count`, and then, once that has fully finished running, carefully check back over everything that it printed in order to confirm for yourself that there are no errors at all present or reported anywhere in its output
  - [ ] Please go ahead and run `python -m doctest <modified file>`, and then, once that has fully finished running, carefully check back over everything that it printed in order to confirm for yourself that there are no errors at all present or reported anywhere in its output
- [ ] I have personally gone ahead and performed a full, careful, and thorough self-review of the entirety of my own code, reading through the whole of it line by line all by myself before submitting anything
- [ ] I have gone through and added explanatory comments to my code, and I made a deliberate point of doing this particularly within those specific areas of the code that happen to be especially difficult and hard-to-understand for a reader coming to it fresh
- [ ] I have gone ahead and made all of the various corresponding changes over to the project documentation as well, so that the documentation stays properly in sync with the behavior of the code as it now stands
- [ ] I have added in a set of tests, specifically ones that go on to actually prove and clearly demonstrate that the fix I have made here is genuinely and reliably effective, or else, in the alternative, that my newly added feature really and truly does work in the way that it is meant to
- [ ] Every single last one of the new unit tests passes successfully in a local run on my own machine, each of them coming back green when they are all run together with the entirety of my changes applied on top of everything
- [ ] I have gone all the way back through and very carefully checked over the whole of my code from beginning to end, and in doing so I have corrected each and every single one of the misspellings that I happened to come across at any point anywhere along the way
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## linkding__1261 — verb_pad4x

**Baseline description:**

```
The rest of the links on this page are absolute paths without a specified hostname, but these in particlar use
build_absolute_uri. I am running linkding behind two different load balancers which makes these links bubble up the "internal" hostname instead of the hostname I actually got to the page from.
```

**Rewritten description:**

```
The whole of the rest of the links that happen to be found sitting on this particular page are, as it turns out, absolute paths, and they are ones which do not have any sort of specified hostname attached onto them at all, but then these particular links right here are very much the exception to that, and the reason for that is because they instead go and make use of build_absolute_uri in order to do their thing. The overall situation that is going on here is that I myself happen to be running my linkding instance in such a way that it sits behind two entirely different load balancers, one and then another, and it is precisely this particular kind of setup which is the thing that ends up making these particular links go and bubble all the way up the "internal" hostname, rather than instead going and showing off the actual real hostname that I genuinely did use in order to get myself to the page in the very first place to begin with.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## litgpt__2188 — verb_pad2x

**Baseline description:**

```
## What does this PR do?
This PR adds a `generate_strategy` option to the `litgpt serve` command. This allows users to explicitly specify the generation strategy (e.g., `"sequential"`, `"tensor_parallel"`) when initializing the model for serving.

## Motivation
Previously, the `generate_strategy` was hardcoded to `"sequential"` in `serve.py` when verifying `devices > 1`, giving users no option to choose alternative strategies like `"tensor_parallel"` which might be preferred for certain deployments.

## Who can review this?
@bhimrazy 
Anyone from the community is free to review once the tests are passed.
```

**Rewritten description:**

```
## What does this PR do?
This particular PR goes ahead and adds a brand new `generate_strategy` option onto the `litgpt serve` command. What this then allows is for users to be able to explicitly specify the generation strategy that they want (as some examples, `"sequential"`, or `"tensor_parallel"`) at the point when they are initializing the model for the purpose of serving it.

## Motivation
Up until now, the `generate_strategy` had been hardcoded so that it was set to `"sequential"` over in `serve.py`, specifically at the point of verifying that `devices > 1`, and this ended up giving users no option at all to go and choose alternative strategies such as `"tensor_parallel"`, which is the kind of thing that might well be preferred for certain deployments.

## Who can review this?
@bhimrazy
Anyone at all from the community is free to go ahead and review this once the tests have been passed.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## numba__10276 — verb_terse

**Baseline description:**

```
First contribution to numba, would appreciate all feedback.

Resolves #10270.
```

**Rewritten description:**

```
First numba contribution; feedback appreciated. Resolves #10270.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## numba__10366 — verb_terse

**Baseline description:**

```
Closes #7369 

The helper `normalize_axis_tuple` could be an overload for `numpy.lib.array_utils.normalize_axis_tuple`, do you want it to be? I think it only has that location/ public API since numpy 2.x, not sure if numba minds that.
```

**Rewritten description:**

```
Closes #7369

`normalize_axis_tuple` could overload `numpy.lib.array_utils.normalize_axis_tuple` — want that? That public API only exists since numpy 2.x; unsure if numba minds.
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

## protocompile__630 — verb_terse

**Baseline description:**

```
This fixes EOF lookups for `InverseLocation`. Currently this will panic as any `LineOffset` requires a trailing newline. We now use the EOF as the end of line for the last line.

Fixes https://github.com/bufbuild/vscode-buf/issues/478#issuecomment-3541151881
```

**Rewritten description:**

```
Fixes `InverseLocation` EOF lookups, panicking since `LineOffset` needs trailing newline; now uses EOF as last line's end.

Fixes https://github.com/bufbuild/vscode-buf/issues/478#issuecomment-3541151881
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## prowler__9606 — verb_pad4x

**Baseline description:**

```
### Context

The current implementation of the AWS Bedrock service in Prowler only fetches the first page of results for Guardrails and Agents. This limitation means that in environments with a large number of these resources (exceeding the default AWS page size), Prowler fails to detect and scan all of them, leading to incomplete security assessments.

### Description

This PR implements proper pagination logic for the [list_guardrails](cci:1://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:54:4-84:13) and [list_agents](cci:1://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:143:4-177:13) methods in [bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0).

Changes include:
- Updated [[prowler/providers/aws/services/bedrock/bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/prowler/providers/aws/services/bedrock/bedrock_service.py) logic to iterate through all available pages of results using the `nextToken` provided by the AWS API.
- Added a new unit test file [[tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py](cci:7://file:///prowler/tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py) to verify that the pagination logic correctly collects resources across multiple pages.
- Added inline documentation to the code to explain the pagination flow and loop mechanics.

### Steps to review

1.  **Code Review**: Verify changes in [[prowler/providers/aws/services/bedrock/bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/prowler/providers/aws/services/bedrock/bedrock_service.py). Ensure the `while True` loops correctly handle the `nextToken` for both Guardrails and Agents.
2.  **Test Verification**:
    - Run the new unit tests:
      ```bash
      poetry run pytest tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py
      ```
    - Run existing tests to ensure no regressions:
      ```bash
      poetry run pytest tests/providers/aws/services/bedrock/bedrock_service_test.py
      ```

### Checklist

- Are there new checks included in this PR? **No**
    - If so, do we need to update permissions for the provider? N/A
- [x] Review if the code is being covered by tests.
- [x] Review if code is being documented following this specification https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [ ] Review if backport is needed.
- [ ] Review if is needed to change the [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md)
- [x] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), if applicable.

#### UI
N/A

#### API
N/A

### License

By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.


closes https://github.com/prowler-cloud/prowler/issues/9607
```

**Rewritten description:**

```
### Context

The particular way and manner in which the AWS Bedrock service that lives inside of Prowler happens to be currently implemented at the present time is such that it only ever goes and fetches the very first single page of all of the results, and, what is more, it goes and does this very same thing for both the Guardrails resources on the one hand and also, equally, the Agents resources on the other hand. What this one particular limitation right here ends up actually meaning in practice is that, in any and all of those environments which happen to have within them a genuinely large number of these sorts of resources (that is to say, a number of them which ends up exceeding the default AWS page size that is set in place), Prowler will end up failing to properly detect and then, following on from that, to scan every last one of them in the way that it really should be doing, and this failure of it, in turn, goes on to lead quite directly to the production of security assessments that end up being incomplete and lacking.

### Description

What it is that this PR actually does is go right ahead and implement some proper, correct, and working pagination logic, and, importantly, it goes and does exactly that for both the [list_guardrails](cci:1://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:54:4-84:13) method on the one hand and also the [list_agents](cci:1://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:143:4-177:13) method on the other hand, both of which happen to live and reside inside of the [bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0) file.

Changes include:
- Updated the [[prowler/providers/aws/services/bedrock/bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/prowler/providers/aws/services/bedrock/bedrock_service.py) logic, doing so in such a way and to such a degree that it now goes and iterates its way carefully through each and every single one of the available pages of the results that there happen to be, and, importantly, it manages to do the whole of this specifically by making use of the `nextToken` value, that is, the very one that is handed to it and provided by the AWS API itself.
- Added in a brand new unit test file, namely the one called [[tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py](cci:7://file:///prowler/tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py), and this whole thing was done specifically in order to be able to properly verify and confirm that the pagination logic does, in point of actual fact, go and correctly collect up the full entirety of all of the resources, and, moreover, that it manages to do so right across each and every single one of the multiple different pages that there happen to be present.
- Added in some helpful inline documentation over into the body of the code itself, and this too was done quite specifically and deliberately in order to properly explain the whole of the pagination flow, along with all of the mechanics of how the loop itself works, and to do so for the benefit of whoever it happens to be that ends up reading over the code at some later point on down the line.

### Steps to review

1.  **Code Review**: Go right ahead and take the time to carefully verify the changes that were made over inside of [[prowler/providers/aws/services/bedrock/bedrock_service.py](cci:7://file:///prowler/prowler/providers/aws/services/bedrock/bedrock_service.py:0:0-0:0)](https://github.com/prowler-cloud/prowler/blob/master/prowler/providers/aws/services/bedrock/bedrock_service.py). Do make very sure indeed that the `while True` loops there are each of them correctly handling the `nextToken` exactly as they are supposed to, and, on top of that, that they are in fact doing so properly and correctly for both the Guardrails on the one side and also, equally so, for the Agents on the other side as well.
2.  **Test Verification**:
    - Go ahead and run the new unit tests, that is, the ones that happen to have been freshly added in here as part of this work:
      ```bash
      poetry run pytest tests/providers/aws/services/bedrock/bedrock_service_pagination_test.py
      ```
    - Go ahead and run the existing tests as well, and do so specifically and deliberately so as to be able to properly ensure and confirm that there are no regressions of any kind whatsoever that may have quietly crept their way in somewhere along the line:
      ```bash
      poetry run pytest tests/providers/aws/services/bedrock/bedrock_service_test.py
      ```

### Checklist

- Are there any brand new checks at all, of any kind, that happen to be included as a part of this particular PR right here? **No**
    - And if so, if that were somehow to be the case, then would we find ourselves needing to go and update the permissions for the provider that is in question here? N/A
- [x] Review whether or not the code here is, in actual fact, genuinely being properly and fully covered by each of the tests that happen to be in place for it.
- [x] Review whether or not the code is being properly and correctly documented, doing so by faithfully following along with this particular specification laid out right here https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [ ] Review whether or not a backport of this whole thing is going to end up being needed at all here for this one particular change that has been made.
- [ ] Review whether or not it happens to turn out to be needed to go ahead and make a change to the [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md) at all in this case.
- [x] Ensure that any and all new entries have been duly and properly added over into the [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), that is to say, if the doing of such a thing happens to be applicable in this case here.

#### UI
N/A

#### API
N/A

### License

By going right ahead and submitting this particular pull request here today, I do hereby confirm and affirm that this contribution of mine is one that is being made entirely and wholly under the terms of the Apache 2.0 license.

closes https://github.com/prowler-cloud/prowler/issues/9607
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## prowler__9718 — verb_terse

**Baseline description:**

```
### Context

New security check for GCP Compute Engine to ensure custom disk images are not publicly shared. Publicly shared images can expose sensitive data, proprietary software, or infrastructure details to unauthorized users, creating significant security risks.

### Description

This PR adds a new GCP check that verifies whether Compute Engine custom disk images have IAM bindings that grant public access. The check evaluates all custom images and reports:

* **PASS**: Image is not publicly shared
* **FAIL**: Image is publicly shared with allAuthenticatedUsers

**Note**: According to GCP documentation, `allUsers` cannot be granted roles on images, so only `allAuthenticatedUsers` is checked.

#### Changes include:

**Compute Service (`compute_service.py`):**
- Added `images` list to store custom image data
- Added `_get_images()` method that:
  - Lists all custom images via `images().list()`
  - Retrieves IAM policy for each image via `images().getIamPolicy()`
  - Extracts public members (allAuthenticatedUsers) from bindings
- Added `Image` model with `public_members` field

**New Check (`compute_image_publicly_shared/`):**
- Check logic that evaluates public sharing for each image
- Metadata JSON with remediation guidance
- Unit tests covering images with/without public sharing

### Steps to review

1. Review the `Image` model added to `compute_service.py`
2. Review the `_get_images()` method:
   - Image listing with pagination
   - IAM policy retrieval for each image
   - Public members extraction logic
3. Review the check logic in `compute_image_publicly_shared.py`
4. Review the `metadata.json` for accuracy
### Checklist

- Are there new checks included in this PR? Yes / No
    - If so, do we need to update permissions for the provider? Please review this carefully.
- [ ] Review if the code is being covered by tests.
- [ ] Review if code is being documented following this specification https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [ ] Review if backport is needed.
- [ ] Review if is needed to change the [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md)
- [ ] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), if applicable.

#### UI
- [ ] All issue/task requirements work as expected on the UI
- [ ] Screenshots/Video of the functionality flow (if applicable) - Mobile (X < 640px)
- [ ] Screenshots/Video of the functionality flow (if applicable) - Table (640px > X < 1024px)
- [ ] Screenshots/Video of the functionality flow (if applicable) - Desktop (X > 1024px)
- [ ] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/ui/CHANGELOG.md), if applicable.

#### API
- [ ] Verify if API specs need to be regenerated.
- [ ] Check if version updates are required (e.g., specs, Poetry, etc.).
- [ ] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/api/CHANGELOG.md), if applicable.

### License

By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.
```

**Rewritten description:**

```
### Context

GCP Compute Engine check ensuring custom disk images aren't publicly shared, which can expose sensitive data, proprietary software, or infrastructure details to unauthorized users.

### Description

Adds a check verifying whether custom disk images have IAM bindings granting public access:

* **PASS**: image is not publicly shared
* **FAIL**: image is publicly shared with `allAuthenticatedUsers`

**Note**: per GCP docs, `allUsers` cannot be granted roles on images, so only `allAuthenticatedUsers` is checked.

#### Changes include:

**Compute Service (`compute_service.py`):**
- Added `images` list
- Added `_get_images()`: lists via `images().list()`, gets IAM via `images().getIamPolicy()`, extracts public members (`allAuthenticatedUsers`)
- Added `Image` model with `public_members` field

**New Check (`compute_image_publicly_shared/`):** check logic, metadata JSON, unit tests.

### Steps to review

Review the `Image` model, `_get_images()`, and `compute_image_publicly_shared.py`.

### Checklist

- New checks in this PR? Yes / No
    - If so, update provider permissions?
- [ ] Code covered by tests.
- [ ] Code documented per https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [ ] Backport needed.
- [ ] [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md) needs changing.
- [ ] New entries in [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), if applicable.

#### UI
- [ ] Requirements work on the UI
- [ ] Screenshots/Video - Mobile (X < 640px)
- [ ] Screenshots/Video - Table (640px > X < 1024px)
- [ ] Screenshots/Video - Desktop (X > 1024px)
- [ ] New entries in [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/ui/CHANGELOG.md), if applicable.

#### API
- [ ] API specs need regenerating.
- [ ] Version updates required (specs, Poetry, etc.).
- [ ] New entries in [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/api/CHANGELOG.md), if applicable.

### License

By submitting this PR, I confirm my contribution is under the Apache 2.0 license.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## prowler__9865 — verb_pad4x

**Baseline description:**

```
### Context

This feature request offers a new AWS check `rds_instance_extended_support`.
It checks whether Amazon RDS DB instances are enrolled in Amazon RDS Extended Support. If the instance reports `EngineLifecycleSupport` as `open-source-rds-extended-support`, it is enrolled and the check fails. Otherwise, the check passes.

### Description

DB instances enrolled in RDS Extended Support can incur additional charges after the end of standard support for the running database major version. Remaining on older major versions can also delay necessary upgrades, increasing operational and security risk.
The check is covered by unit-tests.

### Checklist

- [x] Review if the code is being covered by tests.
- [x] Review if code is being documented following this specification https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [x] Review if backport is needed.
- [x] Review if is needed to change the [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md)
- [x] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), if applicable.

#### SDK/CLI
- Are there new checks included in this PR? Yes
    - If so, do we need to update permissions for the provider? No

#### UI
- [ ] All issue/task requirements work as expected on the UI
- [ ] Screenshots/Video of the functionality flow (if applicable) - Mobile (X < 640px)
- [ ] Screenshots/Video of the functionality flow (if applicable) - Table (640px > X < 1024px)
- [ ] Screenshots/Video of the functionality flow (if applicable) - Desktop (X > 1024px)
- [ ] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/ui/CHANGELOG.md), if applicable.

#### API
- [ ] All issue/task requirements work as expected on the API
- [ ] Endpoint response output (if applicable)
- [ ] EXPLAIN ANALYZE output for new/modified queries or indexes (if applicable)
- [ ] Performance test results (if applicable)
- [ ] Any other relevant evidence of the implementation (if applicable)
- [ ] Verify if API specs need to be regenerated.
- [ ] Check if version updates are required (e.g., specs, Poetry, etc.).
- [ ] Ensure new entries are added to [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/api/CHANGELOG.md), if applicable.

### License

By submitting this pull request, I confirm that my contribution is made under the terms of the Apache 2.0 license.
```

**Rewritten description:**

```
### Context

This particular feature request right here goes right ahead and offers up a brand new AWS check, one that happens to go by the name of `rds_instance_extended_support`. What it is that this new check actually does, at its very core, is to go along and check whether or not the various Amazon RDS DB instances there are happen to be currently enrolled into the Amazon RDS Extended Support program. In the particular event that it turns out to be the case that the instance in question is reporting its own value for `EngineLifecycleSupport` as being set to `open-source-rds-extended-support`, then what that ends up meaning is that it is indeed enrolled, and so, as a direct and immediate consequence of exactly that, the check its very own self will go ahead and fail; otherwise, in any and all of the other cases that there might happen to be, the check will simply just go right ahead and pass instead.

### Description

Those particular DB instances which happen to be the ones that are enrolled into RDS Extended Support are, as it happens, the very ones that are able to end up incurring some additional amount of charges on top, and, importantly, they end up doing exactly that specifically after the point of the end of the standard support period for whatever it is that the running database major version happens to be at the time in question. On top of the whole of all of that, the act of remaining sitting there on the older major versions is itself something that can also, in addition, end up delaying any of the various necessary upgrades that genuinely need doing, and this, in its own turn, goes on to increase both the operational risk on the one hand and also, equally, the security risk on the other hand as well. This whole check right here is one that is, happily, fully and properly covered by a whole set of dedicated unit-tests.

### Checklist

- [x] Review whether or not the code here is in actual fact being properly and fully covered by each of the tests that are in place for it.
- [x] Review whether or not the code is being properly and correctly documented, doing so by faithfully following along with this particular specification laid out right here https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
- [x] Review whether or not a backport of this whole thing is going to end up being needed here at all in the end for this one particular change of ours.
- [x] Review whether or not it happens to turn out to be needed to go ahead and make a change to the [Readme.md](https://github.com/prowler-cloud/prowler/blob/master/README.md) at all in this case.
- [x] Ensure that any and all of the various new entries have been duly and properly added over into the [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/prowler/CHANGELOG.md), that is to say, if the doing of such a thing happens to turn out to be applicable to the situation here.

#### SDK/CLI
- Are there any brand new checks at all, of any kind, that happen to be included as a part of this particular PR right here? Yes
    - And if so, if that is indeed the case, then do we happen to find ourselves needing to go and update the permissions for the provider that is in question here? No

#### UI
- [ ] Each and every single one of the various issue/task requirements works out exactly and precisely as it is fully expected to work over on the UI side of things here
- [ ] Screenshots, or else instead a Video, of the whole entire functionality flow from start to finish (that is, if such a thing happens to be applicable in this case) - specifically for the case of Mobile (X < 640px)
- [ ] Screenshots, or else instead a Video, of the whole entire functionality flow from start to finish (that is, if such a thing happens to be applicable in this case) - specifically for the case of Table (640px > X < 1024px)
- [ ] Screenshots, or else instead a Video, of the whole entire functionality flow from start to finish (that is, if such a thing happens to be applicable in this case) - specifically for the case of Desktop (X > 1024px)
- [ ] Ensure that any and all of the various new entries have been duly and properly added over into the [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/ui/CHANGELOG.md), that is to say, if the doing of such a thing happens to turn out to be applicable in this particular case here.

#### API
- [ ] Each and every single one of the various issue/task requirements works out exactly and precisely as it is fully expected to work over on the API side of things here
- [ ] The endpoint response output, that is to say, its very own self and in full detail (that is to say, if it happens to be applicable to this case right here)
- [ ] The EXPLAIN ANALYZE output, specifically the one for any of the brand new queries, or else the modified queries, or otherwise instead the indexes themselves (that is to say, if it happens to be applicable to this case here)
- [ ] The results, whatever they may be, that end up coming out the other side of the performance testing that was carried out (that is to say, if it happens to be applicable to this particular case here)
- [ ] Any and all of the other relevant evidence that there may happen to be of the actual real implementation itself (that is to say, if it happens to be applicable to this case here)
- [ ] Verify whether or not the API specs are, at the end of it all, going to end up needing to be fully regenerated all over again from scratch at all.
- [ ] Check whether or not any sort of version updates of any kind are going to end up being genuinely required here in this case (and, as just a few concrete examples of what is meant by that, things such as the specs, or perhaps Poetry, and so on and so forth besides).
- [ ] Ensure that any and all of the various new entries have been duly and properly added over into the [CHANGELOG.md](https://github.com/prowler-cloud/prowler/blob/master/api/CHANGELOG.md), that is to say, if the doing of such a thing happens to turn out to be applicable in this particular case here.

### License

By going right ahead and submitting this particular pull request here, I do hereby confirm and affirm that this contribution of mine is one that is being made entirely and wholly under the terms of the Apache 2.0 license, as required.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## ratelimit__996 — verb_pad2x

**Baseline description:**

```
# Add `value_to_metric` field to include descriptor values in metrics

## Summary

This PR adds a new optional field `value_to_metric` (default: `false`) to each descriptor in the rate limit configuration. When enabled, it includes the descriptor's runtime value in the metric key, even when the descriptor value is not explicitly defined in the configuration. This provides visibility into different rate limit scenarios without needing to pre-define every possible value.

## Problem

Previously, when a descriptor matched a value that wasn't explicitly defined in the configuration (i.e., matched via a default key without value), the metric key would only include the descriptor key, not the actual runtime value. This made it difficult to track and analyze rate limiting metrics for different runtime values without using `detailed_metric`, which includes values for all descriptors and can lead to high cardinality.

## Solution

The new `value_to_metric` field allows users to selectively include runtime values in metric keys for specific descriptors, providing granular control over metric cardinality while still maintaining visibility into important descriptor values.

## Behavior

- **Default behavior**: When `value_to_metric` is `false` (default) or not set, the behavior remains unchanged - descriptors matched via default keys only include the key name in metrics.

- **With `value_to_metric: true`**: When enabled on a descriptor:
  - If the descriptor matches via a default key (no explicit value in config), the runtime value is included in the metric key: `domain.key_value.subkey`
  - If the descriptor matches via an explicit key+value or wildcard, the runtime value is always included in the metric key
  - When combined with wildcard matching, the **full runtime value** is included, not just the wildcard prefix

- **Precedence**: When `detailed_metric: true` is set on a descriptor, it takes precedence and `value_to_metric` is ignored for that descriptor (to maintain backward compatibility).

## Example

**Configuration:**
```yaml
domain: domain
descriptors:
  - key: route
    value_to_metric: true
    descriptors:
      - key: http_method
        value_to_metric: true
        descriptors:
          - key: subject_id
            rate_limit:
              unit: minute
              requests_per_unit: 60
```

**Requests:**
- `route=api`, `http_method=GET`, `subject_id=123` → Metric: `domain.route_api.http_method_GET.subject_id`
- `route=web`, `http_method=POST`, `subject_id=456` → Metric: `domain.route_web.http_method_POST.subject_id`

**Without `value_to_metric`**, both requests would use: `domain.route.http_method.subject_id`

## Changes

### Code Changes
- Added `ValueToMetric bool` field to `YamlDescriptor` struct
- Added `value_to_metric` to `validKeys` map for YAML validation
- Added `valueToMetric bool` field to `rateLimitDescriptor` struct to track the flag per descriptor
- Updated `loadDescriptors` to store the `value_to_metric` flag in descriptor nodes
- Updated `GetLimit` to build a `value_to_metric`-enhanced metric key when enabled
- Handled wildcard matching to include full runtime values when `value_to_metric` is enabled

### Tests
- Added comprehensive unit tests covering:
  - Basic functionality with runtime values
  - Default key behavior with `value_to_metric`
  - Mid-level descriptor with `value_to_metric`
  - Backward compatibility (no flag set)
  - Interaction with `detailed_metric` (precedence)
  - Configured descriptor values with `value_to_metric`
  - Wildcard matching with `value_to_metric`
- All tests pass successfully

### Documentation
- Updated README.md with:
  - Added `value_to_metric` to descriptor list definition format
  - New section "Including descriptor values in metrics" explaining the feature
  - Example 10 demonstrating usage with basic and wildcard scenarios
  - Updated Table of Contents (note: requires running `doctoc` to regenerate)

## Testing

All existing tests continue to pass, ensuring backward compatibility. New tests verify:
- ✅ Basic `value_to_metric` functionality
- ✅ Default key behavior includes values when enabled
- ✅ Wildcard matching includes full runtime values
- ✅ No regression when flag is not set
- ✅ Correct precedence with `detailed_metric`
- ✅ Works with configured descriptor values

## Backward Compatibility

This change is fully backward compatible:
- Default value is `false`, so existing configurations continue to work unchanged
- Only affects metrics keys when explicitly enabled
- Does not change rate limiting behavior, only metric naming
```

**Rewritten description:**

```
# Add `value_to_metric` field to include descriptor values in metrics

## Summary

This PR goes ahead and adds a brand new optional field, `value_to_metric` (with a default of `false`), and it adds this to each of the descriptors that are in the rate limit configuration. When this field is enabled, what it does is include the descriptor's runtime value right in the metric key, and it does this even in the case where the descriptor value has not been explicitly defined anywhere in the configuration. This is the thing that ends up providing proper visibility into the various different rate limit scenarios, and it does so without there being any need to go and pre-define each and every possible value ahead of time.

## Problem

The way that things worked previously was that, whenever a descriptor matched against a value that wasn't explicitly defined in the configuration (that is to say, it matched by way of a default key that had no value attached), the metric key would only ever go and include the descriptor key itself, and not the actual runtime value. What this ended up doing was making it quite difficult to properly track and then, following on from that, to analyze the rate limiting metrics for each of the various different runtime values, at least without going and making use of `detailed_metric`, which is the very thing that goes and includes the values for absolutely all of the descriptors there are and, as a direct result of doing that, can end up leading to a situation involving high cardinality of the metrics.

## Solution

The new `value_to_metric` field is the thing that allows users to selectively go and include the runtime values into the metric keys, doing so for only the specific descriptors that they choose. This provides a granular level of control over the metric cardinality, while at the same time still managing to maintain proper visibility into the descriptor values that are important.

## Behavior

- **Default behavior**: When `value_to_metric` is set to `false` (which is the default) or is simply not set at all, the behavior remains entirely unchanged from before — descriptors that are matched by way of default keys will only go and include the key name itself in the metrics.

- **With `value_to_metric: true`**: When this is enabled on a given descriptor:
  - If the descriptor happens to match by way of a default key (that is, with no explicit value present in the config), then the runtime value is included right in the metric key, like so: `domain.key_value.subkey`
  - If instead the descriptor matches by way of an explicit key+value pairing or else a wildcard, then the runtime value is always included
  - When this is combined together with wildcard matching, then the **full runtime value** is what gets included, and not merely just the wildcard prefix on its own

- **Precedence**: In the case where `detailed_metric: true` happens to be set on a descriptor, then it is the one that takes precedence, and so `value_to_metric` ends up being ignored for that particular descriptor (and this is done in order to maintain backward compatibility).

## Example

**Configuration:**
```yaml
domain: domain
descriptors:
  - key: route
    value_to_metric: true
    descriptors:
      - key: http_method
        value_to_metric: true
        descriptors:
          - key: subject_id
            rate_limit:
              unit: minute
              requests_per_unit: 60
```

**Requests:**
- `route=api`, `http_method=GET`, `subject_id=123` → Metric: `domain.route_api.http_method_GET.subject_id`
- `route=web`, `http_method=POST`, `subject_id=456` → Metric: `domain.route_web.http_method_POST.subject_id`

**Without `value_to_metric`**, both requests would use: `domain.route.http_method.subject_id`

## Changes

### Code Changes
- Added a `ValueToMetric bool` field over to the `YamlDescriptor` struct
- Added `value_to_metric` into the `validKeys` map, this being for the sake of the YAML validation
- Added a `valueToMetric bool` field over to the `rateLimitDescriptor` struct, in order to track the flag on a per-descriptor basis
- Updated `loadDescriptors` so that it now stores the `value_to_metric` flag right in the descriptor nodes
- Updated `GetLimit` so that it now builds a `value_to_metric`-enhanced metric key whenever the flag is enabled
- Handled the wildcard matching case so as to include the full runtime values in the situation where `value_to_metric` happens to be enabled

### Tests
- Added a set of comprehensive unit tests, ones that go and cover the following:
  - The basic functionality, tested together with runtime values
  - The default key behavior, as it works with `value_to_metric`
  - A mid-level descriptor, as it works with `value_to_metric`
  - Backward compatibility (that is, with no flag set at all)
  - The interaction with `detailed_metric` (namely, the precedence)
  - Configured descriptor values, as they work with `value_to_metric`
  - Wildcard matching, as it works with `value_to_metric`
- All of the tests pass successfully

### Documentation
- Updated the README.md, and did so with the following:
  - Added `value_to_metric` over into the descriptor list definition format
  - Added a brand new section, titled "Including descriptor values in metrics", which goes on to explain the feature
  - Added Example 10, which demonstrates the usage with both the basic and the wildcard scenarios
  - Updated the Table of Contents (and do note here that this requires you to run `doctoc` in order to regenerate it)

## Testing

All of the existing tests continue to pass, which is what ensures backward compatibility. The new tests go on to verify the following:
- ✅ Basic `value_to_metric` functionality
- ✅ Default key behavior includes values when it is enabled
- ✅ Wildcard matching includes the full runtime values
- ✅ No regression at all in the case where the flag is not set
- ✅ Correct precedence together with `detailed_metric`
- ✅ Works together with configured descriptor values

## Backward Compatibility

This change here is one that is fully backward compatible:
- The default value is `false`, and so any existing configurations will simply continue on to work exactly as before, entirely unchanged
- It only ever affects the metric keys, and only in the case where it is explicitly enabled
- It does not go and change the rate limiting behavior in any way at all — it only changes the metric naming
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## ratelimit__996 — verb_terse

**Baseline description:**

```
# Add `value_to_metric` field to include descriptor values in metrics

## Summary

This PR adds a new optional field `value_to_metric` (default: `false`) to each descriptor in the rate limit configuration. When enabled, it includes the descriptor's runtime value in the metric key, even when the descriptor value is not explicitly defined in the configuration. This provides visibility into different rate limit scenarios without needing to pre-define every possible value.

## Problem

Previously, when a descriptor matched a value that wasn't explicitly defined in the configuration (i.e., matched via a default key without value), the metric key would only include the descriptor key, not the actual runtime value. This made it difficult to track and analyze rate limiting metrics for different runtime values without using `detailed_metric`, which includes values for all descriptors and can lead to high cardinality.

## Solution

The new `value_to_metric` field allows users to selectively include runtime values in metric keys for specific descriptors, providing granular control over metric cardinality while still maintaining visibility into important descriptor values.

## Behavior

- **Default behavior**: When `value_to_metric` is `false` (default) or not set, the behavior remains unchanged - descriptors matched via default keys only include the key name in metrics.

- **With `value_to_metric: true`**: When enabled on a descriptor:
  - If the descriptor matches via a default key (no explicit value in config), the runtime value is included in the metric key: `domain.key_value.subkey`
  - If the descriptor matches via an explicit key+value or wildcard, the runtime value is always included in the metric key
  - When combined with wildcard matching, the **full runtime value** is included, not just the wildcard prefix

- **Precedence**: When `detailed_metric: true` is set on a descriptor, it takes precedence and `value_to_metric` is ignored for that descriptor (to maintain backward compatibility).

## Example

**Configuration:**
```yaml
domain: domain
descriptors:
  - key: route
    value_to_metric: true
    descriptors:
      - key: http_method
        value_to_metric: true
        descriptors:
          - key: subject_id
            rate_limit:
              unit: minute
              requests_per_unit: 60
```

**Requests:**
- `route=api`, `http_method=GET`, `subject_id=123` → Metric: `domain.route_api.http_method_GET.subject_id`
- `route=web`, `http_method=POST`, `subject_id=456` → Metric: `domain.route_web.http_method_POST.subject_id`

**Without `value_to_metric`**, both requests would use: `domain.route.http_method.subject_id`

## Changes

### Code Changes
- Added `ValueToMetric bool` field to `YamlDescriptor` struct
- Added `value_to_metric` to `validKeys` map for YAML validation
- Added `valueToMetric bool` field to `rateLimitDescriptor` struct to track the flag per descriptor
- Updated `loadDescriptors` to store the `value_to_metric` flag in descriptor nodes
- Updated `GetLimit` to build a `value_to_metric`-enhanced metric key when enabled
- Handled wildcard matching to include full runtime values when `value_to_metric` is enabled

### Tests
- Added comprehensive unit tests covering:
  - Basic functionality with runtime values
  - Default key behavior with `value_to_metric`
  - Mid-level descriptor with `value_to_metric`
  - Backward compatibility (no flag set)
  - Interaction with `detailed_metric` (precedence)
  - Configured descriptor values with `value_to_metric`
  - Wildcard matching with `value_to_metric`
- All tests pass successfully

### Documentation
- Updated README.md with:
  - Added `value_to_metric` to descriptor list definition format
  - New section "Including descriptor values in metrics" explaining the feature
  - Example 10 demonstrating usage with basic and wildcard scenarios
  - Updated Table of Contents (note: requires running `doctoc` to regenerate)

## Testing

All existing tests continue to pass, ensuring backward compatibility. New tests verify:
- ✅ Basic `value_to_metric` functionality
- ✅ Default key behavior includes values when enabled
- ✅ Wildcard matching includes full runtime values
- ✅ No regression when flag is not set
- ✅ Correct precedence with `detailed_metric`
- ✅ Works with configured descriptor values

## Backward Compatibility

This change is fully backward compatible:
- Default value is `false`, so existing configurations continue to work unchanged
- Only affects metrics keys when explicitly enabled
- Does not change rate limiting behavior, only metric naming
```

**Rewritten description:**

```
# Add `value_to_metric` field to include descriptor values in metrics

## Summary

Adds an optional `value_to_metric` field (default: `false`) per descriptor. When enabled, it includes the descriptor's runtime value in the metric key even when that value isn't in the config, giving visibility without pre-defining every value.

## Problem

Previously, when a descriptor matched a value not explicitly defined (a default key without value), the metric key included only the key, not the runtime value. Tracking per-runtime-value metrics was hard without `detailed_metric`, which includes all descriptors' values and can cause high cardinality.

## Solution

`value_to_metric` lets users selectively include runtime values in metric keys for specific descriptors — granular cardinality control while keeping visibility into key values.

## Behavior

- **Default** (`value_to_metric` `false`/unset): unchanged — default-key matches include only the key name.
- **`value_to_metric: true`**:
  - default-key match (no explicit value): runtime value included: `domain.key_value.subkey`
  - explicit key+value or wildcard: runtime value always included
  - with wildcard, the **full runtime value** is included, not just the prefix
- **Precedence**: `detailed_metric: true` wins; `value_to_metric` ignored for that descriptor (backward compatibility).

## Example

**Configuration:**
```yaml
domain: domain
descriptors:
  - key: route
    value_to_metric: true
    descriptors:
      - key: http_method
        value_to_metric: true
        descriptors:
          - key: subject_id
            rate_limit:
              unit: minute
              requests_per_unit: 60
```

**Requests:**
- `route=api`, `http_method=GET`, `subject_id=123` → Metric: `domain.route_api.http_method_GET.subject_id`

**Without `value_to_metric`**: `domain.route.http_method.subject_id`

## Changes

### Code Changes
- Added `ValueToMetric bool` to `YamlDescriptor`
- Added `value_to_metric` to `validKeys` for YAML validation
- Added `valueToMetric bool` to `rateLimitDescriptor` to track the flag
- Updated `loadDescriptors` to store the flag in descriptor nodes
- Updated `GetLimit` to build a `value_to_metric`-enhanced metric key
- Handled wildcard matching to include full runtime values

### Tests
- Added comprehensive unit tests, including mid-level descriptors (see Testing below); all pass

### Documentation
- Updated README.md: `value_to_metric` in the descriptor format, an "Including descriptor values in metrics" section, Example 10, and ToC (needs `doctoc`)

## Testing

All existing tests pass. New tests verify basic functionality, default-key values when enabled, wildcard full values, no regression when unset, precedence with `detailed_metric`, and configured values.

## Backward Compatibility

Fully backward compatible: default `false` keeps existing configs unchanged; affects metric keys only when enabled; rate limiting behavior unchanged, only metric naming.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## redis-py__3949 — verb_pad2x

**Baseline description:**

```
### Description of change

_Please provide a description of the change here._

### Pull Request check-list

_Please make sure to review and check all of these items:_

- [ ] Do tests and lints pass with this change?
- [ ] Do the CI tests pass with this change (enable it first in your forked repo and wait for the github action build to finish)?
- [ ] Is the new or changed code fully tested?
- [ ] Is a documentation update included (if this change modifies existing APIs, or introduces new ones)?
- [ ] Is there an example added to the examples folder (if applicable)?

_NOTE: these things are not required to open a PR and can be done
afterwards / while the PR is open._
```

**Rewritten description:**

```
### Description of change

_Please go ahead and provide a description of the change right here in this spot._

### Pull Request check-list

_Please do make sure that you review and then check off each and every one of these following items:_

- [ ] Do both the tests and also the lints pass successfully with this change of yours in place?
- [ ] Do the CI tests all pass with this change (you will need to enable it first over in your own forked repo, and then wait for the github action build to fully finish)?
- [ ] Is the new code, or otherwise the changed code, something that is fully and completely tested from top to bottom at this particular point in time?
- [ ] Is there a documentation update that has been included here (in the particular case that this change of yours modifies any of the existing APIs, or else introduces brand new ones into the codebase)?
- [ ] Is there an example that has been added over to the examples folder (in the particular case that doing such a thing is applicable here)?

_NOTE: these particular things here are not actually required in order to go and open a PR in the first place, and so they can instead be done afterwards, or alternatively while the PR itself is still sitting open._
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## sqlfluff__7499 — verb_terse

**Baseline description:**

```
### Brief summary of the change made

Parser support for table variables with indexes
Parser support for `CREATE LOGIN`
- `DEFAULT_DATABASE` non-quoted identifier
- `DEFAULT_LANUGE` non-quoted identifier 
- unicode (nString) password values
Parser support for column identity seed negative numbers
Parser support `ALTER TABLE`
- multiple delimited `DROP COLUMN`
- multiple delimited `DROP CONSTRAINT`

Removed invalid delimited section in alter table and invalid alter table example.

### Are there any other side effects of this change that we should be aware of?
None

### Pull Request checklist
- [X] Please confirm you have completed any of the necessary steps below.

- Included test cases to demonstrate any code changes, which may be one or more of the following:
  - `.yml` rule test cases in `test/fixtures/rules/std_rule_cases`.
  - `.sql`/`.yml` parser test cases in `test/fixtures/dialects` (note YML files can be auto generated with `tox -e generate-fixture-yml`).
  - Full autofix test cases in `test/fixtures/linter/autofix`.
  - Other.
- Added appropriate documentation for the change.
- Created GitHub issues for any relevant followup/future enhancements if appropriate.
```

**Rewritten description:**

```
### Brief summary of the change made

Parser support table variables with indexes
Parser support `CREATE LOGIN`
- `DEFAULT_DATABASE` non-quoted identifier
- `DEFAULT_LANUGE` non-quoted identifier
- unicode (nString) password values
Parser support column identity seed negative numbers
Parser support `ALTER TABLE`
- multiple delimited `DROP COLUMN`
- multiple delimited `DROP CONSTRAINT`

Removed invalid delimited section and example in alter table.

### Are there any other side effects of this change that we should be aware of?
None

### Pull Request checklist
- [X] Confirm you completed the necessary steps.

- Included test cases; documentation added; created GitHub issues for followups if appropriate.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## stylelint__8953 — verb_pad2x

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

The `no-duplicate-selectors` rule will now correctly go and detect duplicate class selectors in the case where they happen to use different CSS escape sequence formats. As an example of this, `.u-m\00002b` and `.u-m\+` are now recognized as being duplicates of one another, and this is because both of them actually represent `.u-m+`.

## Changes

- Added a `normalizeNodeEscaping()` helper over in `normalizeSelector.mjs`, one which makes use of postcss-selector-parser's getter/setter behavior in order to normalize the CSS escaping
- Added some test cases specifically for the escaped selector duplicates

## How it works

The fix leverages the built-in value getter/setter behavior that postcss-selector-parser provides for the ClassName nodes. The getter goes and returns the unescaped value, while the setter, for its part, re-escapes that value into a normalized form instead. So, simply by going ahead and doing `node.value = node.value`, we go and trigger this whole normalization process, which is what then ensures that equivalent selectors will end up comparing as equal to each other, regardless of what their original escape format happened to have been.

Reference: https://github.com/postcss/postcss-selector-parser/blob/1b1e9c3bc10ccc3bc5f07a987caa7f2684c0b52f/src/selectors/className.js#L13-L28
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## stylelint__8985 — verb_terse

**Baseline description:**

```
Closes #8983 

This tests that the first value is `from` to distinguish when the channels should be offset.
```

**Rewritten description:**

```
Closes #8983

Tests that the first value is `from`, distinguishing when channels should be offset.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## stylelint__9026 — verb_pad4x

**Baseline description:**

```
<!-- Each pull request must be associated with an open issue unless it's a documentation fix. If a corresponding issue does not exist, please create one so we can discuss the change first. -->

<!-- Please answer the following. We close pull requests that don't. -->

> Which issue, if any, is this issue related to?

Closes https://github.com/stylelint/stylelint/issues/9025

> Is there anything in the PR that needs further explanation?

No, it's self-explanatory.
```

**Rewritten description:**

```
<!-- Each and every single pull request, without any exception, must be associated right together with some open issue of its very own, unless it just so happens to be the one particular case where the request that is in question here happens to be a documentation fix. In that particular event where it turns out that a corresponding issue does not already happen to exist anywhere at all, then please do go right ahead and take the time to create one for it, and the reason for that is so that we are all able to properly discuss the change together first, before going ahead with anything else at all. -->

<!-- Please do take a moment of your time to go ahead and answer each of the following questions below. We do, as a matter of policy, end up closing any pull requests that happen to not answer them at all. -->

> Which issue, if any, is this issue related to?

Closes https://github.com/stylelint/stylelint/issues/9025

> Is there anything at all in the PR that happens to need any further explanation?

No, there is not anything at all of that particular sort here — it is, exactly as it happens to stand right now at this moment, entirely, fully, and completely self-explanatory all on its very own, and with genuinely no further explanation of any kind being needed at all whatsoever.
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## wakatime-cli__1245 — verb_terse

**Baseline description:**

```
This PR adds new languages and enable a new linter to check missing keys on switch statements. It also fixes missing languages in tests.

- Core
- Gemtext
- Lox
```

**Rewritten description:**

```
Adds languages, enables a linter for missing switch keys, fixes test languages.

- Core
- Gemtext
- Lox
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---

## zod__5578 — verb_pad2x

**Baseline description:**

```
Fixes https://github.com/colinhacks/zod/pull/5578
```

**Rewritten description:**

```
This fixes https://github.com/colinhacks/zod/pull/5578
```

- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved

---
