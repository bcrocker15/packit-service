from enum import Enum

DOCS_URL = "https://packit.dev/docs"
FAQ_URL = f"{DOCS_URL}/faq"
FAQ_URL_HOW_TO_RETRIGGER = (
    f"{DOCS_URL}/packit-as-a-service/"
    "#how-to-re-trigger-packit-service-actions-in-your-pull-request"
)
KOJI_PRODUCTION_BUILDS_ISSUE = "https://pagure.io/releng/issue/9801"

SANDCASTLE_WORK_DIR = "/sandcastle"
SANDCASTLE_IMAGE = "quay.io/packit/sandcastle"
SANDCASTLE_DEFAULT_PROJECT = "myproject"
SANDCASTLE_PVC = "SANDCASTLE_PVC"

CONFIG_FILE_NAME = "packit-service.yaml"

TESTING_FARM_API_URL = "https://api.dev.testing-farm.io/v0.1/"
TESTING_FARM_INSTALLABILITY_TEST_URL = "https://gitlab.com/testing-farm/tests"

MSG_RETRIGGER = (
    "You can retrigger the {job} by adding a comment (`/packit {command}`) "
    "into this {place}."
)

FILE_DOWNLOAD_FAILURE = "Failed to download file from URL"

PERMISSIONS_ERROR_WRITE_OR_ADMIN = (
    "Only users with write or admin permissions to the repository "
    "can trigger Packit-as-a-Service"
)

COPR_SUCC_STATE = "succeeded"
COPR_FAILED_STATE = "failed"
COPR_API_SUCC_STATE = 1
COPR_API_FAIL_STATE = 2

PG_COPR_BUILD_STATUS_FAILURE = "failure"
PG_COPR_BUILD_STATUS_SUCCESS = "success"

DEFAULT_RETRY_LIMIT = 2
# retry in 3s, 6s
DEFAULT_RETRY_BACKOFF = 3

ALLOWLIST_CONSTANTS = {
    "approved_automatically": "approved_automatically",
    "waiting": "waiting",
    "approved_manually": "approved_manually",
}


class KojiBuildState(Enum):
    """
    Koji states used in fedmsg payloads.

    Sometimes, koji use numbers instead,
    but we don't need them yet.
    Corresponding numbers are as comments if anyone needs them.
    """

    free = "FREE"  # 0
    open = "OPEN"  # 1
    closed = "CLOSED"  # 2
    canceled = "CANCELED"  # 3
    assigned = "ASSIGNED"  # 4
    failed = "FAILED"  # 5
