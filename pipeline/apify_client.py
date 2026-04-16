from apify_client import ApifyClient as _ApifyClient


class ApifyWrapper:
    """Thin wrapper around the Apify SDK to simplify actor calls."""

    def __init__(self, api_token: str):
        self._client = _ApifyClient(token=api_token)

    def run_actor(self, actor_id: str, run_input: dict, max_items: int = 200) -> list[dict]:
        """
        Run an Apify actor and return its dataset items as a list of dicts.
        Blocks until the run finishes. Caps results at max_items.
        """
        run = self._client.actor(actor_id).call(run_input=run_input)
        items = list(
            self._client.dataset(run["defaultDatasetId"]).iterate_items()
        )
        return items[:max_items]
