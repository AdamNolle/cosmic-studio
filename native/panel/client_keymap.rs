// SPDX-License-Identifier: GPL-3.0-only
// Safe, explicit owned client-keymap lookup. NOT Iced or popup authorization.
use super::keyboard_event_context::{EventContext, EventFrame};
use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
use smithay::input::keyboard::xkb;
use std::fmt;

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum LookupError {
    MissingKeymap, MissingModifiers, StaleEvent, InvalidKeymap,
    KeycodeOverflow, InvalidLayout, MissingControl, ResidualControl,
    MultipleOrMissingSymbols, EventMismatch,
}

pub(crate) struct Symbols {
    base: xkb::Keysym,
    all: xkb::Keysym,
    control_cleared: xkb::Keysym,
}
impl Symbols {
    pub(crate) fn base(&self) -> xkb::Keysym { self.base }
    pub(crate) fn all(&self) -> xkb::Keysym { self.all }
    pub(crate) fn control_cleared(&self) -> xkb::Keysym { self.control_cleared }
}
impl fmt::Debug for Symbols {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Symbols").finish_non_exhaustive()
    }
}

#[derive(Default)]
pub(crate) struct ClientKeymap { source: Option<String> }
impl fmt::Debug for ClientKeymap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ClientKeymap").field("available", &self.source.is_some()).finish()
    }
}
impl ClientKeymap {
    pub(crate) fn replace(&mut self, original: String) { self.source = Some(original); }
    pub(crate) fn clear(&mut self) { self.source = None; }

    pub(crate) fn lookup<O: Clone + PartialEq>(
        &self,
        context: &EventContext<O, KeyEvent, Modifiers, RawModifiers>,
        frame: &EventFrame<O, KeyEvent, Modifiers, RawModifiers>,
    ) -> Result<Symbols, LookupError> {
        if !context.is_current(frame) { return Err(LookupError::StaleEvent); }
        let modifiers = frame.modifiers().ok_or(LookupError::MissingModifiers)?;
        let source = self.source.as_ref().ok_or(LookupError::MissingKeymap)?;
        // No shared refcounts, borrowed callback keymap, unsafe Send or default
        // environment/include-based RMLVO. Only exact compiled client text-v1.
        let mut native = xkb::Context::new(xkb::CONTEXT_NO_DEFAULT_INCLUDES | xkb::CONTEXT_NO_ENVIRONMENT_NAMES);
        native.set_log_level(xkb::LogLevel::Critical);
        let map = xkb::Keymap::new_from_string(&native, source.clone(), xkb::KEYMAP_FORMAT_TEXT_V1, xkb::KEYMAP_COMPILE_NO_FLAGS)
            .ok_or(LookupError::InvalidKeymap)?;
        let code = xkb::Keycode::new(frame.event().raw_code.checked_add(8).ok_or(LookupError::KeycodeOverflow)?);
        let raw = modifiers.raw();
        let group = modifiers.group();
        if group >= map.num_layouts() { return Err(LookupError::InvalidLayout); }
        let mut all = xkb::State::new(&map);
        let _ = all.update_mask(raw.depressed, raw.latched, raw.locked, 0, 0, group);
        let layout = all.key_get_layout(code);
        if layout == xkb::LAYOUT_INVALID { return Err(LookupError::InvalidLayout); }
        let base = single(map.key_get_syms_by_level(code, layout, 0))?;
        let all_symbol = single(all.key_get_syms(code))?;
        if all_symbol != frame.event().keysym { return Err(LookupError::EventMismatch); }
        let index = map.mod_get_index(xkb::MOD_NAME_CTRL);
        let bit = 1u32.checked_shl(index).ok_or(LookupError::MissingControl)?;
        let mut without_control = xkb::State::new(&map);
        let _ = without_control.update_mask(raw.depressed & !bit, raw.latched & !bit, raw.locked & !bit, 0, 0, group);
        if without_control.mod_name_is_active(xkb::MOD_NAME_CTRL, xkb::STATE_MODS_EFFECTIVE) {
            return Err(LookupError::ResidualControl);
        }
        Ok(Symbols { base, all: all_symbol, control_cleared: single(without_control.key_get_syms(code))? })
    }
}
fn single(symbols: &[xkb::Keysym]) -> Result<xkb::Keysym, LookupError> {
    match symbols {
        [symbol] if symbol.raw() != xkb::keysyms::KEY_NoSymbol => Ok(*symbol),
        _ => Err(LookupError::MultipleOrMissingSymbols),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::keyboard_event_context::Kind;
    type Context = EventContext<&'static str, KeyEvent, Modifiers, RawModifiers>;
    // Authored self-contained synthetic XKB text: no system-layout dependency.
    const MAP: &str = r#"xkb_keymap {
        xkb_keycodes { minimum = 8; maximum = 255; <TEST> = 38; <CTRL> = 37; <SHIFT> = 50; <L3> = 108; };
        xkb_types { type "EIGHT" { modifiers = Shift+Control+Mod5;
            map[None] = Level1; map[Shift] = Level2; map[Control] = Level3;
            map[Shift+Control] = Level4; map[Mod5] = Level5; map[Control+Mod5] = Level6;
            map[Shift+Mod5] = Level7; map[Shift+Control+Mod5] = Level8; }; };
        xkb_compatibility { };
        xkb_symbols { key <TEST> { type[Group1] = "EIGHT", symbols[Group1] = [ a, A, c, C, at, dollar, e, E ],
            type[Group2] = "EIGHT", symbols[Group2] = [ b, B, d, D, numbersign, percent, f, F ] };
            key <CTRL> { [ Control_L ] }; key <SHIFT> { [ Shift_L ] }; key <L3> { [ ISO_Level3_Shift ] };
            modifier_map Control { <CTRL> }; modifier_map Shift { <SHIFT> }; modifier_map Mod5 { <L3> }; };
    };"#;
    fn setup(raw: RawModifiers, group: u32, symbol: u32) -> (ClientKeymap, Context, EventFrame<&'static str, KeyEvent, Modifiers, RawModifiers>) {
        let mut map = ClientKeymap::default(); map.replace(MAP.into());
        let mut context = Context::new("seat"); context.enter();
        context.set_modifiers(77, Modifiers::default(), raw, group);
        let event = KeyEvent { time: 123, raw_code: 30, keysym: xkb::Keysym::new(symbol), utf8: Some("original-compose-é".into()) };
        let frame = context.capture(Kind::Press, 99, event).unwrap();
        (map, context, frame)
    }
    #[test]
    fn independent_owned_map_is_send_without_unsafe_reference_sharing() {
        fn is_send<T: Send>() {} is_send::<ClientKeymap>();
        let (map, context, frame) = setup(RawModifiers::default(), 0, xkb::keysyms::KEY_a);
        let result = map.lookup(&context, &frame).unwrap();
        assert_eq!((result.base().raw(), result.all().raw(), result.control_cleared().raw()), (97, 97, 97));
        assert_eq!(frame.event().utf8.as_deref(), Some("original-compose-é"));
        assert_eq!((frame.serial(), frame.event().raw_code, frame.event().time), (99, 30, 123));
    }
    #[test]
    fn depressed_latched_and_locked_control_are_cleared_without_losing_shift_or_mod5() {
        for raw in [RawModifiers { depressed: 1|4|128, ..RawModifiers::default() },
                    RawModifiers { depressed: 1|128, latched: 4, locked: 0 },
                    RawModifiers { depressed: 1|128, latched: 0, locked: 4 }] {
            let (map, context, frame) = setup(raw, 0, xkb::keysyms::KEY_E);
            let result = map.lookup(&context, &frame).unwrap();
            assert_eq!(result.control_cleared().raw(), xkb::keysyms::KEY_e);
            let retained = frame.modifiers().unwrap().raw();
            assert_eq!((retained.depressed, retained.latched, retained.locked), (raw.depressed, raw.latched, raw.locked));
        }
    }
    #[test]
    fn active_group_is_not_replaced_with_default_us_or_physical_identity() {
        let (map, context, frame) = setup(RawModifiers { depressed: 1|4, ..RawModifiers::default() }, 1, xkb::keysyms::KEY_D);
        let result = map.lookup(&context, &frame).unwrap();
        assert_eq!((result.base().raw(), result.control_cleared().raw()), (xkb::keysyms::KEY_b, xkb::keysyms::KEY_B));
    }
    #[test]
    fn missing_modifier_or_keymap_source_and_invalid_text_are_not_defaults() {
        let (mut map, mut context, frame) = setup(RawModifiers::default(), 0, 97);
        map.clear(); assert_eq!(map.lookup(&context, &frame).unwrap_err(), LookupError::MissingKeymap);
        map.replace("not a keymap".into()); assert_eq!(map.lookup(&context, &frame).unwrap_err(), LookupError::InvalidKeymap);
        context.enter();let fresh = context.capture(Kind::Release, 99, frame.event().clone()).unwrap();
        assert_eq!(map.lookup(&context, &fresh).unwrap_err(), LookupError::MissingModifiers);
    }
    #[test]
    fn stale_event_wrong_symbol_invalid_group_and_raw_overflow_are_refused() {
        let (map, mut context, frame) = setup(RawModifiers::default(), 0, 98);
        assert_eq!(map.lookup(&context, &frame).unwrap_err(), LookupError::EventMismatch);
        context.set_modifiers(78, Modifiers::default(), RawModifiers::default(), 0);
        assert_eq!(map.lookup(&context, &frame).unwrap_err(), LookupError::StaleEvent);
        let mut event = frame.event().clone();event.raw_code = u32::MAX;
        let fresh = context.capture(Kind::Press, 99, event).unwrap();
        assert_eq!(map.lookup(&context, &fresh).unwrap_err(), LookupError::KeycodeOverflow);
        let (map, context, frame) = setup(RawModifiers::default(), u32::MAX, 97);
        assert_eq!(map.lookup(&context, &frame).unwrap_err(), LookupError::InvalidLayout);
    }
    #[test]
    fn multiple_or_missing_symbols_are_not_guessed_as_one_key() {
        assert_eq!(single(&[]).unwrap_err(), LookupError::MultipleOrMissingSymbols);
        assert_eq!(single(&[xkb::Keysym::new(0)]).unwrap_err(), LookupError::MultipleOrMissingSymbols);
        assert_eq!(single(&[xkb::Keysym::new(97), xkb::Keysym::new(98)]).unwrap_err(), LookupError::MultipleOrMissingSymbols);
    }
    #[test]
    fn debug_does_not_reveal_keymap_or_symbols() {
        let (map, context, frame) = setup(RawModifiers::default(), 0, 97);
        assert_eq!(format!("{map:?}"), "ClientKeymap { available: true }");
        assert_eq!(format!("{:?}", map.lookup(&context, &frame).unwrap()), "Symbols { .. }");
    }
}
