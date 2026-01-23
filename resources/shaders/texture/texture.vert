#version 330 core

in vec2 in_pos;
in vec2 in_texCoord;

out vec2 texCoord;

uniform vec2 position;
uniform vec2 textureSize;
uniform vec2 anchor;
uniform float rotation;
uniform vec2 scale;

uniform vec2 screenSize;

void main() {
    vec2 anchorOffset = (- (anchor - 0.5)) * textureSize * 2;

    float c = cos(radians(rotation));
    float s = sin(radians(rotation));
    mat2 rotMat = mat2(c, -s, s, c);

    vec2 realPos = ((textureSize * in_pos + anchorOffset) * scale * rotMat + position * 2) / screenSize;

    gl_Position = vec4(realPos, 0., 1.);

    texCoord = in_texCoord;
}