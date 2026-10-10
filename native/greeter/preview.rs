// An ordinary Wayland window for appearance review. This path has no PAM,
// greetd IPC, logind lock signal, session-lock request or authentication state.
use cosmic::app::{Core, Settings, Task};
use cosmic::iced::{Alignment, Length, Size};
use cosmic::{Element, executor, widget};

pub fn run() -> cosmic::iced::Result {
    crate::studio::load_fonts();
    cosmic::app::run::<Preview>(
        Settings::default()
            .theme(crate::studio::dark_theme())
            .default_font(cosmic::iced::Font::with_name("Archivo"))
            .size(Size::new(960.0, 440.0))
            .exit_on_close(true),
        (),
    )
}

struct Preview {
    core: Core,
    time: crate::time::Time,
}

#[derive(Debug, Clone)]
pub enum Message {
    None,
}

impl cosmic::Application for Preview {
    type Executor = executor::Default;
    type Flags = ();
    type Message = Message;
    const APP_ID: &'static str = "com.adamnolle.CosmicStudio.LockAppearancePreview";

    fn core(&self) -> &Core { &self.core }
    fn core_mut(&mut self) -> &mut Core { &mut self.core }
    fn init(mut core: Core, _: ()) -> (Self, Task<Message>) {
        core.set_header_title("COSMIC Studio · lock appearance preview".into());
        (
            Self { core, time: crate::time::Time::new() },
            cosmic::command::set_theme(crate::studio::dark_theme()),
        )
    }
    fn update(&mut self, _: Message) -> Task<Message> { Task::none() }
    fn view(&self) -> Element<'_, Message> {
        let identity = widget::column::with_capacity(5)
            .spacing(16)
            .align_x(Alignment::Center)
            .push(widget::icon::from_name("system-lock-screen-symbolic").size(48))
            .push(widget::text::title4("COSMIC Studio"))
            .push(widget::secure_input("Password", "", None, true))
            .push(widget::text::caption("Appearance preview · authentication is disabled"))
            .width(Length::FillPortion(2));
        let content = widget::row::with_capacity(2)
            .spacing(32)
            .align_y(Alignment::Center)
            .push(widget::container(self.time.date_time_widget(false)).width(Length::FillPortion(3)))
            .push(identity);
        widget::container(content).padding(32).center(Length::Fill).into()
    }
}
