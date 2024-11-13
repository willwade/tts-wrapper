from tts_wrapper import SSMLNode


def test_simple_tag() -> None:
    assert str(SSMLNode("speak")) == "<speak></speak>"


def test_tag_with_attrs() -> None:
    assert str(SSMLNode("speak", {"foo": "bar"})) == '<speak foo="bar"></speak>'


def test_tag_with_children() -> None:
    assert (
        str(SSMLNode("speak", children=[SSMLNode("a"), SSMLNode("b")]))
        == "<speak><a></a><b></b></speak>"
    )


def test_add_node() -> None:
    assert str(SSMLNode("speak").add(SSMLNode("a"))) == "<speak><a></a></speak>"


def test_add_text() -> None:
    assert (
        str(SSMLNode("speak").add(SSMLNode("a").add("hello")))
        == "<speak><a>hello</a></speak>"
    )


def test_render_multiple_children() -> None:
    children = ["Hello, ", SSMLNode("break", attrs={"time": "3s"}), " World!"]
    assert (
        str(SSMLNode("speak", children=children))
        == '<speak>Hello, <break time="3s"></break> World!</speak>'
    )
