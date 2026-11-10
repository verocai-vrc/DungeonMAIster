use clap::Parser;

/// Dungeon Meister: a 5E compatible solo engine where code resolves every rule.
#[derive(Debug, Parser)]
#[command(name = "meister", version)]
struct Cli {}

fn main() {
    let _cli = Cli::parse();
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::CommandFactory;

    #[test]
    fn cli_definition_is_valid() {
        Cli::command().debug_assert();
    }

    #[test]
    fn reports_the_package_version() {
        let mut cmd = Cli::command();
        cmd.build();
        assert_eq!(cmd.render_version(), "meister 2.0.0-dev\n");
    }
}
