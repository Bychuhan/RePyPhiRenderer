import os

import moderngl as mgl

from config import *
from shader import *
from texture import *


class Renderer:
    def __init__(self, config: Config, standalone: bool = False):
        self.config = config

        self.ctx = mgl.create_context(standalone=standalone)

        # 初始化着色器
        self.shader_manager = ShaderManager()
        self._init_shaders()

        # 初始化纹理
        self.texture_manager = TextureManager()

    def set_blend(self, enable: bool = True):
        if enable:
            self.ctx.enable(mgl.BLEND)
            self.ctx.blend_func = (
                mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA,
                mgl.ONE, mgl.ONE
            )
        else:
            self.ctx.disable(mgl.BLEND)

    def clear(self, color: list[float] | tuple[float] = (0, 0, 0, 0)):
        self.ctx.clear(color=color)

    def _init_shaders(self):
        # 渲染矩形着色器初始化
        with open(os.path.join(self.config.resources_dir, "shaders/rect/rect.vert")) as vert_file, open(os.path.join(self.config.resources_dir, "shaders/rect/rect.frag")) as frag_file:
            self.shader_manager.create_shader(
                self.ctx,
                "rect",
                [
                    -1.0, -1.0,
                    1.0, -1.0,
                    1.0, 1.0,
                    -1.0, 1.0
                ],
                vert_file.read(),
                frag_file.read(),
                in_types="2f",
                in_vars=["in_pos"],
                indices=[
                    0, 1, 2,
                    0, 3, 2
                ]
            )

        self.shader_manager.set_shader_uniform(
            "rect", "screenSize",
            (self.config.width, self.config.height)
        )

        # 渲染纹理着色器初始化
        with open(os.path.join(self.config.resources_dir, "shaders/texture/texture.vert")) as vert_file, open(os.path.join(self.config.resources_dir, "shaders/texture/texture.frag")) as frag_file:
            self.shader_manager.create_shader(
                self.ctx,
                "texture",
                [
                    -1.0, -1.0, 0.0, 0.0,
                    1.0, -1.0, 1.0, 0.0,
                    1.0, 1.0, 1.0, 1.0,
                    -1.0, 1.0, 0.0, 1.0
                ],
                vert_file.read(),
                frag_file.read(),
                in_types="2f 2f",
                in_vars=["in_pos", "in_texCoord"],
                indices=[
                    0, 1, 2,
                    0, 3, 2
                ]
            )

        self.shader_manager.set_shader_uniform(
            "texture", "screenSize",
            (self.config.width, self.config.height)
        )

    def render_rect(self, x: float, y: float, w: float, h: float,
                    r: float, color: list[float] | tuple[float] = (1, 1, 1, 1),
                    anchor: list[float] | tuple[float] = (0.5, 0.5)):

        self.shader_manager.set_shader_uniform("rect", "position", (x, y))
        self.shader_manager.set_shader_uniform("rect", "size", (w, h))
        self.shader_manager.set_shader_uniform("rect", "anchor", anchor)
        self.shader_manager.set_shader_uniform("rect", "rotation", r)
        self.shader_manager.set_shader_uniform("rect", "color", color)

        self.shader_manager.use_shader("rect", mode=mgl.TRIANGLE_STRIP)

    def render_texture(self, texture_name: str, x: float, y: float, sx: float, sy: float,
                       r: float, color: list[float] | tuple[float] = (1, 1, 1, 1),
                       anchor: list[float] | tuple[float] = (0.5, 0.5)):

        self.shader_manager.set_shader_uniform("texture", "position", (x, y))
        self.shader_manager.set_shader_uniform("texture", "scale", (sx, sy))
        self.shader_manager.set_shader_uniform("texture", "textureSize",
                                               self.texture_manager.get_texture_size(texture_name))
        self.shader_manager.set_shader_uniform("texture", "anchor", anchor)
        self.shader_manager.set_shader_uniform("texture", "rotation", r)
        self.shader_manager.set_shader_uniform("texture", "color", color)

        self.shader_manager.set_shader_uniform("texture", "texture", 0)
        self.texture_manager.use_texture(texture_name, 0)

        self.shader_manager.use_shader("texture", mode=mgl.TRIANGLE_STRIP)
