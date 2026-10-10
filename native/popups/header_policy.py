"""Exactly scoped native focused HeaderBar icons; no widget palette rewrite."""


def neutral_header(text, legacy=False):
    background = 'cosmic.background.on' if legacy else 'cosmic.background(self.transparent).on'
    before = f'''                let (icon_color, text_color) = if *focused {{
                    (
                        Color::from(cosmic.accent_text_color()),
                        Color::from({background}),
                    )'''
    after = f'''                let (icon_color, text_color) = if *focused {{
                    let icon_color = if crate::popup_policy::neutral_header_icon(
                        crate::popup_policy::enabled(), cosmic.is_high_contrast,
                    ) {{
                        Color::from({background})
                    }} else {{
                        Color::from(cosmic.accent_text_color())
                    }};
                    (icon_color, Color::from({background}))'''
    if text.count(before) != 1:
        raise ValueError('Pinned focused HeaderBar source shape changed.')
    return text.replace(before, after, 1)
