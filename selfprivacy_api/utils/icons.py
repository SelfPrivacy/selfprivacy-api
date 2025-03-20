import bleach

ALLOWED_TAGS = [
    "svg",
    "g",
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "text",
    "tspan",
    "tref",
    "textPath",
    "altGlyph",
    "altGlyphDef",
    "altGlyphItem",
    "glyph",
    "glyphRef",
    "marker",
    "color-profile",
    "defs",
    "desc",
    "metadata",
    "title",
    "symbol",
    "use",
    "image",
    "switch",
]
ALLOWED_ATTRIBUTES = {
    "*": ["class", "transform"],
    "svg": ["width", "height", "viewBox", "xmlns"],
    "path": ["d", "fill", "stroke", "stroke-width"],
    "rect": ["x", "y", "width", "height", "rx", "ry", "fill", "stroke", "stroke-width"],
    "circle": ["cx", "cy", "r", "fill", "stroke", "stroke-width"],
    "ellipse": ["cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width"],
    "line": ["x1", "y1", "x2", "y2", "stroke", "stroke-width"],
    "polyline": ["points", "fill", "stroke", "stroke-width"],
    "polygon": ["points", "fill", "stroke", "stroke-width"],
    "text": [
        "x",
        "y",
        "dx",
        "dy",
        "text-anchor",
        "font-family",
        "font-size",
        "fill",
        "stroke",
        "stroke-width",
    ],
}


def sanitize_svg(svg_content):
    return bleach.clean(
        svg_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
