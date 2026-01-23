from typing import Literal
from io import BytesIO
from enum import IntEnum

import moderngl as mgl
from PIL import Image
from loguru import logger


class TextureConverter:
    @staticmethod
    def from_path(ctx: mgl.Context, path: str,
                  components: Literal[3, 4] = 4, flip=True, repeat=False,
                  use_mipmaps=False, filter: tuple[int, int] | None = None) -> mgl.Texture:

        with Image.open(path) as image:
            return TextureConverter.from_image(ctx, image,
                                               components=components, flip=flip, repeat=repeat,
                                               use_mipmaps=use_mipmaps, filter=filter)

    @staticmethod
    def from_bytes(ctx: mgl.Context, data: bytes,
                   components: Literal[3, 4] = 4, flip=True, repeat=False,
                   use_mipmaps=False, filter: tuple[int, int] | None = None) -> mgl.Texture:

        with Image.open(BytesIO(data)) as image:
            return TextureConverter.from_image(ctx, image,
                                               components=components, flip=flip, repeat=repeat,
                                               use_mipmaps=use_mipmaps, filter=filter)

    @staticmethod
    def from_image(ctx: mgl.Context, image: Image.Image,
                   components: Literal[3, 4] = 4, flip=True, repeat=False,
                   use_mipmaps=False, filter: tuple[int, int] | None = None) -> mgl.Texture:

        image = image.convert("RGB" if components == 3 else "RGBA")

        if flip:
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        texture = ctx.texture(
            size=image.size,
            components=components,
            data=image.tobytes()
        )

        texture.repeat_x = repeat
        texture.repeat_y = repeat

        if use_mipmaps:
            texture.build_mipmaps()

        texture.filter = (filter if not filter is None
                          else (mgl.LINEAR, mgl.LINEAR))

        return texture


class TextureCreateTypes(IntEnum):
    PATH = 0
    BYTES = 1
    IMAGE = 2


class TextureManager:
    def __init__(self):
        self.textures: dict[str, mgl.Texture] = {}

    def create_texture(self, ctx: mgl.Context, name: str,
                       data: str | bytes | Image.Image, create_type: Literal[0, 1, 2],
                       components: Literal[3, 4] = 4, flip=True, repeat=False,
                       use_mipmaps=False, filter: tuple[int, int] | None = None, replace=True) -> None:

        if name in self.textures:
            logger.warning(f"纹理 {name} 已存在")

            if not replace:
                return

        match create_type:
            case TextureCreateTypes.PATH:
                new_texture = TextureConverter.from_path(
                    ctx=ctx, path=data, components=components,
                    flip=flip, repeat=repeat, use_mipmaps=use_mipmaps, filter=filter
                )

            case TextureCreateTypes.BYTES:
                new_texture = TextureConverter.from_bytes(
                    ctx=ctx, data=data, components=components,
                    flip=flip, repeat=repeat, use_mipmaps=use_mipmaps, filter=filter
                )

            case TextureCreateTypes.IMAGE:
                new_texture = TextureConverter.from_image(
                    ctx=ctx, image=data, components=components,
                    flip=flip, repeat=repeat, use_mipmaps=use_mipmaps, filter=filter
                )

        self.textures[name] = new_texture

    def use_texture(self, name: str, mode: int | None = mgl.TRIANGLES, location: int = 0):
        if not name in self.textures:
            logger.warning(f"纹理 {name} 不存在")

            return

        texture = self.textures[name]

        texture.use(location=location)

    def destroy_texture(self, name: str):
        if not name in self.textures:
            logger.warning(f"销毁的纹理 {name} 不存在")

            return

        texture = self.textures[name]

        texture.release()

        self.textures.pop(name)

    def get_texture_size(self, name: str, default: tuple[int, int] | list[int, int] = (0, 0)):
        if not name in self.textures:
            logger.warning(f"纹理 {name} 不存在")

            return default

        texture = self.textures[name]

        return texture.size

    def __contains__(self, name: str):
        return name in self.textures
