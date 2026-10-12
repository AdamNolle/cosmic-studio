# Native overflow keyboard recovery candidate (iteration39)

Recovery-first after the original contract review: **opening stays disabled**.
No accepted keyboard-only entry/traversal/restoration/hiding or deployment.

## Actual coordinated seam

Original Press/Release callers already invoke the route after Smithay input;
Repeat after capture without another server down. Its new mutable entry first
tries a dedicated native dismissal, without entering any element mutex, SDK
keyboard handler, ordinary Program update, pointer dispatcher or idle/task.

The candidate requires a unique live originating keyboard/client seat, original
fresh frame/press, unique active same-seat focus on the exact live native overflow
popup, exact ephemeral (popup proxy, creating client WlSeat) owner, no ordinary
or descendant popup, no server keyboard grab and no proxied/internal server
keyboard focus. Unknown/stale/nonzero raw or named modifiers remain refused;
zero is not invented. Original full conversion must identify unmodified Escape.
Repeat, release, duplicate/entry-held and other keys cannot dismiss.

Private ledger consumption checks exact current press lifetime, then allows one
native action attempt for that raw key until its actual release or focus reset.
It does not retire the held press, reconstruct events, validate upstream grabs
or restore reusable authority after a failed effect. All refusals precede consume.
No callback/yield intervenes before synchronous existing force-hide. No anchor
mapping/live parent is required for recovery, no opening/serial grab is requested.
The original client press serial/seat are retained; no first-seat pointer history.

## Actual teardown correction

The real popup creation records its exact popup/client-seat pair. Original
force-hide, close-popups destruction and panel reset clear ownership. The actual
container PopupHandler::done dispatch previously selected only ordinary popups;
it now includes the exact native overflow popup. PanelSpace::close_popup passed
a matching predicate to an **exclusion** API, retaining the done object while
closing unrelated objects. It now closes the requested
object and its recorded client-surface descendants, retaining unrelated roots,
and requests native redraw/layout. Actual native teardown calls a bounded fixed-
point subtree helper (duplicate/cyclic edges terminate), without assuming remote
Done callback ordering. Actual close_popups captures the original parent edges,
MOVES whole selected native PanelPopup + original embedded PopupSurface owners
into the actual synchronous ordered_teardown batch. It keeps all resources alive
until each child-first step's notification/focus cleanup, then releases native
ownership through original PanelPopup/SCTK RAII. Raw proxies do NOT keep SCTK
PopupInner alive; retain_mut removal and later raw tuple ordering was refused.
No duplicate manual role/surface destruction or foreign SCTK change. Original
Drop/component ownership order is retained; actual callback owners may delay
final RAII release, never a claim of observed protocol or restoration ordering.
Duplicate/late Done has no matching native object and does not select unrelated
roots. Cycle fallback bounds the helper, not a claim of valid cyclic protocol
objects. The first unbuilt leaf-only source8/preview9 and intermediate subtree-
selection source8 and raw-order-before-native-owner-retention source8/preview9
are preserved separately; reviewer P1 is not retroactively a passing verdict on
any initial candidate. Exact read-only original SCTK0.20.0 ownership/Drop sources
match locked crate bytes/checksum; exact PANEL Smithay0ff00983 PopupSurface sources
match original Git HEAD/blobs. No fetch/compile/runtime implied. Raw-order host71/
prepared19/compileall/diffcheck passed but did not cover actual owner lifetime. No synthetic focus, enter, release,
shortcut, grab, text or serialized server-mask synchronization is added.

Original Compositor0fbd457/Smithay e3d461a request/commit/root/topmost/existing-grab
checks are not fresh-key authorization; panel Smithay is different0ff00983.
Destroying a popup uses the original protocol/admission path. Upstream restoration
can select root/prior-popup/window, not necessarily the internal anchor. **Neither
owner tracking, local grab:true nor successful dismissal requests certify actual
upstream admission, keyboard recovery or restoration.** Essential controls stay
visible; stable identity/config migration, a11y and manual hiding stay blocked.

## Guard and evidence scope

Exact original HEAD/Git blobs/38 inert-route postimages/contained nonsymlink/new
module/exclusive patch/Git apply/postimages and panel-only fingerprints are
required. Native callback forwarding and SDK isolation remain unchanged. Original
foreign graph/features/dependencies/licensing remain required. Eight authored
native ledger/converter lifecycle cases plus three actual teardown-selection/order/owned-drop cases and five source/Git/teardown guards are
not live Wayland popup tests. Genuine whole-caller compilation and exact native
counts must be collected independently; no result is inferred here.
