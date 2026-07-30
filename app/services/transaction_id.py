import bs4
import requests
from x_client_transaction import ClientTransaction
from x_client_transaction.utils import generate_headers, get_ondemand_file_url, handle_x_migration

from app.core.exceptions import TwitterConfigurationError

X_HOME_URL = "https://x.com"


def build_client_transaction(cookies: dict[str, str]) -> ClientTransaction:
    """Build the x-client-transaction-id generator using an authenticated session.

    Upstream `twitter_openapi_python.tid.get_tid` fetches x.com without cookies. X now
    serves logged-out visitors a slim SPA shell that no longer embeds the webpack chunk
    manifest, so the `,<index>:"ondemand.s"` lookup finds nothing and the library dies with
    `'NoneType' object has no attribute 'group'`. Sending the auth cookies gets the legacy
    page that still contains the manifest.
    """
    session = requests.Session()
    session.headers = generate_headers()  # type: ignore[assignment]
    session.cookies.update(cookies)

    handle_x_migration(session=session)
    home_page = bs4.BeautifulSoup(session.get(url=X_HOME_URL).content, "html.parser")

    try:
        ondemand_file_url = get_ondemand_file_url(response=home_page)
    except AttributeError as exc:
        raise TwitterConfigurationError(
            "Could not read the ondemand.s manifest from x.com. TWITTER_AUTH_TOKEN/TWITTER_CT0 "
            "are most likely expired or invalid."
        ) from exc

    ondemand_file = session.get(url=ondemand_file_url)  # type: ignore[arg-type]

    return ClientTransaction(
        home_page_response=home_page,
        ondemand_file_response=bs4.BeautifulSoup(ondemand_file.content, "html.parser"),
    )
