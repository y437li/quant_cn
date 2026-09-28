"""Project exception hierarchy; every raised error is a `QuantCnError` (CODING_STANDARD §2.5)."""

from __future__ import annotations


class QuantCnError(Exception):
    """
    Purpose:
        Root of every exception the package raises, so callers catch project errors in one place.

    Contract:
        Input:
            message: str  -- human-readable reason; may be empty
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        pipeline.LocalRunner.run  -- catches any project error to close the run as failed
        cli.QuantCnCli.run        -- turns project errors into exit code 1
        core.ConfigError          -- subclass
        core.DataSourceError      -- subclass
        core.LakeError            -- subclass
        core.SchemaError          -- subclass

    Test cases:
        TC-QCE-001  every project exception is a QuantCnError subclass
    """


class ConfigError(QuantCnError):
    """
    Purpose:
        Configuration is missing, malformed or unsafe (e.g. lake root inside the repository).

    Contract:
        Input:
            message: str  -- which key is wrong and why
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        core.Config.load                   -- bad YAML, unsafe lake root
        core.Config.get_dataset            -- unknown dataset name
        data_loading.TushareClient         -- missing token
        data_loading.FetcherFactory.build  -- unknown sweep kind
        pipeline.DownloadPipeline.run      -- unknown dataset requested
        pipeline.CuratePipeline            -- injected type or call

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class SchemaError(QuantCnError):
    """
    Purpose:
        A DataFrame does not satisfy its declared Schema (columns, dtypes, primary key).

    Contract:
        Input:
            message: str  -- the failing column or key
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        core.Schema.normalize  -- value not convertible to the declared dtype
        core.Schema.validate   -- column set, dtype or primary-key violation

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class DataSourceError(QuantCnError):
    """
    Purpose:
        The external data source failed: API error code, retries exhausted, malformed response.

    Contract:
        Input:
            message: str  -- endpoint and vendor message
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        data_loading.TushareClient.query  -- non-zero code after retries, network failure
        core.BaseFetcher.run              -- records the failing key, then re-raises
        core.PermissionDeniedError        -- subclass

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """


class PermissionDeniedError(DataSourceError):
    """
    Purpose:
        The account lacks permission (points) for an endpoint; the dataset is blocked, not broken.

    Contract:
        Input:
            message: str  -- endpoint and vendor message
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        data_loading.TushareClient.query  -- vendor message matches a permission marker
        pipeline.LocalRunner.run          -- marks the step blocked and continues with the next

    Test cases:
        TC-QCE-001  subclass of DataSourceError and QuantCnError
    """


class LakeError(QuantCnError):
    """
    Purpose:
        The local lake cannot be read or written: missing dataset, failed atomic write, bad catalog.

    Contract:
        Input:
            message: str  -- path or dataset involved
        Output:
            exception instance
        Raises:
            (none)

    Used by:
        lake.ParquetWriter         -- atomic write failed
        lake.TradingCalendar       -- trade_cal not downloaded yet
        lake.LakeQuery.sql         -- DuckDB query error
        cli.QuantCnCli             -- backup target missing
        lake.Compactor             -- injected type or call
        pipeline.DownloadPipeline  -- injected type or call
        lake.FetchLog              -- injected type or call
        lake.LakeCatalog           -- injected type or call
        lake.RunLog                -- injected type or call
        pipeline.DeriveStep        -- injected type or call
        lake.DerivedViews          -- injected type or call
        lake.PitAligner            -- injected type or call

    Test cases:
        TC-QCE-001  subclass of QuantCnError
    """
