// SPDX-License-Identifier: MIT
// Adapted from exact Iced 87e1787f Wayland keymap (commented upstream cases retained).
// Borrowed from winit in original source. See pinned-iced-keymap.LICENSE / NOTICE.
use cosmic::iced::keyboard::{Key, Location, key::{Named, Code, Physical, NativeCode}};
use smithay::input::keyboard::xkb::keysyms;

pub(crate) fn scancode_to_physicalkey(scancode: u32) -> Physical {
    // The keycode values are taken from linux/include/uapi/linux/input-event-codes.h, as
    // libxkbcommon's documentation seems to suggest that the keycode values we're interested in
    // are defined by the Linux kernel. If Winit programs end up being run on other Unix-likes,
    // I can only hope they agree on what the keycodes mean.
    //
    // Some of the keycodes are likely superfluous for our purposes, and some are ones which are
    // difficult to test the correctness of, or discover the purpose of. Because of this, they've
    // either been commented out here, or not included at all.
    Physical::Code(match scancode {
        0 => return Physical::Unidentified(NativeCode::Xkb(0)),
        1 => Code::Escape,
        2 => Code::Digit1,
        3 => Code::Digit2,
        4 => Code::Digit3,
        5 => Code::Digit4,
        6 => Code::Digit5,
        7 => Code::Digit6,
        8 => Code::Digit7,
        9 => Code::Digit8,
        10 => Code::Digit9,
        11 => Code::Digit0,
        12 => Code::Minus,
        13 => Code::Equal,
        14 => Code::Backspace,
        15 => Code::Tab,
        16 => Code::KeyQ,
        17 => Code::KeyW,
        18 => Code::KeyE,
        19 => Code::KeyR,
        20 => Code::KeyT,
        21 => Code::KeyY,
        22 => Code::KeyU,
        23 => Code::KeyI,
        24 => Code::KeyO,
        25 => Code::KeyP,
        26 => Code::BracketLeft,
        27 => Code::BracketRight,
        28 => Code::Enter,
        29 => Code::ControlLeft,
        30 => Code::KeyA,
        31 => Code::KeyS,
        32 => Code::KeyD,
        33 => Code::KeyF,
        34 => Code::KeyG,
        35 => Code::KeyH,
        36 => Code::KeyJ,
        37 => Code::KeyK,
        38 => Code::KeyL,
        39 => Code::Semicolon,
        40 => Code::Quote,
        41 => Code::Backquote,
        42 => Code::ShiftLeft,
        43 => Code::Backslash,
        44 => Code::KeyZ,
        45 => Code::KeyX,
        46 => Code::KeyC,
        47 => Code::KeyV,
        48 => Code::KeyB,
        49 => Code::KeyN,
        50 => Code::KeyM,
        51 => Code::Comma,
        52 => Code::Period,
        53 => Code::Slash,
        54 => Code::ShiftRight,
        55 => Code::NumpadMultiply,
        56 => Code::AltLeft,
        57 => Code::Space,
        58 => Code::CapsLock,
        59 => Code::F1,
        60 => Code::F2,
        61 => Code::F3,
        62 => Code::F4,
        63 => Code::F5,
        64 => Code::F6,
        65 => Code::F7,
        66 => Code::F8,
        67 => Code::F9,
        68 => Code::F10,
        69 => Code::NumLock,
        70 => Code::ScrollLock,
        71 => Code::Numpad7,
        72 => Code::Numpad8,
        73 => Code::Numpad9,
        74 => Code::NumpadSubtract,
        75 => Code::Numpad4,
        76 => Code::Numpad5,
        77 => Code::Numpad6,
        78 => Code::NumpadAdd,
        79 => Code::Numpad1,
        80 => Code::Numpad2,
        81 => Code::Numpad3,
        82 => Code::Numpad0,
        83 => Code::NumpadDecimal,
        85 => Code::Lang5,
        86 => Code::IntlBackslash,
        87 => Code::F11,
        88 => Code::F12,
        89 => Code::IntlRo,
        90 => Code::Lang3,
        91 => Code::Lang4,
        92 => Code::Convert,
        93 => Code::KanaMode,
        94 => Code::NonConvert,
        // 95 => Code::KPJPCOMMA,
        96 => Code::NumpadEnter,
        97 => Code::ControlRight,
        98 => Code::NumpadDivide,
        99 => Code::PrintScreen,
        100 => Code::AltRight,
        // 101 => Code::LINEFEED,
        102 => Code::Home,
        103 => Code::ArrowUp,
        104 => Code::PageUp,
        105 => Code::ArrowLeft,
        106 => Code::ArrowRight,
        107 => Code::End,
        108 => Code::ArrowDown,
        109 => Code::PageDown,
        110 => Code::Insert,
        111 => Code::Delete,
        // 112 => Code::MACRO,
        113 => Code::AudioVolumeMute,
        114 => Code::AudioVolumeDown,
        115 => Code::AudioVolumeUp,
        // 116 => Code::POWER,
        117 => Code::NumpadEqual,
        // 118 => Code::KPPLUSMINUS,
        119 => Code::Pause,
        // 120 => Code::SCALE,
        121 => Code::NumpadComma,
        122 => Code::Lang1,
        123 => Code::Lang2,
        124 => Code::IntlYen,
        125 => Code::SuperLeft,
        126 => Code::SuperRight,
        127 => Code::ContextMenu,
        // 128 => Code::STOP,
        // 129 => Code::AGAIN,
        // 130 => Code::PROPS,
        // 131 => Code::UNDO,
        // 132 => Code::FRONT,
        // 133 => Code::COPY,
        // 134 => Code::OPEN,
        // 135 => Code::PASTE,
        // 136 => Code::FIND,
        // 137 => Code::CUT,
        // 138 => Code::HELP,
        // 139 => Code::MENU,
        // 140 => Code::CALC,
        // 141 => Code::SETUP,
        // 142 => Code::SLEEP,
        // 143 => Code::WAKEUP,
        // 144 => Code::FILE,
        // 145 => Code::SENDFILE,
        // 146 => Code::DELETEFILE,
        // 147 => Code::XFER,
        // 148 => Code::PROG1,
        // 149 => Code::PROG2,
        // 150 => Code::WWW,
        // 151 => Code::MSDOS,
        // 152 => Code::COFFEE,
        // 153 => Code::ROTATE_DISPLAY,
        // 154 => Code::CYCLEWINDOWS,
        // 155 => Code::MAIL,
        // 156 => Code::BOOKMARKS,
        // 157 => Code::COMPUTER,
        // 158 => Code::BACK,
        // 159 => Code::FORWARD,
        // 160 => Code::CLOSECD,
        // 161 => Code::EJECTCD,
        // 162 => Code::EJECTCLOSECD,
        163 => Code::MediaTrackNext,
        164 => Code::MediaPlayPause,
        165 => Code::MediaTrackPrevious,
        166 => Code::MediaStop,
        // 167 => Code::RECORD,
        // 168 => Code::REWIND,
        // 169 => Code::PHONE,
        // 170 => Code::ISO,
        // 171 => Code::CONFIG,
        // 172 => Code::HOMEPAGE,
        // 173 => Code::REFRESH,
        // 174 => Code::EXIT,
        // 175 => Code::MOVE,
        // 176 => Code::EDIT,
        // 177 => Code::SCROLLUP,
        // 178 => Code::SCROLLDOWN,
        // 179 => Code::KPLEFTPAREN,
        // 180 => Code::KPRIGHTPAREN,
        // 181 => Code::NEW,
        // 182 => Code::REDO,
        183 => Code::F13,
        184 => Code::F14,
        185 => Code::F15,
        186 => Code::F16,
        187 => Code::F17,
        188 => Code::F18,
        189 => Code::F19,
        190 => Code::F20,
        191 => Code::F21,
        192 => Code::F22,
        193 => Code::F23,
        194 => Code::F24,
        // 200 => Code::PLAYCD,
        // 201 => Code::PAUSECD,
        // 202 => Code::PROG3,
        // 203 => Code::PROG4,
        // 204 => Code::DASHBOARD,
        // 205 => Code::SUSPEND,
        // 206 => Code::CLOSE,
        // 207 => Code::PLAY,
        // 208 => Code::FASTFORWARD,
        // 209 => Code::BASSBOOST,
        // 210 => Code::PRINT,
        // 211 => Code::HP,
        // 212 => Code::CAMERA,
        // 213 => Code::SOUND,
        // 214 => Code::QUESTION,
        // 215 => Code::EMAIL,
        // 216 => Code::CHAT,
        // 217 => Code::SEARCH,
        // 218 => Code::CONNECT,
        // 219 => Code::FINANCE,
        // 220 => Code::SPORT,
        // 221 => Code::SHOP,
        // 222 => Code::ALTERASE,
        // 223 => Code::CANCEL,
        // 224 => Code::BRIGHTNESSDOW,
        // 225 => Code::BRIGHTNESSU,
        // 226 => Code::MEDIA,
        // 227 => Code::SWITCHVIDEOMODE,
        // 228 => Code::KBDILLUMTOGGLE,
        // 229 => Code::KBDILLUMDOWN,
        // 230 => Code::KBDILLUMUP,
        // 231 => Code::SEND,
        // 232 => Code::REPLY,
        // 233 => Code::FORWARDMAIL,
        // 234 => Code::SAVE,
        // 235 => Code::DOCUMENTS,
        // 236 => Code::BATTERY,
        // 237 => Code::BLUETOOTH,
        // 238 => Code::WLAN,
        // 239 => Code::UWB,
        240 => return Physical::Unidentified(NativeCode::Unidentified),
        // 241 => Code::VIDEO_NEXT,
        // 242 => Code::VIDEO_PREV,
        // 243 => Code::BRIGHTNESS_CYCLE,
        // 244 => Code::BRIGHTNESS_AUTO,
        // 245 => Code::DISPLAY_OFF,
        // 246 => Code::WWAN,
        // 247 => Code::RFKILL,
        // 248 => Code::KEY_MICMUTE,
        _ => return Physical::Unidentified(NativeCode::Xkb(scancode)),
    })
}

pub(crate) fn keysym_to_key(keysym: u32) -> Key {
    Key::Named(match keysym {
        // TTY function keys
        keysyms::KEY_BackSpace => Named::Backspace,
        keysyms::KEY_Tab => Named::Tab,
        // keysyms::Linefeed => Named::Linefeed,
        keysyms::KEY_Clear => Named::Clear,
        keysyms::KEY_Return => Named::Enter,
        keysyms::KEY_Pause => Named::Pause,
        keysyms::KEY_Scroll_Lock => Named::ScrollLock,
        keysyms::KEY_Sys_Req => Named::PrintScreen,
        keysyms::KEY_Escape => Named::Escape,
        keysyms::KEY_Delete => Named::Delete,

        // IME keys
        keysyms::KEY_Multi_key => Named::Compose,
        keysyms::KEY_Codeinput => Named::CodeInput,
        keysyms::KEY_SingleCandidate => Named::SingleCandidate,
        keysyms::KEY_MultipleCandidate => Named::AllCandidates,
        keysyms::KEY_PreviousCandidate => Named::PreviousCandidate,

        // Japanese key
        keysyms::KEY_Kanji => Named::KanjiMode,
        keysyms::KEY_Muhenkan => Named::NonConvert,
        keysyms::KEY_Henkan_Mode => Named::Convert,
        keysyms::KEY_Romaji => Named::Romaji,
        keysyms::KEY_Hiragana => Named::Hiragana,
        keysyms::KEY_Hiragana_Katakana => Named::HiraganaKatakana,
        keysyms::KEY_Zenkaku => Named::Zenkaku,
        keysyms::KEY_Hankaku => Named::Hankaku,
        keysyms::KEY_Zenkaku_Hankaku => Named::ZenkakuHankaku,
        // keysyms::Touroku => Named::Touroku,
        // keysyms::Massyo => Named::Massyo,
        keysyms::KEY_Kana_Lock => Named::KanaMode,
        keysyms::KEY_Kana_Shift => Named::KanaMode,
        keysyms::KEY_Eisu_Shift => Named::Alphanumeric,
        keysyms::KEY_Eisu_toggle => Named::Alphanumeric,
        // NOTE: The next three items are aliases for values we've already mapped.
        // keysyms::Kanji_Bangou => Named::CodeInput,
        // keysyms::Zen_Koho => Named::AllCandidates,
        // keysyms::Mae_Koho => Named::PreviousCandidate,

        // Cursor control & motion
        keysyms::KEY_Home => Named::Home,
        keysyms::KEY_Left => Named::ArrowLeft,
        keysyms::KEY_Up => Named::ArrowUp,
        keysyms::KEY_Right => Named::ArrowRight,
        keysyms::KEY_Down => Named::ArrowDown,
        // keysyms::Prior => Named::PageUp,
        keysyms::KEY_Page_Up => Named::PageUp,
        // keysyms::Next => Named::PageDown,
        keysyms::KEY_Page_Down => Named::PageDown,
        keysyms::KEY_End => Named::End,
        // keysyms::Begin => Named::Begin,

        // Misc. functions
        keysyms::KEY_Select => Named::Select,
        keysyms::KEY_Print => Named::PrintScreen,
        keysyms::KEY_Execute => Named::Execute,
        keysyms::KEY_Insert => Named::Insert,
        keysyms::KEY_Undo => Named::Undo,
        keysyms::KEY_Redo => Named::Redo,
        keysyms::KEY_Menu => Named::ContextMenu,
        keysyms::KEY_Find => Named::Find,
        keysyms::KEY_Cancel => Named::Cancel,
        keysyms::KEY_Help => Named::Help,
        keysyms::KEY_Break => Named::Pause,
        keysyms::KEY_Mode_switch => Named::ModeChange,
        // keysyms::script_switch => Named::ModeChange,
        keysyms::KEY_Num_Lock => Named::NumLock,

        // Keypad keys
        // keysyms::KP_Space => return Key::Character(" "),
        keysyms::KEY_KP_Tab => Named::Tab,
        keysyms::KEY_KP_Enter => Named::Enter,
        keysyms::KEY_KP_F1 => Named::F1,
        keysyms::KEY_KP_F2 => Named::F2,
        keysyms::KEY_KP_F3 => Named::F3,
        keysyms::KEY_KP_F4 => Named::F4,
        keysyms::KEY_KP_Home => Named::Home,
        keysyms::KEY_KP_Left => Named::ArrowLeft,
        keysyms::KEY_KP_Up => Named::ArrowUp,
        keysyms::KEY_KP_Right => Named::ArrowRight,
        keysyms::KEY_KP_Down => Named::ArrowDown,
        // keysyms::KP_Prior => Named::PageUp,
        keysyms::KEY_KP_Page_Up => Named::PageUp,
        // keysyms::KP_Next => Named::PageDown,
        keysyms::KEY_KP_Page_Down => Named::PageDown,
        keysyms::KEY_KP_End => Named::End,
        // This is the key labeled "5" on the numpad when NumLock is off.
        // keysyms::KP_Begin => Named::Begin,
        keysyms::KEY_KP_Insert => Named::Insert,
        keysyms::KEY_KP_Delete => Named::Delete,
        // keysyms::KP_Equal => Named::Equal,
        // keysyms::KP_Multiply => Named::Multiply,
        // keysyms::KP_Add => Named::Add,
        // keysyms::KP_Separator => Named::Separator,
        // keysyms::KP_Subtract => Named::Subtract,
        // keysyms::KP_Decimal => Named::Decimal,
        // keysyms::KP_Divide => Named::Divide,

        // keysyms::KP_0 => return Key::Character("0"),
        // keysyms::KP_1 => return Key::Character("1"),
        // keysyms::KP_2 => return Key::Character("2"),
        // keysyms::KP_3 => return Key::Character("3"),
        // keysyms::KP_4 => return Key::Character("4"),
        // keysyms::KP_5 => return Key::Character("5"),
        // keysyms::KP_6 => return Key::Character("6"),
        // keysyms::KP_7 => return Key::Character("7"),
        // keysyms::KP_8 => return Key::Character("8"),
        // keysyms::KP_9 => return Key::Character("9"),

        // Function keys
        keysyms::KEY_F1 => Named::F1,
        keysyms::KEY_F2 => Named::F2,
        keysyms::KEY_F3 => Named::F3,
        keysyms::KEY_F4 => Named::F4,
        keysyms::KEY_F5 => Named::F5,
        keysyms::KEY_F6 => Named::F6,
        keysyms::KEY_F7 => Named::F7,
        keysyms::KEY_F8 => Named::F8,
        keysyms::KEY_F9 => Named::F9,
        keysyms::KEY_F10 => Named::F10,
        keysyms::KEY_F11 => Named::F11,
        keysyms::KEY_F12 => Named::F12,
        keysyms::KEY_F13 => Named::F13,
        keysyms::KEY_F14 => Named::F14,
        keysyms::KEY_F15 => Named::F15,
        keysyms::KEY_F16 => Named::F16,
        keysyms::KEY_F17 => Named::F17,
        keysyms::KEY_F18 => Named::F18,
        keysyms::KEY_F19 => Named::F19,
        keysyms::KEY_F20 => Named::F20,
        keysyms::KEY_F21 => Named::F21,
        keysyms::KEY_F22 => Named::F22,
        keysyms::KEY_F23 => Named::F23,
        keysyms::KEY_F24 => Named::F24,
        keysyms::KEY_F25 => Named::F25,
        keysyms::KEY_F26 => Named::F26,
        keysyms::KEY_F27 => Named::F27,
        keysyms::KEY_F28 => Named::F28,
        keysyms::KEY_F29 => Named::F29,
        keysyms::KEY_F30 => Named::F30,
        keysyms::KEY_F31 => Named::F31,
        keysyms::KEY_F32 => Named::F32,
        keysyms::KEY_F33 => Named::F33,
        keysyms::KEY_F34 => Named::F34,
        keysyms::KEY_F35 => Named::F35,

        // Modifiers
        keysyms::KEY_Shift_L => Named::Shift,
        keysyms::KEY_Shift_R => Named::Shift,
        keysyms::KEY_Control_L => Named::Control,
        keysyms::KEY_Control_R => Named::Control,
        keysyms::KEY_Caps_Lock => Named::CapsLock,
        // keysyms::Shift_Lock => Named::ShiftLock,

        // keysyms::Meta_L => Named::Meta,
        // keysyms::Meta_R => Named::Meta,
        keysyms::KEY_Alt_L => Named::Alt,
        keysyms::KEY_Alt_R => Named::Alt,
        keysyms::KEY_Super_L => Named::Super,
        keysyms::KEY_Super_R => Named::Super,
        keysyms::KEY_Hyper_L => Named::Hyper,
        keysyms::KEY_Hyper_R => Named::Hyper,

        // XKB function and modifier keys
        // keysyms::ISO_Lock => Named::IsoLock,
        // keysyms::ISO_Level2_Latch => Named::IsoLevel2Latch,
        keysyms::KEY_ISO_Level3_Shift => Named::AltGraph,
        keysyms::KEY_ISO_Level3_Latch => Named::AltGraph,
        keysyms::KEY_ISO_Level3_Lock => Named::AltGraph,
        // keysyms::ISO_Level5_Shift => Named::IsoLevel5Shift,
        // keysyms::ISO_Level5_Latch => Named::IsoLevel5Latch,
        // keysyms::ISO_Level5_Lock => Named::IsoLevel5Lock,
        // keysyms::ISO_Group_Shift => Named::IsoGroupShift,
        // keysyms::ISO_Group_Latch => Named::IsoGroupLatch,
        // keysyms::ISO_Group_Lock => Named::IsoGroupLock,
        keysyms::KEY_ISO_Next_Group => Named::GroupNext,
        // keysyms::ISO_Next_Group_Lock => Named::GroupNextLock,
        keysyms::KEY_ISO_Prev_Group => Named::GroupPrevious,
        // keysyms::ISO_Prev_Group_Lock => Named::GroupPreviousLock,
        keysyms::KEY_ISO_First_Group => Named::GroupFirst,
        // keysyms::ISO_First_Group_Lock => Named::GroupFirstLock,
        keysyms::KEY_ISO_Last_Group => Named::GroupLast,
        // keysyms::ISO_Last_Group_Lock => Named::GroupLastLock,
        //
        keysyms::KEY_ISO_Left_Tab => Named::Tab,
        // keysyms::ISO_Move_Line_Up => Named::IsoMoveLineUp,
        // keysyms::ISO_Move_Line_Down => Named::IsoMoveLineDown,
        // keysyms::ISO_Partial_Line_Up => Named::IsoPartialLineUp,
        // keysyms::ISO_Partial_Line_Down => Named::IsoPartialLineDown,
        // keysyms::ISO_Partial_Space_Left => Named::IsoPartialSpaceLeft,
        // keysyms::ISO_Partial_Space_Right => Named::IsoPartialSpaceRight,
        // keysyms::ISO_Set_Margin_Left => Named::IsoSetMarginLeft,
        // keysyms::ISO_Set_Margin_Right => Named::IsoSetMarginRight,
        // keysyms::ISO_Release_Margin_Left => Named::IsoReleaseMarginLeft,
        // keysyms::ISO_Release_Margin_Right => Named::IsoReleaseMarginRight,
        // keysyms::ISO_Release_Both_Margins => Named::IsoReleaseBothMargins,
        // keysyms::ISO_Fast_Cursor_Left => Named::IsoFastCursorLeft,
        // keysyms::ISO_Fast_Cursor_Right => Named::IsoFastCursorRight,
        // keysyms::ISO_Fast_Cursor_Up => Named::IsoFastCursorUp,
        // keysyms::ISO_Fast_Cursor_Down => Named::IsoFastCursorDown,
        // keysyms::ISO_Continuous_Underline => Named::IsoContinuousUnderline,
        // keysyms::ISO_Discontinuous_Underline => Named::IsoDiscontinuousUnderline,
        // keysyms::ISO_Emphasize => Named::IsoEmphasize,
        // keysyms::ISO_Center_Object => Named::IsoCenterObject,
        keysyms::KEY_ISO_Enter => Named::Enter,

        // dead_grave..dead_currency

        // dead_lowline..dead_longsolidusoverlay

        // dead_a..dead_capital_schwa

        // dead_greek

        // First_Virtual_Screen..Terminate_Server

        // AccessX_Enable..AudibleBell_Enable

        // Pointer_Left..Pointer_Drag5

        // Pointer_EnableKeys..Pointer_DfltBtnPrev

        // ch..C_H

        // 3270 terminal keys
        // keysyms::3270_Duplicate => Named::Duplicate,
        // keysyms::3270_FieldMark => Named::FieldMark,
        // keysyms::3270_Right2 => Named::Right2,
        // keysyms::3270_Left2 => Named::Left2,
        // keysyms::3270_BackTab => Named::BackTab,
        keysyms::KEY_3270_EraseEOF => Named::EraseEof,
        // keysyms::3270_EraseInput => Named::EraseInput,
        // keysyms::3270_Reset => Named::Reset,
        // keysyms::3270_Quit => Named::Quit,
        // keysyms::3270_PA1 => Named::Pa1,
        // keysyms::3270_PA2 => Named::Pa2,
        // keysyms::3270_PA3 => Named::Pa3,
        // keysyms::3270_Test => Named::Test,
        keysyms::KEY_3270_Attn => Named::Attn,
        // keysyms::3270_CursorBlink => Named::CursorBlink,
        // keysyms::3270_AltCursor => Named::AltCursor,
        // keysyms::3270_KeyClick => Named::KeyClick,
        // keysyms::3270_Jump => Named::Jump,
        // keysyms::3270_Ident => Named::Ident,
        // keysyms::3270_Rule => Named::Rule,
        // keysyms::3270_Copy => Named::Copy,
        keysyms::KEY_3270_Play => Named::Play,
        // keysyms::3270_Setup => Named::Setup,
        // keysyms::3270_Record => Named::Record,
        // keysyms::3270_ChangeScreen => Named::ChangeScreen,
        // keysyms::3270_DeleteWord => Named::DeleteWord,
        keysyms::KEY_3270_ExSelect => Named::ExSel,
        keysyms::KEY_3270_CursorSelect => Named::CrSel,
        keysyms::KEY_3270_PrintScreen => Named::PrintScreen,
        keysyms::KEY_3270_Enter => Named::Enter,

        keysyms::KEY_space => {
            return Key::Character(" ".into());
        }
        // exclam..Sinh_kunddaliya

        // XFree86
        // keysyms::XF86_ModeLock => Named::ModeLock,

        // XFree86 - Backlight controls
        keysyms::KEY_XF86MonBrightnessUp => Named::BrightnessUp,
        keysyms::KEY_XF86MonBrightnessDown => Named::BrightnessDown,
        // keysyms::XF86_KbdLightOnOff => Named::LightOnOff,
        // keysyms::XF86_KbdBrightnessUp => Named::KeyboardBrightnessUp,
        // keysyms::XF86_KbdBrightnessDown => Named::KeyboardBrightnessDown,

        // XFree86 - "Internet"
        keysyms::KEY_XF86Standby => Named::Standby,
        keysyms::KEY_XF86AudioLowerVolume => Named::AudioVolumeDown,
        keysyms::KEY_XF86AudioRaiseVolume => Named::AudioVolumeUp,
        keysyms::KEY_XF86AudioPlay => Named::MediaPlay,
        keysyms::KEY_XF86AudioStop => Named::MediaStop,
        keysyms::KEY_XF86AudioPrev => Named::MediaTrackPrevious,
        keysyms::KEY_XF86AudioNext => Named::MediaTrackNext,
        keysyms::KEY_XF86HomePage => Named::BrowserHome,
        keysyms::KEY_XF86Mail => Named::LaunchMail,
        // keysyms::XF86_Start => Named::Start,
        keysyms::KEY_XF86Search => Named::BrowserSearch,
        keysyms::KEY_XF86AudioRecord => Named::MediaRecord,

        // XFree86 - PDA
        keysyms::KEY_XF86Calculator => Named::LaunchApplication2,
        // keysyms::XF86_Memo => Named::Memo,
        // keysyms::XF86_ToDoList => Named::ToDoList,
        keysyms::KEY_XF86Calendar => Named::LaunchCalendar,
        keysyms::KEY_XF86PowerDown => Named::Power,
        // keysyms::XF86_ContrastAdjust => Named::AdjustContrast,
        // keysyms::XF86_RockerUp => Named::RockerUp,
        // keysyms::XF86_RockerDown => Named::RockerDown,
        // keysyms::XF86_RockerEnter => Named::RockerEnter,

        // XFree86 - More "Internet"
        keysyms::KEY_XF86Back => Named::BrowserBack,
        keysyms::KEY_XF86Forward => Named::BrowserForward,
        // keysyms::XF86_Stop => Named::Stop,
        keysyms::KEY_XF86Refresh => Named::BrowserRefresh,
        keysyms::KEY_XF86PowerOff => Named::Power,
        keysyms::KEY_XF86WakeUp => Named::WakeUp,
        keysyms::KEY_XF86Eject => Named::Eject,
        keysyms::KEY_XF86ScreenSaver => Named::LaunchScreenSaver,
        keysyms::KEY_XF86WWW => Named::LaunchWebBrowser,
        keysyms::KEY_XF86Sleep => Named::Standby,
        keysyms::KEY_XF86Favorites => Named::BrowserFavorites,
        keysyms::KEY_XF86AudioPause => Named::MediaPause,
        // keysyms::XF86_AudioMedia => Named::AudioMedia,
        keysyms::KEY_XF86MyComputer => Named::LaunchApplication1,
        // keysyms::XF86_VendorHome => Named::VendorHome,
        // keysyms::XF86_LightBulb => Named::LightBulb,
        // keysyms::XF86_Shop => Named::BrowserShop,
        // keysyms::XF86_History => Named::BrowserHistory,
        // keysyms::XF86_OpenURL => Named::OpenUrl,
        // keysyms::XF86_AddFavorite => Named::AddFavorite,
        // keysyms::XF86_HotLinks => Named::HotLinks,
        // keysyms::XF86_BrightnessAdjust => Named::BrightnessAdjust,
        // keysyms::XF86_Finance => Named::BrowserFinance,
        // keysyms::XF86_Community => Named::BrowserCommunity,
        keysyms::KEY_XF86AudioRewind => Named::MediaRewind,
        // keysyms::XF86_BackForward => Key::???,
        // XF86_Launch0..XF86_LaunchF

        // XF86_ApplicationLeft..XF86_CD
        keysyms::KEY_XF86Calculater => Named::LaunchApplication2, // Nice typo, libxkbcommon :)
        // XF86_Clear
        keysyms::KEY_XF86Close => Named::Close,
        keysyms::KEY_XF86Copy => Named::Copy,
        keysyms::KEY_XF86Cut => Named::Cut,
        // XF86_Display..XF86_Documents
        keysyms::KEY_XF86Excel => Named::LaunchSpreadsheet,
        // XF86_Explorer..XF86iTouch
        keysyms::KEY_XF86LogOff => Named::LogOff,
        // XF86_Market..XF86_MenuPB
        keysyms::KEY_XF86MySites => Named::BrowserFavorites,
        keysyms::KEY_XF86New => Named::New,
        // XF86_News..XF86_OfficeHome
        keysyms::KEY_XF86Open => Named::Open,
        // XF86_Option
        keysyms::KEY_XF86Paste => Named::Paste,
        keysyms::KEY_XF86Phone => Named::LaunchPhone,
        // XF86_Q
        keysyms::KEY_XF86Reply => Named::MailReply,
        keysyms::KEY_XF86Reload => Named::BrowserRefresh,
        // XF86_RotateWindows..XF86_RotationKB
        keysyms::KEY_XF86Save => Named::Save,
        // XF86_ScrollUp..XF86_ScrollClick
        keysyms::KEY_XF86Send => Named::MailSend,
        keysyms::KEY_XF86Spell => Named::SpellCheck,
        keysyms::KEY_XF86SplitScreen => Named::SplitScreenToggle,
        // XF86_Support..XF86_User2KB
        keysyms::KEY_XF86Video => Named::LaunchMediaPlayer,
        // XF86_WheelButton
        keysyms::KEY_XF86Word => Named::LaunchWordProcessor,
        // XF86_Xfer
        keysyms::KEY_XF86ZoomIn => Named::ZoomIn,
        keysyms::KEY_XF86ZoomOut => Named::ZoomOut,

        // XF86_Away..XF86_Messenger
        keysyms::KEY_XF86WebCam => Named::LaunchWebCam,
        keysyms::KEY_XF86MailForward => Named::MailForward,
        // XF86_Pictures
        keysyms::KEY_XF86Music => Named::LaunchMusicPlayer,

        // XF86_Battery..XF86_UWB
        //
        keysyms::KEY_XF86AudioForward => Named::MediaFastForward,
        // XF86_AudioRepeat
        keysyms::KEY_XF86AudioRandomPlay => Named::RandomToggle,
        keysyms::KEY_XF86Subtitle => Named::Subtitle,
        keysyms::KEY_XF86AudioCycleTrack => Named::MediaAudioTrack,
        // XF86_CycleAngle..XF86_Blue
        //
        keysyms::KEY_XF86Suspend => Named::Standby,
        keysyms::KEY_XF86Hibernate => Named::Hibernate,
        // XF86_TouchpadToggle..XF86_TouchpadOff
        //
        keysyms::KEY_XF86AudioMute => Named::AudioVolumeMute,

        // XF86_Switch_VT_1..XF86_Switch_VT_12

        // XF86_Ungrab..XF86_ClearGrab
        keysyms::KEY_XF86Next_VMode => Named::VideoModeNext,
        // keysyms::XF86_Prev_VMode => Named::VideoModePrevious,
        // XF86_LogWindowTree..XF86_LogGrabInfo

        // SunFA_Grave..SunFA_Cedilla

        // keysyms::SunF36 => Named::F36 | Named::F11,
        // keysyms::SunF37 => Named::F37 | Named::F12,

        // keysyms::SunSys_Req => Named::PrintScreen,
        // The next couple of xkb (until SunStop) are already handled.
        // SunPrint_Screen..SunPageDown

        // SunUndo..SunFront
        keysyms::KEY_SunCopy => Named::Copy,
        keysyms::KEY_SunOpen => Named::Open,
        keysyms::KEY_SunPaste => Named::Paste,
        keysyms::KEY_SunCut => Named::Cut,

        // SunPowerSwitch
        keysyms::KEY_SunAudioLowerVolume => Named::AudioVolumeDown,
        keysyms::KEY_SunAudioMute => Named::AudioVolumeMute,
        keysyms::KEY_SunAudioRaiseVolume => Named::AudioVolumeUp,
        // SUN_VideoDegauss
        keysyms::KEY_SunVideoLowerBrightness => Named::BrightnessDown,
        keysyms::KEY_SunVideoRaiseBrightness => Named::BrightnessUp,
        // SunPowerSwitchShift
        //
        _ => return Key::Unidentified,
    })
}

pub(crate) fn keysym_location(keysym: u32) -> Location {
    match keysym {
        keysyms::KEY_Shift_L
        | keysyms::KEY_Control_L
        | keysyms::KEY_Meta_L
        | keysyms::KEY_Alt_L
        | keysyms::KEY_Super_L
        | keysyms::KEY_Hyper_L => Location::Left,
        keysyms::KEY_Shift_R
        | keysyms::KEY_Control_R
        | keysyms::KEY_Meta_R
        | keysyms::KEY_Alt_R
        | keysyms::KEY_Super_R
        | keysyms::KEY_Hyper_R => Location::Right,
        keysyms::KEY_KP_0
        | keysyms::KEY_KP_1
        | keysyms::KEY_KP_2
        | keysyms::KEY_KP_3
        | keysyms::KEY_KP_4
        | keysyms::KEY_KP_5
        | keysyms::KEY_KP_6
        | keysyms::KEY_KP_7
        | keysyms::KEY_KP_8
        | keysyms::KEY_KP_9
        | keysyms::KEY_KP_Space
        | keysyms::KEY_KP_Tab
        | keysyms::KEY_KP_Enter
        | keysyms::KEY_KP_F1
        | keysyms::KEY_KP_F2
        | keysyms::KEY_KP_F3
        | keysyms::KEY_KP_F4
        | keysyms::KEY_KP_Home
        | keysyms::KEY_KP_Left
        | keysyms::KEY_KP_Up
        | keysyms::KEY_KP_Right
        | keysyms::KEY_KP_Down
        | keysyms::KEY_KP_Page_Up
        | keysyms::KEY_KP_Page_Down
        | keysyms::KEY_KP_End
        | keysyms::KEY_KP_Begin
        | keysyms::KEY_KP_Insert
        | keysyms::KEY_KP_Delete
        | keysyms::KEY_KP_Equal
        | keysyms::KEY_KP_Multiply
        | keysyms::KEY_KP_Add
        | keysyms::KEY_KP_Separator
        | keysyms::KEY_KP_Subtract
        | keysyms::KEY_KP_Decimal
        | keysyms::KEY_KP_Divide => Location::Numpad,
        _ => Location::Standard,
    }
}
