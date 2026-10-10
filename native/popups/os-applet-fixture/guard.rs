// Private test copies only; never included in a deployed applet.
fn studio_fixture_guard(flag: &str, get: impl Fn(&str) -> Option<String>) -> bool {
    if get("STUDIO_PRIVATE_TEST").as_deref() != Some("1")
        || get(flag).as_deref() != Some("1")
        || get("DBUS_SYSTEM_BUS_ADDRESS").as_deref() != Some("unix:path=/dev/null")
    {
        return false;
    }
    let Some(root) = get("STUDIO_TEST_ROOT") else { return false };
    let root = std::path::Path::new(&root);
    if !root.is_absolute() || root == std::path::Path::new("/")
        || root.components().any(|p| p == std::path::Component::ParentDir)
    {
        return false;
    }
    for key in ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"] {
        let Some(value) = get(key) else { return false };
        let path = std::path::Path::new(&value);
        if path == root || !path.starts_with(root)
            || path.components().any(|p| p == std::path::Component::ParentDir)
        {
            return false;
        }
    }
    let Some(runtime) = get("XDG_RUNTIME_DIR") else { return false };
    let runtime = std::path::Path::new(&runtime);
    runtime.is_absolute() && !runtime.starts_with("/run/user")
        && !runtime.components().any(|p| p == std::path::Component::ParentDir)
}

fn studio_private_fixture(flag: &str) -> bool {
    studio_fixture_guard(flag, |key| std::env::var(key).ok())
}

#[cfg(test)]
mod studio_fixture_tests {
    use super::studio_fixture_guard;
    use std::collections::HashMap;

    #[test]
    fn only_disposable_configuration_runtime_and_disabled_system_bus_can_autotrigger() {
        let mut env: HashMap<&str, &str> = HashMap::from([
            ("STUDIO_PRIVATE_TEST", "1"),
            ("STUDIO_PRIVATE_AUTO_CALENDAR", "1"),
            ("STUDIO_TEST_ROOT", "/tmp/studio-review"),
            ("XDG_CONFIG_HOME", "/tmp/studio-review/config"),
            ("XDG_DATA_HOME", "/tmp/studio-review/data"),
            ("XDG_CACHE_HOME", "/tmp/studio-review/cache"),
            ("XDG_RUNTIME_DIR", "/tmp/studio-short-runtime"),
            ("DBUS_SYSTEM_BUS_ADDRESS", "unix:path=/dev/null"),
        ]);
        let check = |values: &HashMap<&str, &str>| {
            studio_fixture_guard("STUDIO_PRIVATE_AUTO_CALENDAR", |key| values.get(key).map(|x| x.to_string()))
        };
        assert!(check(&env));
        for (key, invalid) in [
            ("STUDIO_PRIVATE_TEST", "0"),
            ("STUDIO_PRIVATE_AUTO_CALENDAR", "0"),
            ("XDG_CONFIG_HOME", "/home/test/.config"),
            ("XDG_CONFIG_HOME", "/tmp/studio-review/../other-config"),
            ("XDG_RUNTIME_DIR", "/run/user/1000"),
            ("XDG_RUNTIME_DIR", "/tmp/../run/user/1000"),
            ("DBUS_SYSTEM_BUS_ADDRESS", "unix:path=/run/dbus/system_bus_socket"),
            ("STUDIO_TEST_ROOT", "/"),
        ] {
            let saved = env.insert(key, invalid).unwrap();
            assert!(!check(&env), "guard accepted {key}={invalid}");
            env.insert(key, saved);
        }
        env.remove("XDG_DATA_HOME");
        assert!(!check(&env));
    }
}
