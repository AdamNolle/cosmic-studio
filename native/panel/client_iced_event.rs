// SPDX-License-Identifier: GPL-3.0-only
// Explicit metadata conversion only. NOT dispatch, popup-grab or press authority.
use super::{client_keymap::{ClientKeymap, LookupError}, client_key_tables,
    keyboard_event_context::{EventContext, EventFrame, Kind}};
use cosmic::iced::keyboard::{self, Key, Modifiers as IcedModifiers};
use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
use smithay::input::keyboard::xkb;
use std::fmt;

pub(crate) type Frame<O> = EventFrame<O, KeyEvent, Modifiers, RawModifiers>;
pub(crate) type Context<O> = EventContext<O, KeyEvent, Modifiers, RawModifiers>;
pub(crate) struct Converted<O> {
    original: Frame<O>,
    iced: keyboard::Event,
}
impl<O> Converted<O> {
    pub(crate) fn original(&self) -> &Frame<O> { &self.original }
    pub(crate) fn iced(&self) -> &keyboard::Event { &self.iced }
}
impl<O> fmt::Debug for Converted<O> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Converted").finish_non_exhaustive()
    }
}

pub(crate) fn convert<O: Clone + PartialEq>(
    map: &ClientKeymap, context: &Context<O>, frame: &Frame<O>,
) -> Result<Converted<O>, LookupError> {
    // Independent original raw-mask slave lookup; never the lossy server state.
    // Explicit call only: ordinary native forwarding does not parse a keymap.
    let symbols = map.lookup(context, frame)?;
    let key = logical(symbols.base());
    let modified_key = logical(symbols.control_cleared());
    let physical_key = client_key_tables::scancode_to_physicalkey(frame.event().raw_code);
    let location = client_key_tables::keysym_location(symbols.all().raw());
    let modifiers = modifiers(frame.modifiers().ok_or(LookupError::MissingModifiers)?.named());
    let iced = match frame.kind() {
        Kind::Release => keyboard::Event::KeyReleased { key, modified_key, physical_key, location, modifiers },
        Kind::Press | Kind::Repeat => keyboard::Event::KeyPressed {
            key, modified_key, physical_key, location, modifiers,
            // Preserve actual SCTK compose output including None/Some("").
            // A symbol character is NOT composed text; no IME reconstruction.
            text: frame.event().utf8.as_deref().map(Into::into),
            repeat: frame.kind() == Kind::Repeat,
        },
    };
    Ok(Converted { original: frame.clone(), iced })
}
fn logical(symbol: xkb::Keysym) -> Key {
    let named = client_key_tables::keysym_to_key(symbol.raw());
    if !matches!(named, Key::Unidentified) { return named; }
    // Exact locked xkb0.9 already omits the terminating NUL. Unlike the
    // upstream Wayland helper, do NOT pop the last Unicode character.
    let character = xkb::keysym_to_utf8(symbol);
    if character.is_empty() { Key::Unidentified } else { Key::Character(character.into()) }
}
fn modifiers(named: &Modifiers) -> IcedModifiers {
    let mut result = IcedModifiers::NONE;
    result.set(IcedModifiers::SHIFT, named.shift);
    result.set(IcedModifiers::CTRL, named.ctrl);
    result.set(IcedModifiers::ALT, named.alt);
    result.set(IcedModifiers::LOGO, named.logo);
    result.set(IcedModifiers::CAPS_LOCK, named.caps_lock);
    // Iced has no NumLock bit. Its effect remains in symbols; original frame
    // retains num_lock and every raw mask/group. Do not alias it to CapsLock.
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use cosmic::iced::keyboard::{key::{Code, NativeCode, Physical, Named}, Location};
    const MAP: &str = r#"xkb_keymap {
        xkb_keycodes { minimum = 8; maximum = 255; <TEST> = 38; <CTRL> = 37; <SHIFT> = 50; };
        xkb_types { type "FOUR" { modifiers = Shift+Control;
            map[None] = Level1; map[Shift] = Level2; map[Control] = Level3; map[Shift+Control] = Level4; }; };
        xkb_compatibility { };
        xkb_symbols { key <TEST> { type[Group1] = "FOUR", symbols[Group1] = [ a, A, c, C ],
            type[Group2] = "FOUR", symbols[Group2] = [ b, B, d, D ] };
            key <CTRL> { [ Control_L ] }; key <SHIFT> { [ Shift_L ] };
            modifier_map Control { <CTRL> }; modifier_map Shift { <SHIFT> }; };
    };"#;
    fn setup(kind: Kind, text: Option<&str>, group: u32, raw: RawModifiers, named: Modifiers, symbol: u32)
        -> (ClientKeymap, Context<&'static str>, Frame<&'static str>) {
        let mut map = ClientKeymap::default();map.replace(MAP.into());
        let mut context = Context::new("original-seat");context.enter();context.set_modifiers(77, named, raw, group);
        let frame = context.capture(kind, 99, KeyEvent { time: 123, raw_code: 30,
            keysym: xkb::Keysym::new(symbol), utf8: text.map(Into::into) }).unwrap();
        (map, context, frame)
    }
    #[test]
    fn full_press_uses_base_control_cleared_physical_and_original_compose() {
        let (map, context, frame) = setup(Kind::Press, Some("é🦀"), 0,
            RawModifiers { depressed: 1|4, ..Default::default() },
            Modifiers { shift: true, ctrl: true, ..Default::default() }, xkb::keysyms::KEY_C);
        let converted = convert(&map, &context, &frame).unwrap();
        assert_eq!(converted.iced(), &keyboard::Event::KeyPressed {
            key: Key::Character("a".into()), modified_key: Key::Character("A".into()),
            physical_key: Physical::Code(Code::KeyA), location: Location::Standard,
            modifiers: IcedModifiers::SHIFT | IcedModifiers::CTRL, text: Some("é🦀".into()), repeat: false,
        });
        assert!(context.is_current(converted.original()));
        assert_eq!((converted.original().origin(), converted.original().serial(), converted.original().event().time), (&"original-seat",99,123));
    }
    #[test]
    fn release_has_no_text_or_repeat_but_retains_original_envelope() {
        let (map, context, frame) = setup(Kind::Release, Some("opaque-original"), 0, RawModifiers::default(), Modifiers::default(), 97);
        let converted = convert(&map, &context, &frame).unwrap();
        assert!(matches!(converted.iced(), keyboard::Event::KeyReleased { physical_key: Physical::Code(Code::KeyA), .. }));
        assert_eq!(converted.original().kind(), Kind::Release);
        assert_eq!(converted.original().event().utf8.as_deref(), Some("opaque-original"));
    }
    #[test]
    fn only_original_repeat_kind_sets_repeat_and_none_empty_compose_stay_distinct() {
        for text in [None, Some("")] {
            let (map, context, frame) = setup(Kind::Repeat, text, 0, RawModifiers::default(), Modifiers::default(), 97);
            let converted = convert(&map, &context, &frame).unwrap();
            let keyboard::Event::KeyPressed { repeat, text: actual, .. } = converted.iced() else { panic!("press shape required") };
            assert!(*repeat);assert_eq!(actual.as_deref(), text);assert!(context.is_current(&frame));
        }
    }
    #[test]
    fn layout_changes_logical_not_physical_and_latched_locked_control_is_removed() {
        for raw in [RawModifiers { depressed: 1, latched: 4, locked: 0 }, RawModifiers { depressed: 1, latched: 0, locked: 4 }] {
            let (map, context, frame) = setup(Kind::Press, None, 1, raw, Modifiers::default(), xkb::keysyms::KEY_D);
            let converted = convert(&map, &context, &frame).unwrap();
            let keyboard::Event::KeyPressed { key, modified_key, physical_key, .. } = converted.iced() else { panic!("press") };
            assert_eq!(key, &Key::Character("b".into()));assert_eq!(modified_key, &Key::Character("B".into()));
            assert_eq!(physical_key, &Physical::Code(Code::KeyA));
            assert_eq!(converted.original().modifiers().unwrap().raw().locked, raw.locked);
        }
    }
    #[test]
    fn original_named_keys_unicode_and_dead_unknown_symbols_are_not_compose() {
        for (symbol, expected) in [(xkb::keysyms::KEY_Return, Named::Enter), (xkb::keysyms::KEY_Tab, Named::Tab),
            (xkb::keysyms::KEY_ISO_Left_Tab, Named::Tab), (xkb::keysyms::KEY_Escape, Named::Escape),
            (xkb::keysyms::KEY_KP_Enter, Named::Enter), (xkb::keysyms::KEY_XF86AudioMute, Named::AudioVolumeMute)] {
            assert_eq!(logical(xkb::Keysym::new(symbol)), Key::Named(expected));
        }
        assert_eq!(logical(xkb::Keysym::new(xkb::keysyms::KEY_space)), Key::Character(" ".into()));
        assert_eq!(logical(xkb::utf32_to_keysym('é' as u32)), Key::Character("é".into()));
        assert_eq!(logical(xkb::utf32_to_keysym('🦀' as u32)), Key::Character("🦀".into()));
        assert_eq!(logical(xkb::Keysym::new(xkb::keysyms::KEY_dead_acute)), Key::Unidentified);
        assert_eq!(logical(xkb::Keysym::new(0)), Key::Unidentified);
    }
    #[test]
    fn linux_scancode_offset_super_sides_and_unmapped_codes_are_exact() {
        use client_key_tables::scancode_to_physicalkey as physical;
        assert_eq!(physical(30), Physical::Code(Code::KeyA));assert_eq!(physical(38), Physical::Code(Code::KeyL));
        assert_eq!(physical(125), Physical::Code(Code::SuperLeft));assert_eq!(physical(126), Physical::Code(Code::SuperRight));
        assert_eq!(physical(0), Physical::Unidentified(NativeCode::Xkb(0)));
        assert_eq!(physical(240), Physical::Unidentified(NativeCode::Unidentified));
        assert_eq!(physical(999), Physical::Unidentified(NativeCode::Xkb(999)));
        for (symbol, expected) in [(xkb::keysyms::KEY_Control_L, Location::Left), (xkb::keysyms::KEY_Shift_R, Location::Right),
            (xkb::keysyms::KEY_KP_Enter, Location::Numpad), (xkb::keysyms::KEY_KP_7, Location::Numpad), (97, Location::Standard)] {
            assert_eq!(client_key_tables::keysym_location(symbol), expected);
        }
    }
    #[test]
    fn all_available_iced_modifier_bits_from_original_named_callback_no_numlock_alias() {
        let named = Modifiers { shift: true, ctrl: true, alt: true, logo: true, caps_lock: true, num_lock: true };
        assert_eq!(modifiers(&named), IcedModifiers::SHIFT|IcedModifiers::CTRL|IcedModifiers::ALT|IcedModifiers::LOGO|IcedModifiers::CAPS_LOCK);
        assert_eq!(modifiers(&Modifiers { num_lock: true, ..Default::default() }), IcedModifiers::NONE);
        assert_eq!(modifiers(&Modifiers::default()), IcedModifiers::NONE);
    }
    #[test]
    fn missing_stale_mismatched_and_recreated_event_conversion_refuses() {
        let (mut map, mut context, frame) = setup(Kind::Press, None, 0, RawModifiers::default(), Modifiers::default(), 98);
        assert_eq!(convert(&map,&context,&frame).unwrap_err(),LookupError::EventMismatch);
        map.clear();assert_eq!(convert(&map,&context,&frame).unwrap_err(),LookupError::MissingKeymap);
        context.enter();assert_eq!(convert(&map,&context,&frame).unwrap_err(),LookupError::StaleEvent);
        let fresh = context.capture(Kind::Press, 99, frame.event().clone()).unwrap();
        assert_eq!(convert(&map,&context,&fresh).unwrap_err(),LookupError::MissingModifiers);
    }
    #[test]
    fn conversion_and_debug_do_not_mutate_or_log_private_event_values() {
        let (map, mut context, frame) = setup(Kind::Press, Some("private"), 0, RawModifiers::default(), Modifiers::default(), 97);
        let converted = convert(&map,&context,&frame).unwrap();
        assert_eq!(format!("{converted:?}"), "Converted { .. }");assert!(context.is_current(&frame));
        context.invalidate();assert!(!context.is_current(converted.original()));
        assert_eq!(converted.original().event().utf8.as_deref(), Some("private"));
    }
}
