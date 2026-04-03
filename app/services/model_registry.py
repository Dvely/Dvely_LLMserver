from app.core.errors import APIError


class ModelRegistry:
    """Maps public aliases to upstream Ollama model names."""

    def __init__(self, alias_to_upstream: dict[str, str]) -> None:
        self._alias_to_upstream = dict(alias_to_upstream)

    def aliases(self) -> list[str]:
        return sorted(self._alias_to_upstream.keys())

    def resolve(self, alias: str) -> str:
        upstream = self._alias_to_upstream.get(alias)
        if upstream:
            return upstream

        supported = ", ".join(self.aliases())
        raise APIError(
            status_code=400,
            error_type="invalid_request_error",
            message=f"Unsupported model '{alias}'. Supported models: {supported}",
        )
