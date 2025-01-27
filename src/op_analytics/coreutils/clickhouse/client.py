import logging
from threading import Lock
from typing import Any, Literal

import clickhouse_connect
import polars as pl
import pyarrow as pa
import stamina
from clickhouse_connect.driver.client import Client

from op_analytics.coreutils.env import env_get
from op_analytics.coreutils.logger import human_rows, human_size, structlog

log = structlog.get_logger()


ClickHouseInstance = Literal["GOLDSKY", "OPLABS"]

_GOLDSKY_CLIENT: Client | None = None
_OPLABS_CLIENT: Client | None = None

_INIT_LOCK = Lock()


def connect(instance: ClickHouseInstance):
    log.debug(f"connecting to {instance} Clickhouse client...")
    # Server-generated ids (as opoosed to client-generated) are required for running
    # concurrent queries. See https://clickhouse.com/docs/en/integrations/python#managing-clickhouse-session-ids.
    clickhouse_connect.common.set_setting("autogenerate_session_id", False)
    client = clickhouse_connect.get_client(
        host=env_get(f"CLICKHOUSE_{instance}_HOST"),
        port=int(env_get(f"CLICKHOUSE_{instance}_PORT")),
        username=env_get(f"CLICKHOUSE_{instance}_USER"),
        password=env_get(f"CLICKHOUSE_{instance}_PASSWORD"),
        connect_timeout=60,
        send_receive_timeout=300,
    )
    log.debug(f"initialized {instance} Clickhouse client.")
    return client


def init_client(instance: ClickHouseInstance):
    """Idempotent client initialization.

    This function guarantess only one global instance exists.
    """
    global _GOLDSKY_CLIENT
    global _OPLABS_CLIENT

    with _INIT_LOCK:
        if instance == "GOLDSKY":
            if _GOLDSKY_CLIENT is None:
                _GOLDSKY_CLIENT = connect(instance)

        if instance == "OPLABS":
            if _OPLABS_CLIENT is None:
                _OPLABS_CLIENT = connect(instance)

    if instance == "GOLDSKY":
        if _GOLDSKY_CLIENT is None:
            raise RuntimeError(f"{instance} Clickhouse client was not properly initialized.")
        return _GOLDSKY_CLIENT

    if instance == "OPLABS":
        if _OPLABS_CLIENT is None:
            raise RuntimeError(f"{instance} Clickhouse client was not properly initialized.")
        return _OPLABS_CLIENT

    raise NotImplementedError()


def run_goldsky_statement(statement):
    """A statement does not return results."""
    client = init_client("GOLDSKY")
    client.query(statement)


def run_goldsky_query(
    query: str,
    parameters: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
):
    return run_query("GOLDSKY", query, parameters, settings)


def retry_logger(exc: Exception) -> bool:
    global _OPLABS_CLIENT

    log.error(f"Encountered exception: {exc}")

    _OPLABS_CLIENT = None
    log.warning("Attempting to reconnect OPLABS client.")
    init_client("OPLABS")

    return True


@stamina.retry(on=retry_logger, attempts=3)
def run_oplabs_query(
    query: str,
    parameters: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
):
    return run_query("OPLABS", query, parameters, settings)


def run_query(
    instance: ClickHouseInstance,
    query: str,
    parameters: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
):
    """Return arrow table with clickhouse results"""
    client = init_client(instance)

    arrow_result = client.query_arrow(
        query=query, parameters=parameters, settings=settings, use_strings=True
    )
    return pl.from_arrow(arrow_result)


@stamina.retry(on=retry_logger, attempts=3)
def insert_arrow(
    instance: ClickHouseInstance,
    database: str,
    table: str,
    df_arrow: pa.Table,
    log_level=logging.DEBUG,
):
    """Write arrow table to clickhouse."""
    client = init_client(instance)

    result = client.insert_arrow(table=table, arrow_table=df_arrow, database=database)

    log.log(
        log_level,
        f"done inserting [{human_rows(result.written_rows)} {human_size(result.written_bytes())}] to {database}.{table}",
    )
