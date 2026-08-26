"""Verify the package can be imported and basic metadata is accessible."""


def test_package_importable():
    import research_tool

    assert research_tool.__doc__ is not None


def test_package_has_subpackages():
    from research_tool import (
        cli,
        config,
        core,
        domain,
        implementations,
        infrastructure,
        interfaces,
    )

    assert all([core, domain, interfaces, infrastructure, implementations, config, cli])
