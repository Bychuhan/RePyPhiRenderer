from typing import Any, Type, Callable
import tomllib

from .arg_specs import *


class ArgParser:
    @staticmethod
    def parse(argv: list[str | Any], aliases: dict[str, str] = {}, type_hints: dict[str, Type] = {}) -> dict[str, Any]:
        if not argv:
            return {}

        result = {}

        for index, arg in enumerate(argv):
            is_short_arg = False

            # --key
            if arg.startswith("--"):
                temp_arg = arg[2:]

            # -k
            elif arg.startswith("-"):
                temp_arg = arg[1:]

                is_short_arg = True

            else:
                continue

            # --key=value
            if "=" in temp_arg:
                key = temp_arg.split("=")[0]  # 第一个等号前所有字符
                value = "".join(temp_arg.split("=")[1:])  # 第一个等号后所有字符

            # --key value
            else:
                key = temp_arg
                try:
                    value = argv[index+1]
                except IndexError:
                    value = True  # Flag 处理

            if is_short_arg:
                key = aliases.get(key, key)  # 参数别名映射，找不到则不变

            # 参数值类型转换
            if not isinstance(value, bool):  # 非 Flag 才进行处理，非 Flag 时 value 的类型为 str
                value_type = type_hints.get(key, str)

                converter: Callable = ARG_TYPE_CONVERTERS.get(value_type, str)

                value = converter(value)

            result[key] = value

        return result

    @staticmethod
    def parse_from_toml(path):
        with open(path, "rb") as f:
            config = tomllib.load(f)

        return config
