import re


class BashSecurityValidator:
    VALIDATORS = [
        ("sudo", r"\bsudo\b"),
        ("rm_rf", r"\brm\s+(-[a-zA-Z]*)?r"),
        # ("cmd_substitution", r"\$\("), 
    ]

    def validate(self, command: str) -> list:
        """ 验证 Bash 命令中是否存在明显危险的模式。 """
        failures = []
        for name, pattern in self.VALIDATORS:
            if re.search(pattern, command):
                failures.append((name, pattern))
        return failures

    def is_safe(self, command: str) -> bool:
        """ 判断 Bash 命令是否安全。 """
        return len(self.validate(command)) == 0

    def describe_failures(self, command: str) -> str:
        """ 命令验证失败的详细描述。 """
        failures = self.validate(command)
        if not failures:
            return "命令安全"
        parts = [f"{name} (模式: {pattern})" for name, pattern in failures]
        return "命令包含危险模式: " + ", ".join(parts)


bash_validator = BashSecurityValidator()